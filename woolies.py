import requests
import json
import sys


class WooliesAPI:

    def __init__(self, quick=False):
        self.quick = quick


        self.session = requests.Session()
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


def load_cache():
    with open('woolies_all.json') as f:
        cache_data = json.loads(f.read())
    return cache_data


def save_cache(cache_data):
    with open('woolies_all.json', 'w') as f:
        f.write(json.dumps(cache_data))


def main():
    quick = False
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick = True
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
        #save_cache(categories)
    with open('woolies_all.json', 'w') as f:
        f.write(json.dumps(categories))
    #print(json.dumps(category, indent=4))


if __name__ == '__main__':
    main()
