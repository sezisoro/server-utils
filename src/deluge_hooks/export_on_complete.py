#!/usr/bin/env python

"""Hardlinks completed downloads to separate directory for formatting.

Expected to be called from Deluge's Execute plugin on event 'Torrent Complete'.

Workflow is to hardlink files so that the torrent remains seeding, the files
are added to the library using the correct naming conventions, the user doesn't
have to remember which torrents can safely be removed, and no space is wasted.

Execute plugin expected to call this file with three positional arguments:

    export_on_complete.py <torrent_id> <torrent_name> <torrent_path>

See the [Deluge Execute docs](https://deluge-torrent.org/plugins/execute/) for
more information on hook integration.
"""

import argparse
import logging
import os
from enum import Enum
from pathlib import Path
from sys import exit

__version__ = "0.1.0"
__usage__ = "flietype_blocklist.py torrent_id torrent_name torrent_path"

COMPLETED_DOWNLOAD_PATHNAME = "/sb1/xfer/deluge/complete/"
EXPORTED_DOWNLOAD_PATHNAME = "/sb1/xfer/xport/"

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description=__usage__)
parser.add_argument(
    "torrent_id",
    default=None,
    type=str,
    help="ID for interacting with torrents via the Deluge RPC API",
)
parser.add_argument(
    "torrent_name",
    default=None,
    type=str,
    help="Name of torrent",
)
parser.add_argument(
    "torrent_path",
    default=None,
    type=str,
    help=(
        "Location of torrent files\n"
        "Note this directory may depend on the state of the torrent"
    ),
)
parser.add_argument(
    "-v",
    "--verbose",
    # action="count",
    # default=0,
    action="store_true",
    default=False,
    help="Enable verbose output",
)
parser.add_argument(
    "--dry_run",
    action="store_true",
    default=True,
    help="Enable debug mode; perform no modifications",
)
args = parser.parse_args()


class Exporter:
    class MediaType(Enum):
        Unknown = 0
        Book = 1
        Comic = 2
        Movie = 3
        Music = 4
        Serial = 5

        def getMediaTypeSubdir(self) -> Path:
            if self.value == Exporter.MediaType.Book:
                return Path("/books")
            elif self.value == Exporter.MediaType.Comic:
                return Path("/comics")
            elif self.value == Exporter.MediaType.Movie:
                return Path("movie")
            elif self.value == Exporter.MediaType.Serial:
                return Path("/serial")
            else:
                return Path("/unsorted")

    @staticmethod
    def infer_media_type(to_infer: Path) -> Exporter.MediaType:
        if not to_infer.exists():
            logger.error(f"Source not found: {to_infer}")
            raise RuntimeError(f"Given a nonexistent path: {to_infer}")

        # Attempt to get the media type from Deluge
        # Scan the directory tree and return the most frequent extension
        return Exporter.MediaType.Unknown

    @staticmethod
    def hardlink_to_destination(source: Path, export_directory: Path) -> None:
        if not source.exists():
            raise RuntimeError(f"File or directory not found: {source}")

        media_type = Exporter.infer_media_type(source)
        destination = export_directory.joinpath(media_type.getMediaTypeSubdir())

        # Every piece of media gets a directory
        if not source.is_dir():
            destination = destination.joinpath(source.stem)
            destination.mkdir()

        logger.info(f"Linking {source} to {destination}")
        if not args.dry_run:
            destination.mkdir(parents=True)
            destination.hardlink_to(source)


def main(args):
    if args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    # if args.verbose == 0:
    #    log_level = logging.WARNING
    # elif args.verbose == 1:
    #    log_level = logging.INFO
    # else:
    #    log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if args.dry_run:
        logger.info("Running in dry-run mode...")

    logger.info(
        f"Torrent ID: {args.rorrent_id} Torrent Name: {args.torrent_name} Torrent Path: {args.torrent_path}"
    )

    # Ensure the torrent is downloaded
    finished_download_path = Path(COMPLETED_DOWNLOAD_PATHNAME)
    torrent_source_path = Path(args.torrent_path)
    if (
        not os.path.commonpath([torrent_source_path, finished_download_path])
        == finished_download_path
    ):
        logger.error(
            f"Received a torrent that isn't complete (not in {finished_download_path}):  {torrent_source_path}"
        )
        return 1

    logger.info(f"Exporting {torrent_source_path}")
    hardlink_to_destination(torrent_source_path, Path(EXPORTED_DOWNLOAD_PATHNAME))
    return 0


if __name__ == "__main__":
    exit(main(args))
