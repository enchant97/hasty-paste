import argparse
import os
import sys
from pathlib import Path

from . import helpers

paste_root = None


def command_view(args):
    if args.list:
        paste_ids = helpers.get_all_paste_ids(paste_root)
        for id_ in paste_ids:
            print(id_)


def main():
    global paste_root
    paste_root = os.environ.get("PASTE_ROOT")

    if not paste_root:
        sys.exit("PASTE_ROOT has not been set")

    paste_root = Path(paste_root)

    parser = argparse.ArgumentParser(description="The Hasty Paste Management CLI")
    parser.add_argument("--paste-root", help="show the configured paste root", nargs="?", const=True)
    parsers = parser.add_subparsers(help="Available Commands")
    view_parser = parsers.add_parser("view", description="View pastes")
    view_parser.set_defaults(func=command_view)
    view_parser.add_argument("--list", help="list the paste id's", nargs="?", const=True)

    args = parser.parse_args()

    if args.paste_root:
        print(paste_root)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
