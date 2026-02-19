import math
import re
import time
import requests
import json

from .. import output, request, units
import hotprices_au
from hotprices_au.logging import logger


class WooliesAPI:
    def __init__(self, quick=False, request_delay: float = 0.3):
        self.quick = quick
        self.request_delay = request_delay

        self.session = request.get_base_session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "Origin": "https://www.woolworths.com.au",
            "Referer": "https://www.woolworths.com.au/shop/browse/fruit-veg",
            "Accept": "application/json",
        }
        self._started = False
        self.start()

    def start(self):
        if not self._started:
            response = self.session.get("https://www.woolworths.com.au")
            response.raise_for_status()
            self._started = True

    def get_category(self, cat_id, cat_slug="", cat_name=""):
        raw_json = r"""
            {
                "pageNumber": 1,
                "pageSize": 36,
                "sortType": "Name",
                "url": "/shop/browse/fruit-veg",
                "location": "/shop/browse/fruit-veg",
                "formatObject": "{\"name\":\"Fruit & Veg\"}",
                "isSpecial": false,
                "isBundle": false,
                "isMobile": false,
                "filters": [
                    {
                        "Items": [
                            {
                                "Term": "Woolworths"
                            }
                        ],
                        "Key": "SoldBy"
                    }
                ],
                "token": "",
                "gpBoost": 0,
                "isHideUnavailableProducts": false,
                "enableAdReRanking": false,
                "groupEdmVariants": true,
                "categoryVersion": "v2"
            }
        """
        request_data = json.loads(raw_json)
        request_data["categoryId"] = cat_id
        if cat_slug:
            request_data["url"] = f"/shop/browse/{cat_slug}"
            request_data["location"] = f"/shop/browse/{cat_slug}"
        if cat_name:
            import json as _json
            request_data["formatObject"] = _json.dumps({"name": cat_name})
        # Larger page size leads to an error, have to make do with 36 items per
        # page
        request_data["pageSize"] = 36
        woolworths_count = 0
        consecutive_empty = 0
        CONSECUTIVE_EMPTY_MAX = 3
        while True:
            print(f'Page {request_data["pageNumber"]}')
            if self.request_delay > 0:
                time.sleep(self.request_delay)
            response = self.session.post(
                "https://www.woolworths.com.au/apis/ui/browse/category",
                json=request_data,
            )
            response.raise_for_status()
            response_data = response.json()

            all_bundles = response_data["Bundles"]
            woolworths_bundles = [
                bundle for bundle in all_bundles
                if all(
                    p.get("SoldBy", "Woolworths") == "Woolworths"
                    for p in bundle.get("Products", [])
                )
            ]
            for bundle in woolworths_bundles:
                yield bundle

            woolworths_count += len(woolworths_bundles)

            # If the API returns no bundles at all, we are done
            if len(all_bundles) == 0:
                break

            # Track consecutive pages with no Woolworths products -- signals
            # we have exhausted genuine stock and the rest is third-party
            if len(woolworths_bundles) == 0:
                consecutive_empty += 1
                if consecutive_empty >= CONSECUTIVE_EMPTY_MAX:
                    logger.info(
                        f"Category {cat_id}: {CONSECUTIVE_EMPTY_MAX} consecutive pages "
                        f"with no Woolworths products, stopping. "
                        f"Total Woolworths products: {woolworths_count}"
                    )
                    break
            else:
                consecutive_empty = 0

            # Temporary speedup
            if self.quick:
                break

            # Not done, go to next page
            request_data["pageNumber"] += 1

    def get_categories(self):
        response = self.session.get(
            "https://www.woolworths.com.au/apis/ui/PiesCategoriesWithSpecials"
        )
        response.raise_for_status()
        response_data = response.json()
        category_data = response_data["Categories"]
        categories = []
        for category_obj in category_data:
            if is_filtered_category(category_obj):
                continue
            categories.append(category_obj)
        return categories


