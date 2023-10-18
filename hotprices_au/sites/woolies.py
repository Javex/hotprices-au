import math
import re
import requests
import json

from .. import output, request, units
import hotprices_au
from hotprices_au.logging import logger


class WooliesAPI:

    def __init__(self, quick=False):
        self.quick = quick


        self.session = request.get_base_session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'Origin': 'https://www.woolworths.com.au',
            'Referer': 'https://www.woolworths.com.au/shop/browse/fruit-veg',
            'Accept': 'application/json',
        }
        self._started = False
        self.start()

    def start(self):
        if not self._started:
            response = self.session.get('https://www.woolworths.com.au')
            response.raise_for_status()
            self._started = True

    def get_category(self, cat_id):
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
        request_data['categoryId'] = cat_id
        # Larger page size leads to an error, have to make do with 36 items per
        # page
        request_data['pageSize'] = 36
        product_count = 0
        page_count = None
        while True:
            if page_count is None:
                print(f'Page {request_data["pageNumber"]}')
            else:
                print(f'Page {request_data["pageNumber"]}/{page_count}')
            response = self.session.post(
                'https://www.woolworths.com.au/apis/ui/browse/category',
                json=request_data,
            )
            response.raise_for_status()
            response_data = response.json()
            for bundle in response_data['Bundles']:
                yield bundle

            # Next page calculation
            total_products = response_data['TotalRecordCount']

            # Warn once if we expect more products that it can return
            if total_products >= 10000 and page_count is None:
                logger.warn(f'Category {cat_id} has too many products: {total_products}. Will only be able to fetch 10,000.')

            bundle_size = len(response_data['Bundles'])
            product_count += bundle_size
            if product_count >= total_products or bundle_size == 0:
                # We're done
                break

            # Temporary speedup
            if self.quick:
                break

            # Not done, go to next page
            request_data['pageNumber'] += 1
            page_count = math.ceil(total_products / request_data['pageSize'])

    def get_categories(self):
        response = self.session.get('https://www.woolworths.com.au/apis/ui/PiesCategoriesWithSpecials')
        response.raise_for_status()
        response_data = response.json()
        category_data = response_data['Categories']
        categories = []
        for category_obj in category_data:
            if is_filtered_category(category_obj):
                continue
            categories.append(category_obj)
        return categories


def is_filtered_category(category_obj):
    cat_id = category_obj['NodeId']
    if cat_id == 'specialsgroup':
        # Skip for now, expect duplicate products
        return True

    cat_desc = category_obj['Description']
    if cat_desc == 'Front of Store':
        # Throws error, probably nothing special in here anyway
        return True

    return False


def get_canonical(item, today):
    if len(item['Products']) > 1:
        raise RuntimeError("More than one product, help")
    item = item['Products'][0]

    price = item['Price']
    unit = item['PackageSize']

    # If item is out of stock then price might be empty so we need to take the "WasPrice" field
    if price is None:
        price_was = item['WasPrice']
        if not item['IsInStock'] and price_was:
            price = price_was

    # The second case is to handle two products with that "size"
    if price is None or unit.lower() == "min. 250g":
        price = item['CupPrice']
        unit = item['CupMeasure']

    # Price is still None, can't do anything, skipping product
    if price is None:
        return None

    # Fix some particularly problematic products
    match item['Stockcode']:
        case 249086: unit = '1kg'  # Woolworths Pot Set Greek Style Yoghurt
        case 203793: unit = '2 pack'  # Nicorette Quit Smoking Quickmist Smart Track Mouth Spray Freshmint
        case 532887: unit = '700ml'  # Kahlua White Russian
        case 985323: unit = '800ml'  # Nelson County Bourbon & Cola
    result = {
        'id': item['Stockcode'],
        'name': item['Name'],
        'description': item['Description'],
        'price': price,
        'priceHistory': [{
            'date': today,
            'price': price,
        }],
        'isWeighted': False,  # TODO: What is this and how do I find it in woolies data?
    }

    try:
        quantity, unit = units.parse_str_unit(unit)
    except RuntimeError:
        # Not in stock and we can't use "WasPrice" because we can't parse the weird unit it uses.
        # No idea what the right price would be so just skip the product
        if not item['IsInStock']:
            return None
        elif item['Unit'].lower() == "each":
            unit = 'ea'
            quantity = 1
        else:
            print(f"Can't parse unit '{unit}' for item {result}")
            return None
    result['unit'] = unit
    result['quantity'] = quantity
    result = units.convert_unit(result)
    return result


