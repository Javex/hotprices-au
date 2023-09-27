import pathlib
import json
import gzip
from datetime import datetime


def save_data(store, categories, compression='gzip'):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    fname = f"{date_str}.json"
    save_dir = pathlib.Path(f"output/{store}")
    save_dir.mkdir(parents=True, exist_ok=True)
    fpath = save_dir / fname

    if compression == 'gzip':
        fpath = fpath.with_suffix('.json.gz')
        with gzip.open(fpath, 'wt') as fp:
            fp.write(json.dumps(categories))
    elif compression is None:
        fpath.write_text(json.dumps(categories))
    else:
        raise RuntimeError(f"Unsupported compression '{compression}'")