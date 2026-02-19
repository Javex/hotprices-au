import re
import time
from typing import Any
import json
import pathlib
import bs4
import camoufox
from bs4 import BeautifulSoup
from playwright.sync_api import BrowserContext
from playwright._impl._errors import TimeoutError

from .. import output, request, units
import hotprices_au.categories

# How many errors are acceptable for a category before failing?
# This means it's okay if *some* categories don't return 100% of products
ERROR_COUNT_MAX = 9
ERROR_IGNORE = True


class ColesScraper:
    def __init__(
        self, store_id, save_path_dir: pathlib.Path, quick=False, headless=True, request_delay: float = 2.0
    ):
        self.quick = quick
        self.store_id = store_id
        self.save_path_dir = save_path_dir
        self.headless = headless
        self.request_delay = request_delay
        self.captured_api_key = None

        self.session = request.get_base_session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Origin": "https://www.coles.com.au",
            "Referer": "https://www.coles.com.au",
        }
        self.extra_headers = {}
        self.fox: camoufox.Camoufox = camoufox.Camoufox(
            headless=self.headless,
            enable_cache=True,
            humanize=True,
        )

    def __enter__(self):
        self.fox.__enter__()
        self._setup()
        return self

    def _setup(self):
        if self.fox.browser is None:
            raise RuntimeError("Unexpected None browser in camoufox instance")
        if isinstance(self.fox.browser, BrowserContext):
            raise RuntimeError("Unexpected type BrowserContext: %s", self.fox.browser)
        self.context = self.fox.browser.new_context()
        self.page = self.context.new_page()
        self.api = self.context.request
        self.context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )
        self.page.on("request", self._capture_api_key)

    def _capture_api_key(self, request):
        """Intercept network requests to capture the API key from headers."""
        url = request.url
        if "coles.com.au/api/" in url or "coles.com.au/_next/data" in url:
            headers = request.headers
            for key_name in ["ocp-apim-subscription-key", "col-api-key", "x-api-key"]:
                if key_name in headers:
                    self.captured_api_key = headers[key_name]

    def reset(self, retries=0):
        """
        Reset the browser to bypass bot protection.

        `retries` is used to count how many times it's been attempted. Used for recursion.
        """
        self.page.close()
        self.context.close()
        self.fox.__exit__()

        self.fox: camoufox.Camoufox = camoufox.Camoufox(
            headless=self.headless,
            enable_cache=True,
            humanize=True,
        )
        self.fox.__enter__()
        self._setup()
        try:
            self.start()
        except TimeoutError:
            if retries < 5:
                print(f"Got TimeoutError, retrying. Retries so far: {retries}")
                return self.reset(retries + 1)
            else:
                raise

    def __exit__(self, *args: Any):
        self.page.context.tracing.stop(path="trace.zip")
        self.fox.__exit__(*args)

    def start(self):
        response = self.page.goto(
            "https://www.coles.com.au", wait_until="domcontentloaded"
        )
        if response is None:
            raise RuntimeError("Unexpected None response")
        locator = self.page.locator("script#__NEXT_DATA__")
        locator.wait_for(state="attached")

        try:
            browse_link = self.page.locator("a[href*='/browse/']").first
            if browse_link:
                browse_link.click()
                self.page.wait_for_timeout(2000)
                self.page.go_back()
                self.page.wait_for_timeout(1000)
        except Exception:
            pass

        response_text = self.page.content()
        try:
            html = BeautifulSoup(response_text, features="html.parser")
            next_data_script = html.find("script", id="__NEXT_DATA__")
            if next_data_script is None:
                raise RuntimeError("Cannot find __NEXT_DATA__ script in response")
            if not isinstance(next_data_script, bs4.Tag):
                raise RuntimeError("Expected tag for script, got %s", next_data_script)
            next_data_str = next_data_script.string
            if next_data_str is None:
                raise RuntimeError(
                    "Unexpected None str for next_data_script: %s", next_data_script
                )
            next_data_json = json.loads(next_data_str)
        except:
            output.save_response(response.text(), self.save_path_dir)
            raise

        if self.captured_api_key:
            self.api_key = self.captured_api_key
        else:
            self.api_key = next_data_json["runtimeConfig"]["BFF_API_SUBSCRIPTION_KEY"]
        self.extra_headers["ocp-apim-subscription-key"] = self.api_key
        for cookie in self.page.context.cookies():
            assert "name" in cookie
            assert "value" in cookie
            self.session.cookies.set(cookie["name"], cookie["value"])
        self.version = next_data_json["buildId"]

    def get_category(self, cat_slug, page_filter: int):
        product_count = 0
        error_count = 0
        page = 1
        while True:
            # If there's a filter and we're not on the right page then skip
            if page_filter != None and page != page_filter:
                page += 1
                continue

            response = self.get_category_page(cat_slug, page)
            if response.headers.get("content-type", "").lower() == "text/html":
                print("Encountered bot protection, resetting")
                # Bot protection kicked in, do a reset
                self.reset()
                # Try once more
                response = self.get_category_page(cat_slug, page)

            if response is None:
                raise RuntimeError("Unexpected None response")
            if not response.ok:
                error_count += 1
                print(f"Error fetching page {page}")
                if not ERROR_IGNORE:
                    # Need to also raise an error if there's a page filter as there
                    # are no more pages to try
                    if error_count > ERROR_COUNT_MAX or page_filter is not None:
                        raise
                else:
                    page += 1
                    continue
            response_text = response.text()
            try:
                response_data = json.loads(response_text)
            except:
                output.save_response(response_text, self.save_path_dir)
                raise

            search_results = response_data["pageProps"]["searchResults"]
            for result in search_results["results"]:
                yield result

            # Next page calculation
            total_products = search_results["noOfResults"]
            product_count += len(search_results["results"])
            if product_count >= total_products:
                # We're done
                break

            # Temporary speedup
            if self.quick:
                break

            # Not done, go to next page
            page += 1

    def get_category_page(self, cat_slug, page: int):
        params = {
            "slug": cat_slug,
            "page": page,
        }
        if self.request_delay > 0:
            time.sleep(self.request_delay)
        print(f"Page {page}")
        query = "&".join(f"{key}={value}" for key, value in params.items())
        response = self.api.get(
            f"https://www.coles.com.au/_next/data/{self.version}/en/browse/{cat_slug}.json?{query}",
            headers=self.extra_headers,
        )
        return response

    def get_categories(self):
        """Fetch categories via GraphQL API."""
        query = """
            query GetShopProductsMenu($storeId: BrandedId!, $withCampaignLinks: Boolean!, $campaignCount: Int) {
                menuItems: productCategories(
                    storeId: $storeId
                    withCampaignLinks: $withCampaignLinks
                    campaignCount: $campaignCount
                ) {
                    ...shopProductsMenuFields
                }
            }

            fragment shopProductsMenuFields on ProductCategories {
                restrictedIds: excludedCategoryIds
                items: catalogGroupView {
                    ...shopProductMenuItemFields
                    childItems: catalogGroupView {
                        ...shopProductMenuItemFields
                        childItems: catalogGroupView {
                            ...shopProductMenuItemFields
                        }
                    }
                }
            }

            fragment shopProductMenuItemFields on ProductCategory {
                ...catalogGroupFields
                type
            }

            fragment catalogGroupFields on ProductCategory {
                id
                level
                name
                originalName
                productCount
                seoToken
                type
                subType
            }
        """
        variables = {
            "storeId": f"COL:{self.store_id}",
            "withCampaignLinks": True,
            "campaignCount": 0,
        }

        response = self.api.post(
            "https://www.coles.com.au/api/graphql",
            headers={
                **self.extra_headers,
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "query": query,
                    "variables": variables,
                    "operationName": "GetShopProductsMenu",
                }
            ),
        )

        if response is None:
            print("Warning: Unexpected None response from GraphQL API")
            return []
        if not response.ok:
            print(f"Warning: GraphQL API returned status {response.status}")
            print(f"Response: {response.text()[:500]}")
            return []

        data = response.json()
        menu_items = data.get("data", {}).get("menuItems", {})
        items = menu_items.get("items", [])

        # Promotional and deal categories that only surface products already
        # present in their primary categories -- scraping them would produce duplicates.
        EXCLUDED_SLUGS = {
            "down-down",              # Discounted items duplicated from real categories
            "back-to-school",         # Seasonal promotional set
            "bonus-credit-products",  # Loyalty/points deals, not regular stock
            "liquorland",             # Alcohol
            "tobacco",                # Tobacco
        }

        categories = []
        for category_obj in items:
            cat_slug = category_obj.get("seoToken")
            if cat_slug in EXCLUDED_SLUGS:
                continue
            categories.append(
                {
                    "id": category_obj.get("id"),
                    "name": category_obj.get("name"),
                    "seoToken": cat_slug,
                    "catalogGroupView": category_obj.get("childItems", []),
                }
            )
        return categories