def main(quick, save_path):
    woolies = WooliesAPI(quick=quick)
    categories = woolies.get_categories()
    #categories = load_cache()
    for category_obj in categories:
        cat_id = category_obj['NodeId']
        cat_desc = category_obj['Description']
        print(f'Fetching category {cat_id} ({cat_desc})')
        category = woolies.get_category(cat_id)
        all_category_bundles = list(category)
        category_obj['Products'] = all_category_bundles

        if quick:
            break
    output.save_data(categories, save_path)
    get_category_mapping(categories)


def normalise_category_name(category_name):
    category_name, _ = re.subn(r'[^A-Za-z]+', '', category_name)
    return category_name


def ensure_subcategories(raw_categories):
    """
    This exist for backfill reasons: Initial data doesn't have subcategories so
    we need to re-fetch that data if we don't have it yet. Can probably be
    removed once we've got it fixed.
    """
    has_children = False
    for main_cat in raw_categories:
        if main_cat.get('Children'):
            has_children = True
            break

    if has_children:
        return raw_categories
    else:
        woolies = WooliesAPI()
        return woolies.get_categories()


def get_category_mapping(raw_categories):
    "Raw woolies categories to standard format"
    categories = []
    raw_categories = ensure_subcategories(raw_categories)
    for main_category in raw_categories:
        if is_filtered_category(main_category):
            continue
        main_cat_seo = main_category['UrlFriendlyName']
        main_cat_name = main_category['Description']
        # Create entry for main category for products that aren't in any sub category
        category_id = f"Aisle.{normalise_category_name(main_cat_name)}"
        categories.append({
            'id': main_category['NodeId'],
            'search_name': main_cat_name,
            'description': main_cat_name,
            'url': f'https://www.woolworths.com.au/shop/browse/{main_cat_seo}',
            'code': None,
        })

        sub_categories = main_category.get('Children', [])
        if not sub_categories:
            raise RuntimeError("No subcats")
        for sub_category in sub_categories:
            sub_cat_seo = sub_category['UrlFriendlyName']
            sub_cat_name = sub_category['Description']
            sub_category_id = f"{category_id}.{normalise_category_name(sub_cat_name)}"
            sub_category_item = {
                'id': sub_category['NodeId'],
                'search_name': sub_cat_name,
                'description': f'{main_cat_name} > {sub_cat_name}',
                'url': f'https://www.woolworths.com.au/shop/browse/{main_cat_seo}/{sub_cat_seo}',
                'code': None,
            }
            categories.append(sub_category_item)

    categories = hotprices_au.categories.merge_save_save_categories('woolies', categories)

    category_map = {c['search_name']: c for c in categories}
    return category_map


def get_category_from_map(category_map, raw_item):
    deptcategory_names = json.loads(raw_item['Products'][0]['AdditionalAttributes']['piesdepartmentnamesjson'])
    category_names = json.loads(raw_item['Products'][0]['AdditionalAttributes']['piescategorynamesjson'])
    subcategory_names = json.loads(raw_item['Products'][0]['AdditionalAttributes']['piessubcategorynamesjson'])
    current_favourite = None
    categories_to_check = subcategory_names + category_names + deptcategory_names
    for category_name in categories_to_check:
        candidate = category_map.get(category_name)
        if not candidate:
            continue
        if current_favourite is None:
            current_favourite = candidate
        candidate_path_depth = len(candidate['url'].split('/'))
        current_candidate_path_depth = len(current_favourite['url'].split('/'))
        if candidate_path_depth > current_candidate_path_depth:
            current_favourite = candidate

    if not current_favourite:
        # Try by dept data ID
        dept_data_list = json.loads(raw_item['Products'][0]['AdditionalAttributes']['PiesProductDepartmentsjson'])
        for dept_data in dept_data_list:
            category_id = dept_data['Id']
            for category in category_map.values():
                if category['id'] == category_id:
                    current_favourite = category
                    # Yes it only breaks the inner loop but it's unlikely there
                    # is more than one matching element and this case is
                    # incredibly rare anyway, only if the data is really bad so it
                    # doesn't matter
                    break

    # May need manual override
    if not current_favourite:
        match raw_item['Stockcode']:
            case 283400: category_name = 'Bakery'
        current_favourite = category_map[category_name]

    try:
        return current_favourite['code']
    except Exception:
        import pprint; pprint.pprint(raw_item)
        print(deptcategory_names)
        print(category_names)
        print(subcategory_names)
        import pdb; pdb.set_trace()


if __name__ == '__main__':
    main()
