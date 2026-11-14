#!/usr/bin/env python3

"""Categorizes & hardlinks completed downloads to export directory for triage.

Problem-to-Solve is to keep seeding and also tag, organize and import media on
completion without duplicating space. To automate process without keeping track
of what has been imported, what is ready to be deleted, deluge can call this
program on download complete and delete the original on seeding complete (if
ever).

Deluge Execute plugin expected to call this file with three positional arguments:

    export_on_complete.py <torrent_id> <torrent_name> <torrent_path>

In this program, the first two positional arguments are never used.

See the [Deluge Execute docs](https://deluge-torrent.org/plugins/execute/) for
more information on hook integration.
"""

import argparse
import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from sys import exit

from deluge_exporter.mediatype import MediaType

LOGGER = logging.getLogger(__name__)

# Used to double check the file is complete
# TODO: use deluge RPC API to check torrent state instead
COMPLETED_DIRECTORY = "/sb1/xfer/deluge/complete/"

EXPORT_DIRECTORY = "/sb1/xfer/xport/"

__version__ = "0.1.0"
__usage__ = "deluge_exporter_hook.py torrent_id torrent_name torrent_path"

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
    help="Path to torrent file or root directory",
)
parser.add_argument(
    "-d",
    "--destination",
    default=None,
    type=str,
    help="Ignore inferred destination and hardlink to supplied directory",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="Enable verbose output",
)
parser.add_argument(
    "--dry_run",
    action="store_true",
    default=False,
    help="Enable debug mode; perform no modifications",
)
parser.add_argument(
    "-l",
    "--log_to_syslog",
    default=False,
    action="store_true",
    help="Log to syslog instead of STDOUT/STDERR; useful for debugging automation",
)
args = parser.parse_args()


def main(args):
    if args.verbose == 0:
        log_level = logging.WARNING
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logging.basicConfig(level=log_level)

    if args.log_to_syslog:
        LOGGER.addHandler(logging.handlers.SysLogHandler("/var/run/syslog"))

    if args.dry_run:
        LOGGER.info("Running in dry-run mode...")

    LOGGER.info(
        f"Torrent ID: {args.torrent_id} Torrent Name: {args.torrent_name} Torrent Path: {args.torrent_path}"
    )

    # Safeguard in case the deluge plugin gets misconfigured
    source_path = Path(args.torrent_path)
    inbox_path = Path(COMPLETED_DIRECTORY)
    if not Path(
        os.path.commonpath([source_path.resolve(), inbox_path.resolve()])
    ).samefile(inbox_path):
        LOGGER.error(f"Torrent isn't complete (not in {inbox_path}):  {source_path}")
        return 1

    if args.destination is not None:
        destination_path = Path(args.destination).resolve()
        if not (destination_path.exists() and destination_path.is_dir()):
            LOGGER.error(f"Overridden destination invalid: {destination_path}")
            return 1
    else:
        mediatype: MediaType = MediaType.infer_mediatype_from_filetree(source_path)
        LOGGER.debug(f"Inferred media type: {mediatype}")
        destination_path = Path(EXPORT_DIRECTORY).joinpath(mediatype.subdirectory)

    if not destination_path.exists():
        LOGGER.debug(f"Creating destination directory {destination_path}")
        if not args.dry_run:
            destination_path.mkdir(parents=True)

    destination_path = destination_path.joinpath(source_path.stem)
    LOGGER.info(f"Exporting {source_path} to {destination_path}")
    if not args.dry_run:
        # shutil.copytree requires src be a directory
        if source_path.is_file():
            destination_path.mkdir()
            destination_path = destination_path.joinpath(source_path.name)
            destination_path.hardlink_to(source_path)
        else:
            shutil.copytree(source_path, destination_path, copy_function=os.link)

    return 0


if __name__ == "__main__":
    exit(main(args))