def is_filtered_category(category_obj):
    # Node ID fallback for legacy entries - prefer slug-based matching below
    cat_id_skip = [
        "specialsgroup",
    ]

    # Categories excluded by URL slug -- more robust than node IDs which can change
    cat_slug_skip = {
        "everyday-market",      # External marketplace, 100k+ products duplicated elsewhere
        "home-lifestyle",       # Non-grocery, out of scope
        "electronics",          # Non-grocery, out of scope
        "halloween",            # Seasonal promotional set
        "healthylife-pharmacy", # External partner, not standard Woolworths stock
        "beer-wine-spirits",    # Alcohol
        "sports-fitness-outdoor-activities",  # Non-grocery, out of scope
        "cleaning-maintenance", # Dominated by third-party Everyday Market products
        "health-wellness",      # Dominated by third-party Everyday Market products
        "beauty-personal-care", # Dominated by third-party Everyday Market products
        "baby",                 # Dominated by third-party Everyday Market products
        "pet",                  # Dominated by third-party Everyday Market products
        "personal-care",        # Dominated by third-party Everyday Market products
        "beauty",               # Dominated by third-party Everyday Market products
        "international-foods",  # 83% overlap with Pantry, only 37 unique products
    }

    cat_slug = category_obj.get("UrlFriendlyName", "")
    if cat_slug in cat_slug_skip:
        return True

    cat_id = category_obj["NodeId"]
    if cat_id in cat_id_skip:
        return True

    cat_desc = category_obj["Description"]
    if cat_desc == "Front of Store":
        # Throws error, probably nothing special in here anyway
        return True

    return False


def get_canonical(item, today):
    if len(item["Products"]) > 1:
        raise RuntimeError("More than one product, help")
    item = item["Products"][0]

    price = item["Price"]
    unit = item["PackageSize"]

    # If item is out of stock then price might be empty so we need to take the "WasPrice" field
    if price is None:
        price_was = item["WasPrice"]
        if not item["IsInStock"] and price_was:
            price = price_was

    # The second case is to handle two products with that "size"
    if price is None or unit.lower() == "min. 250g":
        price = item["CupPrice"]
        unit = item["CupMeasure"]

    # Price is still None, can't do anything, skipping product
    if price is None:
        return None

    # Skip online-only products (not available in physical stores)
    if item.get("IsOnlineOnly"):
        return None

    # Skip Everyday Market / third-party seller products
    if item.get("SoldBy", "Woolworths") != "Woolworths":
        return None

    # Fix some particularly problematic products
    match item["Stockcode"]:
        case 249086:
            unit = "1kg"  # Woolworths Pot Set Greek Style Yoghurt
        case 203793:
            unit = "2 pack"  # Nicorette Quit Smoking Quickmist Smart Track Mouth Spray Freshmint
        case 532887:
            unit = "700ml"  # Kahlua White Russian
        case 985323:
            unit = "800ml"  # Nelson County Bourbon & Cola
    result = {
        "id": item["Stockcode"],
        "name": item["Name"],
        "description": item["Description"],
        "price": price,
        "priceHistory": [
            {
                "date": today,
                "price": price,
            }
        ],
        "isWeighted": False,  # TODO: What is this and how do I find it in woolies data?
    }

    try:
        quantity, unit = units.parse_str_unit(unit)
    except RuntimeError:
        # Not in stock and we can't use "WasPrice" because we can't parse the weird unit it uses.
        # No idea what the right price would be so just skip the product
        if not item["IsInStock"]:
            return None
        elif item["Unit"].lower() == "each":
            unit = "ea"
            quantity = 1
        else:
            print(f"Can't parse unit '{unit}' for item {result}")
            return None
    result["unit"] = unit
    result["quantity"] = quantity
    result = units.convert_unit(result)
    return result


