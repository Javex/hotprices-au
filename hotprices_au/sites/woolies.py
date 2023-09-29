import requests
import json

from .. import output, request, units


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
                "filters": [],
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
        while True:
            print(f'Page {request_data["pageNumber"]}')
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

    def get_categories(self):
        response = self.session.get('https://www.woolworths.com.au/api/ui/v2/bootstrap')
        response.raise_for_status()
        response_data = response.json()
        categories = response_data['ListTopLevelPiesCategories']['Categories']
        return categories


def get_canonical(item, today):
    if len(item['Products']) > 1:
        raise RuntimeError("More than one product, help")
    item = item['Products'][0]

    # If item is out of stock then price might be empty so we need to take the "WasPrice" field
    price = item['CupPrice']
    unit = item['CupMeasure']
    if price is None:
        price = item['Price']
        unit = item['PackageSize']

    if price is None:
        price_was = item['WasPrice']
        if not item['IsInStock'] and price_was:
            price = price_was

    # Price is still None, can't do anything, skipping product
    if price is None:
        return None

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
    try:
        result = units.convert_unit(result)
    except KeyError:
        # Wrong data, fix manually
        if result['name'] == 'Kahlua White Russian' and result['unit'] == 'mm':
            result['unit'] = 'ml'
        elif result['name'] == 'Nelson County Bourbon & Cola' and result['unit'] == 'nl':
            result['unit'] = 'ml'
        else:
            raise
    return result



def main(quick):
    woolies = WooliesAPI(quick=quick)
    categories = woolies.get_categories()
    #categories = load_cache()
    for category_obj in categories:
        cat_id = category_obj['NodeId']
        if cat_id == "specialsgroup":
            # Skip for now, expect duplicate products
            continue

        if 'Products' in category_obj:
            # Already cached
            continue

        cat_desc = category_obj['Description']
        if cat_desc == 'Front of Store':
            # Throws error, probably nothing special in here anyway
            continue
        print(f'Fetching category {cat_id} ({cat_desc})')
        category = woolies.get_category(cat_id)
        all_category_bundles = list(category)
        category_obj['Products'] = all_category_bundles

        if quick:
            break
    output.save_data('woolies', categories, quick)


if __name__ == '__main__':
    main()