def get_canonical(item, today):
    ad_types = [
        "SINGLE_TILE",
        "CONTENT_ASSOCIATION",
    ]
    if item["_type"] in ad_types and item.get("adId"):
        # Ad tile, not a product
        return None

    if item["pricing"] is None:
        # No pricing information, can't process
        return None

    # Skip online-only products (not available in physical stores)
    availability = item.get("availability", {}) or {}
    if availability.get("storeAvailability") == "ONLINE_ONLY":
        return None

    match item["description"]:
        case "MINI CHRISTMAS CARD 20PK":
            item["size"] = "20pk"
        case "BOTTLE GIFT BAG":
            item["size"] = "1ea"

    quantity, unit = get_quantity_and_unit(item)

    name = item["name"]
    brand = item["brand"]
    if brand:
        name = f"{brand} {name}"
    result = {
        "id": item["id"],
        "name": name,
        "description": item["description"],
        "price": item["pricing"]["now"],
        "priceHistory": [
            {
                "date": today,
                "price": item["pricing"]["now"],
            }
        ],
        "isWeighted": item["pricing"]["unit"].get("isWeighted", False),
        "unit": unit,
        "quantity": quantity,
        # 'organic':
    }
    result = units.convert_unit(result)
    return result


def get_quantity_and_unit(item):
    # Try to parse size information first, it looks better in the frontend
    size = item["size"]
    if not size:
        # Maybe the description can be parsed as size
        size = item["description"]

    unit_data = item["pricing"]["unit"]
    quantity = unit_data["quantity"]
    try:
        parsed_quantity, unit = parse_str_unit(size)
        # A quantity of 0 or 1 indicates that the information is elsewhere
        if parsed_quantity != quantity and quantity > 1:
            raise RuntimeError(
                f"Quantity '{quantity} does not matched parsed quantity '{parsed_quantity}"
            )
        # If quantity is 1 and we parsed a different value then that's the right value
        # (e.g. 1 (quantity) packet of 38g (parsed_quantity))
        quantity = parsed_quantity
    except RuntimeError:
        # If that didn't work we can now try to get the info from standard sizes (e.g. per 100g)
        if "ofMeasureUnits" in unit_data:
            unit = unit_data["ofMeasureUnits"]
        elif item.get("pricing", {}).get("comparable"):
            return parse_comparable(item)
        else:
            raise

    return quantity, unit


