import argparse
import asyncio
import os
import shutil
import sys
from datetime import datetime, timedelta
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


async def command_cleanup(args):
    if args.all:
        confirm = "n"
        if args.y:
            confirm = "y"
        else:
            confirm = input("Are you sure you want to delete ALL pastes? y/n: ")
        if confirm.startswith("y"):
            shutil.rmtree(paste_root)
            paste_root.mkdir(parents=True, exist_ok=True)
        else:
            print("canceled")
    elif args.expired and args.older_than is None:
        paste_ids = helpers.get_all_paste_ids(paste_root)
        if args.expired:
            for id_ in paste_ids:
                paste_path = helpers.create_paste_path(paste_root, id_)
                meta = await helpers.read_paste_meta(paste_path)
                if meta.is_expired:
                    paste_path.unlink(missing_ok=True)
                    print(f"removed: '{id_}'")
                else:
                    print(f"skipping: '{id_}'")
    elif args.older_than:
        older_than = datetime.utcnow() - timedelta(days=args.older_than)

        confirm = "n"
        if args.y:
            confirm = "y"
        else:
            confirm = input(f"Are you sure you want to remove pastes created before '{older_than}'? y/n: ")

        if not confirm.startswith("y"):
            return

        paste_ids = helpers.get_all_paste_ids(paste_root)
        for id_ in paste_ids:
            paste_path = helpers.create_paste_path(paste_root, id_)
            meta = await helpers.read_paste_meta(paste_path)
            if (args.expired and meta.is_expired) or meta.creation_dt < older_than:
                paste_path.unlink(missing_ok=True)
                print(f"removed: '{id_}'")
            else:
                print(f"skipping: '{id_}'")
    else:
        print("no filters given, nothing removed")


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
    cleanup_parser = parsers.add_parser("cleanup", description="Cleanup pastes")
    cleanup_parser.set_defaults(func=command_cleanup)
    cleanup_parser.add_argument("-y", help="always confirm dialogues", nargs="?", const=True)
    cleanup_parser.add_argument("--all", help="select all pastes", nargs="?", const=True)
    cleanup_parser.add_argument("--expired", help="select expired pastes", nargs="?", const=True)
    cleanup_parser.add_argument("--older-than", help="select pastes created before given number of days", type=int)

    args = parser.parse_args()
    print(args)
    if args.paste_root:
        print(paste_root)
    else:
        await args.func(args)


if __name__ == "__main__":
    asyncio.run(main())
