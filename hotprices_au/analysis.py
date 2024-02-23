from datetime import datetime
import gzip
import json
import pathlib

from .logging import logger
from . import output, sites


def get_canoncial_for(store, raw_items, category_map, today):
    canonical_items = []
    store_module = sites.sites[store]
    for raw_item in raw_items:
        try:
            canonical_item = store_module.get_canonical(raw_item, today)
        except Exception:
            logger.exception(f"Unable to process store '{store}' item: {raw_item}")
            import pprint; pprint.pprint(raw_item)
            raise
        if canonical_item is None:
            continue
        canonical_item['store'] = store
        try:
            canonical_item['category'] = store_module.get_category_from_map(category_map, raw_item)
        except KeyError:
            canonical_item['category'] = None
        canonical_items.append(canonical_item)
    return canonical_items


def dedup_items(items):
    lookup = {}
    dedup_items = []
    duplicates = {}
    for item in items:
        seen_item = lookup.get((item['store'], item['id']))
        if not seen_item:
            lookup[(item['store'], item['id'])] = item
            dedup_items.append(item)
        else:
            duplicates.setdefault(item['store'], 0)
            duplicates[item['store']] += 1

    if duplicates:
        logger.info(f'Deduplicated items: {json.dumps(duplicates)}')

    return dedup_items


def merge_price_history(old_items, new_items, store_filter):
    if old_items is None:
        return new_items

    lookup = {}
    for old_item in old_items:
        if store_filter is not None and old_item['store'] != store_filter:
            new_items.append(old_item)
        else:
            lookup[(old_item['store'], old_item['id'])] = old_item

    new_prices = {}
    for new_item in new_items:
        old_item = lookup.pop((new_item['store'], new_item['id']), None)
        current_price = new_item['priceHistory'][0]['price']
        if old_item:
            old_price = old_item['priceHistory'][0]['price']
            if old_price == current_price:
                new_item['priceHistory'] = old_item['priceHistory']
            else:
                new_prices.setdefault(new_item['store'], 0)
                new_prices[new_item['store']] += 1
                new_item['priceHistory'] += old_item['priceHistory']

    if lookup:
        logger.info(f'{len(lookup)} products not in latest list.')

    for store, new_price_count in new_prices.items():
        if new_price_count:
            logger.info(f"Store '{store}' has {new_price_count} new prices")

    return new_items


def copy_items_to_site(latest_canonical_file, data_dir: pathlib.Path, compress):
    with gzip.open(latest_canonical_file, 'rt') as fp:
        all_items = json.loads(fp.read())

    by_store = {}
    for item in all_items:
        by_store.setdefault(item['store'], []).append(item)

    # Create data dir if it doesn't exist yet
    data_dir.mkdir(parents=True, exist_ok=True)

    for store, store_items in by_store.items():
        latest_canonical_file_store = pathlib.Path(data_dir / f"latest-canonical.{store}.compressed.json")
        store_data = json.dumps(store_items)
        if compress:
            latest_canonical_file_store = latest_canonical_file_store.with_suffix('.json.gz')
            with gzip.open(latest_canonical_file_store, 'wt') as fp:
                fp.write(store_data)
        else:
            latest_canonical_file_store.write_text(store_data)


def transform_data(
        day, output_dir, data_dir,
        store_filter=None,
        compress=False,
        require_history=True
    ):
    """
    require_history: Whether to expect the "latest-canonical.json.gz" to
        already exist. Default is true (updating history) but can be set
        to false if doing a full history build.
    """
    all_items = []
    for store in sites.sites.keys():
        if store_filter is not None and store_filter != store:
            # Skip if we only transform one store
            continue
        store_items = []
        raw_categories = output.load_data(store, output_dir, day=day)
        # Let's try and figure out categories
        store_module = sites.sites[store]
        category_map = store_module.get_category_mapping(raw_categories)

        for category in raw_categories:
            try:
                raw_items = category['Products']
            except KeyError:
                # Don't have items for this category
                continue

            canonical_items = get_canoncial_for(store, raw_items, category_map, day.strftime('%Y-%m-%d'))
            store_items += canonical_items

        store_items = dedup_items(store_items)

        uncategorised = 0
        for item in store_items:
            if item['category'] is None:
                uncategorised += 1

        logger.info(f"Total number of products for store '{store}': {len(store_items)}. Uncategorised: {uncategorised}")
        all_items += store_items

    latest_canonical_file = pathlib.Path(output_dir / "latest-canonical.json.gz")
    if latest_canonical_file.exists() or require_history:
        with gzip.open(latest_canonical_file, 'rt') as fp:
            old_items = json.loads(fp.read())
        all_items = merge_price_history(old_items, all_items, store_filter)
    
    with gzip.open(latest_canonical_file, 'wt') as fp:
        fp.write(json.dumps(all_items))

    copy_items_to_site(latest_canonical_file, data_dir, compress)
    return all_items


def parse_full_history(output_dir: pathlib.Path, data_dir, store_filter=None, compress=False):
    # First remove canonical data
    latest_canonical_file = output_dir / "latest-canonical.json.gz"
    if latest_canonical_file.exists():
        latest_canonical_file.unlink()
    # List all stores in output_dir first
    for store in output_dir.iterdir():
        if store.name not in sites.sites:
            # Files we can ignore
            continue
        if store_filter is not None and store.name != store_filter:
            # We filter here so we do one store at a time
            continue
        for data_file in sorted(store.iterdir()):
            fname = data_file.name
            day = datetime.strptime(fname.split('.')[0], '%Y-%m-%d')
            transform_data(day, output_dir, data_dir, store_filter=store.name, compress=compress, require_history=False)