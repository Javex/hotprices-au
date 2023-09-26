import pathlib
import json
from datetime import datetime


def save_data(store, categories):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    fname = f"{date_str}.json"
    save_dir = pathlib.Path(f"output/{store}")
    save_dir.mkdir(parents=True, exist_ok=True)
    fpath = save_dir / fname
    fpath.write_text(json.dumps(categories))