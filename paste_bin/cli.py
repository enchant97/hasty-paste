import argparse
import asyncio
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .core.storage import DiskStorage


class CliController:
    def __init__(self, storage: DiskStorage) -> None:
        self._storage = storage

    async def process_args(self, args):
        if args.paste_root:
            print(self._storage._paste_root)
        else:
            try:
                await args.func(args)
            except AttributeError:
                print("no command given, using '--help' to get help")

    async def command_view(self, args):
        if args.list:
            paste_ids = self._storage.read_all_paste_ids()
            if args.expired:
                async for id_ in paste_ids:
                    paste_path = self._storage._create_paste_path(id_)
                    meta = await self._storage.read_paste_meta(id_)
                    if meta is not None and meta.is_expired:
                        print(paste_path if args.locate else id_)
            else:
                async for id_ in paste_ids:
                    if args.locate:
                        paste_path = self._storage._create_paste_path(id_)
                        print(paste_path)
                    else:
                        print(id_)

    async def command_cleanup(self, args):
        if args.all:
            confirm = "n"
            if args.y:
                confirm = "y"
            else:
                confirm = input(
                    "Are you sure you want to delete ALL pastes? y/n: ")
            if confirm.startswith("y"):
                shutil.rmtree(self._storage._paste_root)
                self._storage._paste_root.mkdir(parents=True, exist_ok=True)
            else:
                print("canceled")
        elif args.expired and args.older_than is None:
            paste_ids = self._storage.read_all_paste_ids()
            if args.expired:
                async for id_ in paste_ids:
                    meta = await self._storage.read_paste_meta(id_)
                    if meta is not None and meta.is_expired:
                        await self._storage.delete_paste(id_)
                        print(f"removed: '{id_}'")
                    else:
                        print(f"skipping: '{id_}'")
        elif args.older_than:
            older_than = datetime.utcnow() - timedelta(days=args.older_than)

            confirm = "n"
            if args.y:
                confirm = "y"
            else:
                confirm = input(
                    f"Are you sure you want to remove pastes created before '{older_than}'? y/n: ")

            if not confirm.startswith("y"):
                return

            paste_ids = self._storage.read_all_paste_ids()
            async for id_ in paste_ids:
                meta = await self._storage.read_paste_meta(id_)
                if meta is not None and ((args.expired and meta.is_expired) or meta.creation_dt < older_than):
                    await self._storage.delete_paste(id_)
                    print(f"removed: '{id_}'")
                else:
                    print(f"skipping: '{id_}'")
        elif args.directories:
            dirs_removed = 0
            for path in self._storage._paste_root.iterdir():
                if path.is_dir():
                    try:
                        path.rmdir()
                        dirs_removed += 1
                    except OSError:
                        # directory was not empty
                        pass
            print(f"cleaned {dirs_removed} empty directories")
        else:
            print("no filters given, nothing removed")


async def main():
    paste_root = os.environ.get("STORAGE__DISK__PASTE_ROOT")

    if not paste_root:
        sys.exit("STORAGE__DISK__PASTE_ROOT has not been set")

    paste_root = Path(paste_root)
    paste_root.mkdir(parents=True, exist_ok=True)

    cli = CliController(DiskStorage(paste_root))

    parser = argparse.ArgumentParser(description="The Hasty Paste Management CLI. " +
                                     "Please be aware this CLI is experimental, " +
                                     "usage may change without notice."
                                     )
    parser.add_argument(
        "--paste-root", help="show the configured paste root", action="store_true")
    parsers = parser.add_subparsers(help="Available Commands")
    view_parser = parsers.add_parser("view", description="View pastes")
    view_parser.set_defaults(func=cli.command_view)
    view_parser.add_argument(
        "--list", help="list the paste id's", action="store_true")
    view_parser.add_argument(
        "--expired", help="only select expired", action="store_true")
    view_parser.add_argument(
        "--locate", help="show the filepath to paste(s)", action="store_true")
    cleanup_parser = parsers.add_parser(
        "cleanup", description="Cleanup pastes")
    cleanup_parser.set_defaults(func=cli.command_cleanup)
    cleanup_parser.add_argument(
        "-y", help="always confirm dialogues", action="store_true")
    cleanup_parser.add_argument(
        "--all", help="select all pastes", action="store_true")
    cleanup_parser.add_argument(
        "--expired", help="select expired pastes", action="store_true")
    cleanup_parser.add_argument(
        "--older-than", help="select pastes created before given number of days", type=int)
    cleanup_parser.add_argument(
        "--directories", help="remove empty directories", action="store_true",
    )

    args = parser.parse_args()
    await cli.process_args(args)


if __name__ == "__main__":
    asyncio.run(main())
