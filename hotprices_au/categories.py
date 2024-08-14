import json
import pathlib

from hotprices_au.logging import logger

PKG_DATA_FOLDER = pathlib.Path(__file__).parent / "data"


def merge_save_save_categories(store, categories):
    store_file = PKG_DATA_FOLDER / f"{store}-categories.json"
    # Create folder if it doesn't exist
    PKG_DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    if store_file.exists():
        old_mapping = json.loads(store_file.read_text())
        old_lookup = {c["id"]: c for c in old_mapping}

        for category in categories:
            old_category = old_lookup.pop(category["id"], None)
            if old_category is None:
                logger.info(
                    f"Found new unmapped category for {store}: {category['id']} - {category['description']}"
                )
            else:
                category["code"] = old_category["code"]

        if old_lookup:
            for old_cat in old_lookup.values():
                logger.info(
                    f"Found category absent in latest mapping for {store}: "
                    f"{old_cat['id']} - {old_cat['description']}"
                )
                categories.append(old_cat)

    store_file.write_text(json.dumps(categories, indent=2))
    return categories
