#!/usr/bin/env python3

"""Categorizes & hardlinks completed downloads to export directory for triage.

Guesses media category from suffixes & filepaths, and hardlinks given path to
categorized export directory.
"""

import argparse
import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from sys import exit

from media_tools.mediatype import MediaType

LOGGER = logging.getLogger(__name__)

EXPORT_DIRECTORY = "/sb1/xfer/xport/"


def main(args=None):
    __usage__ = "deluge_exporter [-l] [-dv] input [--output]"
    parser = argparse.ArgumentParser(description=__usage__)
    parser.add_argument(
        "input",
        default=None,
        type=str,
        help="Path to media root to be classified",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        type=str,
        help="If set, skip classification and link directly to this path",
    )
    parser.add_argument(
        "-l",
        "--log_to_syslog",
        default=False,
        action="store_true",
        help="Log to syslog (journal) instead of STDOUT/STDERR",
    )
    parser.add_argument(
        "-d",
        "--dry_run",
        action="store_true",
        default=False,
        help="Enable debug mode; perform no modifications",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Enable verbose output",
    )
    parsed_args = parser.parse_args(args)

    if parsed_args.verbose == 0:
        log_level = logging.WARNING
    elif parsed_args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    if parsed_args.log_to_syslog:
        LOGGER.addHandler(
            logging.handlers.SysLogHandler(
                address="/dev/log",
                facility=logging.handlers.SysLogHandler.LOG_DAEMON,
            )
        )

    if parsed_args.dry_run:
        LOGGER.info("Running in dry-run mode...")

    source_path = Path(parsed_args.input)
    if parsed_args.output is not None:
        destination_path = Path(parsed_args.output).resolve()
        if not (destination_path.exists() and destination_path.is_dir()):
            LOGGER.error(f"Overridden destination invalid: {destination_path}")
            return 1
    else:
        mediatype: MediaType = MediaType.infer_mediatype_from_filetree(source_path)
        LOGGER.debug(f"Inferred media type: {mediatype}")
        destination_path = Path(EXPORT_DIRECTORY).joinpath(mediatype.subdirectory)

    if not destination_path.exists():
        LOGGER.debug(f"Creating destination directory {destination_path}")
        if not parsed_args.dry_run:
            destination_path.mkdir(parents=True)

    destination_path = destination_path.joinpath(source_path.stem)
    LOGGER.info(f"Exporting {source_path} to {destination_path}")
    if not parsed_args.dry_run:
        # shutil.copytree requires src be a directory
        if source_path.is_file():
            destination_path.mkdir()
            destination_path = destination_path.joinpath(source_path.name)
            destination_path.hardlink_to(source_path)
        else:
            shutil.copytree(source_path, destination_path, copy_function=os.link)

    return 0


if __name__ == "__main__":
    exit(main())
