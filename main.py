import argparse
import logging
from datetime import datetime
import pathlib
from hotprices_au import sites, analysis


def main_sync(args):
    sites.sites[args.store].main(args.quick, args.output_dir)


def main_analysis(args):
    data_dir = pathlib.Path('static/data')
    analysis.transform_data(args.day, args.output_dir, data_dir, args.store)


def parse_date(date):
    return datetime.strptime(date, '%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path('output'))

    subparsers = parser.add_subparsers(help='sub-command help')

    sync_parser = subparsers.add_parser('sync')
    sync_parser.add_argument('--quick', action='store_true', default=False)
    sync_parser.add_argument('store', choices=list(sites.sites))
    sync_parser.set_defaults(func=main_sync)

    analysis_parser = subparsers.add_parser('analysis')
    analysis_parser.add_argument('--day', type=parse_date, default=datetime.now())
    analysis_parser.add_argument('--store', choices=list(sites.sites))
    analysis_parser.set_defaults(func=main_analysis)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    args.func(args)


if __name__ == '__main__':
    main()