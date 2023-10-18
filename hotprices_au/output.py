import pathlib
import json
import gzip
from datetime import datetime


def get_save_path(store, output_dir, compression='gzip', day=None):
    if day is None:
        day = datetime.now()
    date_str = day.strftime("%Y-%m-%d")

    fname = f"{date_str}.json"
    save_dir = output_dir / store
    save_dir.mkdir(parents=True, exist_ok=True)
    fpath = save_dir / fname
    if compression == 'gzip':
        fpath = fpath.with_suffix('.json.gz')
    return fpath


def save_data(categories, save_path, compression='gzip'):
    if compression == 'gzip':
        with gzip.open(save_path, 'wt') as fp:
            fp.write(json.dumps(categories))
    elif compression is None:
        save_path.write_text(json.dumps(categories))
    else:
        raise RuntimeError(f"Unsupported compression '{compression}'")


def load_data(store, output_dir, compression='gzip', day=None):
    fpath = get_save_path(store, output_dir, compression, day)
    if compression == 'gzip':
        with gzip.open(fpath, 'rt') as fp:
            raw_data = fp.read()
    elif compression is None:
        raw_data = fpath.read_text()
    else:
        raise RuntimeError(f"Unsupported compression '{compression}'")

    decoded_data = json.loads(raw_data)
    return decoded_data