def parse_comparable(item):
    comparable = item["pricing"]["comparable"]
    m = re.match(r"\$([\.0-9]+) per (.*)", comparable)
    if not m:
        raise RuntimeError(f"Unable to parse comparable {comparable}")

    price_str, per_str = m.group(1), m.group(2)
    price_per = float(price_str)
    if price_per != item["pricing"]["now"]:
        raise RuntimeError(
            f"Price from {comparable} extracted as {price_per} "
            f"does not match expected price of {item['pricing']['now']}"
        )

    if per_str == "1ea":
        quantity, unit = 1, "ea"
    else:
        raise RuntimeError(
            f"Unable to understad what {per_str} means from {comparable}"
        )
    return quantity, unit


def parse_str_unit(size):
    # Try coles-special methods before going to the generic function
    size = size.lower()
    matches = [
        re.match(
            r"^.* (?P<quantity>[0-9]+)(?P<unit>[a-z]+):(pack(?P<count>[0-9]+)|(?P<each>ea))",
            size,
        ),
        re.match(
            r"^.* (?P<count>[0-9]+)pk can (?P<quantity>[0-9]+)(?P<unit>[a-z]+)", size
        ),
        # re.match(r'^.* (?P<quantity>[0-9]+)(?P<unit>[a-z]+) \(?(?P<count>[0-9]+)pk\)?', size),
        re.match(
            r"^.* (?P<quantity>[0-9]+)(?P<unit>[a-z]+) \(?(?P<count>[0-9]+)pk\)?(:ctn)?(?P<ctn_count>[0-9]+)?",
            size,
        ),
    ]
    for matched in matches:
        if matched:
            quantity = float(matched.group("quantity"))
            unit = matched.group("unit")
            count_match = matched.group("count")
            try:
                ctn_count_match = matched.group("ctn_count")
            except IndexError:
                ctn_count_match = False
            if ctn_count_match:
                count = float(ctn_count_match)
            elif count_match:
                count = float(count_match)
            else:
                each_str = matched.group("each")
                if each_str:
                    count = 1
                else:
                    continue
            quantity *= count
            return quantity, unit
    else:
        return units.parse_str_unit(size)


