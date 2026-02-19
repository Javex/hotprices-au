import argparse
import logging
from datetime import datetime
import pathlib
from hotprices_au import sites, analysis, output


def main_sync(args):
    save_path = output.get_save_path(args.store, args.output_dir)
    if args.print_save_path:
        print(save_path.relative_to(args.output_dir), end="")
    elif args.skip_existing and save_path.exists():
        print(
            f"Skipping because outputfile {save_path} already exists and "
            f"requested to skip if output file exists."
        )
    else:
        sites.sites[args.store].main(args.quick, save_path, args.category, args.page, request_delay=args.request_delay)


def main_analysis(args):
    data_dir = pathlib.Path("static/data")
    if args.history:
        analysis.parse_full_history(
            args.output_dir, data_dir, args.store, args.compress
        )
    else:
        analysis.transform_data(
            args.day, args.output_dir, data_dir, args.store, args.compress
        )


def parse_date(date):
    return datetime.strptime(date, "%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument(
        "--output-dir", type=pathlib.Path, default=pathlib.Path("output")
    )

    subparsers = parser.add_subparsers(help="sub-command help")

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--quick", action="store_true", default=False)
    sync_parser.add_argument(
        "--print-save-path",
        action="store_true",
        default=False,
        help="Print relative path where file will be stored, then exit",
    )
    sync_parser.add_argument("--skip-existing", action="store_true", default=False)
    sync_parser.add_argument("--category", help="Fetch a particular category only.")
    sync_parser.add_argument(
        "--page",
        help="Only fetch one particular page. Useful when also using the --category option.",
        type=int,
    )
    sync_parser.add_argument(
        "--request-delay",
        type=float,
        default=2.0,
        dest="request_delay",
        help="Delay in seconds between page requests to avoid bot protection. Set to 0 to disable. (default: 2.0)",
    )
    sync_parser.add_argument("store", choices=list(sites.sites))
    sync_parser.set_defaults(func=main_sync)

    analysis_parser = subparsers.add_parser("analysis")
    analysis_parser.add_argument("--day", type=parse_date, default=datetime.now())
    analysis_parser.add_argument("--store", choices=list(sites.sites))
    analysis_parser.add_argument(
        "--compress",
        action="store_true",
        default=False,
        help=(
            "Whether to compress the individual store files. The main canonical "
            "file will always be compressed."
        ),
    )
    analysis_parser.add_argument(
        "--history",
        action="store_true",
        default=False,
        help="Read the entire history and re-generate information from source",
    )
    analysis_parser.set_defaults(func=main_analysis)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    args.func(args)


if __name__ == "__main__":
    main()

