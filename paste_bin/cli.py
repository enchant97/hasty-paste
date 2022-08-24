import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import helpers

paste_root = None


async def command_view(args):
    if args.list:
        paste_ids = helpers.get_all_paste_ids(paste_root)
        if args.expired:
            for id_ in paste_ids:
                paste_path = helpers.create_paste_path(paste_root, id_)
                meta = await helpers.read_paste_meta(paste_path)
                if meta.is_expired:
                    print(paste_path if args.locate else id_)
        else:
            for id_ in paste_ids:
                if args.locate:
                    paste_path = helpers.create_paste_path(paste_root, id_)
                    print(paste_path)
                else:
                    print(id_)


async def main():
    global paste_root
    paste_root = os.environ.get("PASTE_ROOT")

    if not paste_root:
        sys.exit("PASTE_ROOT has not been set")

    paste_root = Path(paste_root)

    parser = argparse.ArgumentParser(description="The Hasty Paste Management CLI. " +
        "Please be aware this CLI is experimental, usage may change without notice."
    )
    parser.add_argument("--paste-root", help="show the configured paste root", nargs="?", const=True)
    parsers = parser.add_subparsers(help="Available Commands")
    view_parser = parsers.add_parser("view", description="View pastes")
    view_parser.set_defaults(func=command_view)
    view_parser.add_argument("--list", help="list the paste id's", nargs="?", const=True)
    view_parser.add_argument("--expired", help="only select expired", nargs="?", const=True)
    view_parser.add_argument("--locate", help="show the filepath to paste(s)", nargs="?", const=True)

    args = parser.parse_args()

    if args.paste_root:
        print(paste_root)
    else:
        await args.func(args)


if __name__ == "__main__":
    asyncio.run(main())