def main(quick, save_path: pathlib.Path, category: str, page: int, request_delay: float = 2.0):
    """
    category: Slug or name or category to fetch, will fetch only that one.
    page: Page number to fetch.
    """
    save_path_dir = save_path.parent
    coles = ColesScraper(store_id="0584", save_path_dir=save_path_dir, quick=quick, request_delay=request_delay)
    with coles:
        coles.start()
        categories = coles.get_categories()
        # Rename to avoid the overwrite below
        category_filter = category.lower() if category is not None else None
        # categories = load_cache()
        for category_obj in categories:
            cat_slug = category_obj["seoToken"]
            cat_desc = category_obj["name"]
            if category_filter is not None and (
                category_filter != cat_desc.lower()
                or category_filter != cat_slug.lower()
            ):
                continue
            print(f"Fetching category {cat_slug} ({cat_desc})")
            category = coles.get_category(cat_slug, page_filter=page)
            all_category_bundles = list(category)
            category_obj["Products"] = all_category_bundles

            if quick:
                break
            # save_cache(categories)
    output.save_data(categories, save_path)
    get_category_mapping(categories)
    # print(json.dumps(category, indent=4))


def get_category_mapping(raw_categories):
    "Take raw coles categories and turn them into standard format (top-level only)"
    categories = []
    for main_category in raw_categories:
        main_cat_seo = main_category["seoToken"]
        main_cat_name = main_category["name"]
        categories.append(
            {
                "id": main_category["id"],
                "description": main_cat_name,
                "url": f"https://www.coles.com.au/browse/{main_cat_seo}",
                "code": None,
            }
        )

    categories = hotprices_au.categories.merge_save_save_categories("coles", categories)

    category_map = {c["id"]: c for c in categories}
    return category_map


def get_category_from_map(category_map, raw_item):
    # Confusingly "subCategoryId" is actually the parent category
    # and "categoryId" is the level 2 category
    category_id = raw_item["onlineHeirs"][0]["categoryId"]
    return category_map[category_id]["code"]


if __name__ == "__main__":
    main()



