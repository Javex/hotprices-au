import re
import requests
import json
import pathlib
from datetime import datetime
from bs4 import BeautifulSoup

from .. import output, request, units
import hotprices_au.categories

# How many errors are acceptable for a category before failing?
# This means it's okay if *some* categories don't return 100% of products
ERROR_COUNT_MAX = 9
ERROR_IGNORE = True


class ColesScraper:
    def __init__(self, store_id, quick=False):
        self.quick = quick
        self.store_id = store_id

        self.session = request.get_base_session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Origin": "https://www.coles.com.au",
            "Referer": "https://www.coles.com.au",
        }
        self.start()

    def start(self):
        # Need to get the subscription key
        response = self.session.get("https://www.coles.com.au")
        response.raise_for_status()
        html = BeautifulSoup(response.text, features="html.parser")
        next_data_script = html.find("script", id="__NEXT_DATA__")
        next_data_json = json.loads(next_data_script.string)
        self.api_key = next_data_json["runtimeConfig"]["BFF_API_SUBSCRIPTION_KEY"]
        self.session.headers["ocp-apim-subscription-key"] = self.api_key
        self.version = next_data_json["buildId"]

    def get_category(self, cat_slug, page_filter: int):
        params = {
            "slug": cat_slug,
            "page": 1,
        }
        product_count = 0
        error_count = 0
        while True:
            # If there's a filter and we're not on the right page then skip
            if page_filter != None and params["page"] != page_filter:
                params["page"] += 1
                continue

            print(f'Page {params["page"]}')
            response = self.session.get(
                f"https://www.coles.com.au/_next/data/{self.version}/en/browse/{cat_slug}.json",
                params=params,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError:
                error_count += 1
                print(f'Error fetching page {params["page"]}')
                if not ERROR_IGNORE:
                    # Need to also raise an error if there's a page filter as there
                    # are no more pages to try
                    if error_count > ERROR_COUNT_MAX or page_filter is not None:
                        raise
                else:
                    params["page"] += 1
                    continue
            response_data = response.json()
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
            params["page"] += 1

    def get_categories(self):
        response = self.session.get(
            f"https://www.coles.com.au/api/bff/products/categories?storeId={self.store_id}"
        )
        response.raise_for_status()
        category_data = response.json()
        categories = []
        for category_obj in category_data["catalogGroupView"]:
            cat_slug = category_obj["seoToken"]

            if cat_slug in ["down-down", "back-to-school"]:
                # Skip for now, expect duplicate products
                continue

            categories.append(category_obj)
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
            f"Unable to understad what {per_str} means from " f"{comparable}"
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


def main(quick, save_path, category: str, page: int):
    """
    category: Slug or name or category to fetch, will fetch only that one.
    page: Page number to fetch.
    """
    coles = ColesScraper(store_id="0584", quick=quick)
    categories = coles.get_categories()
    # Rename to avoid the overwrite below
    category_filter = category.lower() if category is not None else None
    # categories = load_cache()
    for category_obj in categories:
        cat_slug = category_obj["seoToken"]
        cat_desc = category_obj["name"]
        if category_filter is not None and (
            category_filter != cat_desc.lower() or category_filter != cat_slug.lower()
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
    "Take raw coles categories and turn them into standard format"
    categories = []
    for main_category in raw_categories:
        main_cat_seo = main_category["seoToken"]
        main_cat_name = main_category["name"]
        # Create entry for main category for products that aren't in any sub category
        categories.append(
            {
                "id": main_category["id"],
                "description": main_cat_name,
                "url": f"https://www.coles.com.au/browse/{main_cat_seo}",
                "code": None,
            }
        )

        sub_categories = main_category.get("catalogGroupView", [])
        if not sub_categories:
            raise RuntimeError("No subcats")
        for sub_category in sub_categories:
            sub_cat_seo = sub_category["seoToken"]
            sub_cat_name = sub_category["name"]
            sub_category_item = {
                "id": sub_category["id"],
                "description": f"{main_cat_name} > {sub_cat_name}",
                "url": f"https://www.coles.com.au/browse/{main_cat_seo}/{sub_cat_seo}",
                "code": None,
            }
            categories.append(sub_category_item)

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