def main(quick, save_path, category_filter: str, page_filter: int, request_delay: float = 0.3):
    if page_filter is not None:
        raise NotImplementedError("Page filter not implemented for woolies yet.")
    woolies = WooliesAPI(quick=quick, request_delay=request_delay)
    categories = woolies.get_categories()
    category_filter_lower = category_filter.lower() if category_filter is not None else None
    for category_obj in categories:
        cat_id = category_obj["NodeId"]
        cat_desc = category_obj["Description"]
        cat_slug = category_obj.get("UrlFriendlyName", "")
        if category_filter_lower is not None and (
            category_filter_lower != cat_desc.lower()
            and category_filter_lower != cat_slug.lower()
        ):
            continue
        print(f"Fetching category {cat_id} ({cat_desc})")
        category = woolies.get_category(cat_id, cat_slug=cat_slug, cat_name=cat_desc)
        all_category_bundles = list(category)
        category_obj["Products"] = all_category_bundles

        if quick:
            break
    output.save_data(categories, save_path)
    get_category_mapping(categories)


def normalise_category_name(category_name):
    category_name, _ = re.subn(r"[^A-Za-z]+", "", category_name)
    return category_name


def ensure_subcategories(raw_categories):
    """
    This exist for backfill reasons: Initial data doesn't have subcategories so
    we need to re-fetch that data if we don't have it yet. Can probably be
    removed once we've got it fixed.
    """
    has_children = False
    for main_cat in raw_categories:
        if main_cat.get("Children"):
            has_children = True
            break

    if has_children:
        return raw_categories
    else:
        woolies = WooliesAPI()
        return woolies.get_categories()


def get_category_mapping(raw_categories):
    "Raw woolies categories to standard format (top-level only)"
    categories = []
    raw_categories = ensure_subcategories(raw_categories)
    for main_category in raw_categories:
        if is_filtered_category(main_category):
            continue
        main_cat_seo = main_category["UrlFriendlyName"]
        main_cat_name = main_category["Description"]
        # Create entry for main category for products that aren't in any sub category
        category_id = f"Aisle.{normalise_category_name(main_cat_name)}"
        categories.append(
            {
                "id": main_category["NodeId"],
                "search_name": main_cat_name,
                "description": main_cat_name,
                "url": f"https://www.woolworths.com.au/shop/browse/{main_cat_seo}",
                "code": None,
            }
        )

    categories = hotprices_au.categories.merge_save_save_categories(
        "woolies", categories
    )

    category_map = {c["search_name"]: c for c in categories}
    return category_map


def get_category_from_map(category_map, raw_item):
    deptcategory_names = json.loads(
        raw_item["Products"][0]["AdditionalAttributes"]["piesdepartmentnamesjson"]
    )
    category_names = json.loads(
        raw_item["Products"][0]["AdditionalAttributes"]["piescategorynamesjson"]
    )
    subcategory_names = json.loads(
        raw_item["Products"][0]["AdditionalAttributes"]["piessubcategorynamesjson"]
    )
    current_favourite = None
    categories_to_check = subcategory_names + category_names + deptcategory_names
    for category_name in categories_to_check:
        candidate = category_map.get(category_name)
        if not candidate:
            continue
        if current_favourite is None:
            current_favourite = candidate
        candidate_path_depth = len(candidate["url"].split("/"))
        current_candidate_path_depth = len(current_favourite["url"].split("/"))
        if candidate_path_depth > current_candidate_path_depth:
            current_favourite = candidate

    if not current_favourite:
        # Try by dept data ID
        dept_data_list = json.loads(
            raw_item["Products"][0]["AdditionalAttributes"][
                "PiesProductDepartmentsjson"
            ]
        )
        for dept_data in dept_data_list:
            category_id = dept_data["Id"]
            for category in category_map.values():
                if category["id"] == category_id:
                    current_favourite = category
                    # Yes it only breaks the inner loop but it's unlikely there
                    # is more than one matching element and this case is
                    # incredibly rare anyway, only if the data is really bad so it
                    # doesn't matter
                    break

    # May need manual override
    if not current_favourite:
        match raw_item["Stockcode"]:
            case 283400:
                category_name = "Bakery"
        current_favourite = category_map[category_name]

    try:
        return current_favourite["code"]
    except Exception:
        import pprint

        pprint.pprint(raw_item)
        print(deptcategory_names)
        print(category_names)
        print(subcategory_names)
        import pdb

        pdb.set_trace()


if __name__ == "__main__":
    main()
