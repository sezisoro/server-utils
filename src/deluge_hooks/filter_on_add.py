#!/usr/bin/env python
# -*- coding: utf-8 -*- (PEP 263)
#
# TODO: pick syslog or logging
# https://deluge-torrent.org/plugins/execute/
# https://deluge-torrent.org/development/plugins/

import argparse
import logging
import re
from pathlib import Path
from sys import argv, exit
from syslog import syslog

from deluge.core.rpcserver import export

__version__ = "0.1.0"
__usage__ = "flietype_blocklist.py torrent_id torrent_name torrent_path"

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
    default=False,
    help="Enable debug mode; perform no modifications",
)
args = parser.parse_args()

syslog("deluge test: the script started running")
for arg in argv[1:]:
    syslog(arg)


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

    return 0


if __name__ == "__main__":
    exit(main(args))
