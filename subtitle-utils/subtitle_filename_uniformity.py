#!/usr/bin/env python3
# -*- coding: utf-8 -*- (PEP 263)
#
# subtitle_filename_uniformity.py - Renames and moves subtitles to match found related video
# companion.
#
# Author:   sez
# License:  GPL-3+
# Version:  0.1.0 (2026-10-04)
#
# SYNOPSIS
#   subtitle_filename_uniformity.py [--dry_run] [-rv] [--unsafe_matcher] dir1 dir2
#   cat newline_separated_list_of_dirs | subtitle_filename_uniformity.py [...]
#   subtitle_filename_uniformity.py [...] < newline_separated_list_of_dirs
#
# DESCRIPTION
#   Given a directory, finds a main piece of media (video formats), then finds
#   all subtitles recursively and renames them to match the main media.
#   If there is more than one video in the target directory, abort with code 1.
#   If there are two subtitles with the same name, say there are two english
#   subtitles with no other modifiers, skip file with code 2.
#
# DEPENDENCIES
#
# ARGUMENTS
#   FILES   list of files and directories
#   -v      Print all debug logs (optional
#
# EXIT CODES
#   0   Success
#   1   Path traversal error
#
# EXAMPLES
#   Directory tree before:
#     ./movie/
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/ITA.srt
#     ./movie/moviename.mkv
#   Directory tree after running `subtitle_filename_uniformity.py ./movie`:
#     ./movie/
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/moviename.ita.srt
#     ./movie/moviename.mkv
#
#   Directory tree before:
#     ./movie/
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/ITA.srt
#     ./movie/moviename.mkv
#   Directory tree after running `subtitle_filename_uniformity.py -r ./movie`:
#     ./movie/
#     ./movie/moviename.eng.srt
#     ./movie/moviename.ita.srt
#     ./movie/moviename.spa.sdh.srt
#     ./movie/moviename.mkv
#
#   Directory tree before:
#     ./movie/
#     ./movie/Extras/
#     ./movie/Extras/Featurette.mkv
#     ./movie/Extras/eng.srt
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/ITA.srt
#     ./movie/moviename.mkv
#   Directory tree after running `subtitle_filename_uniformity.py -r ./movie`:
#     ./movie/
#     ./movie/Extras/
#     ./movie/Extras/Featurette.mkv
#     ./movie/Extras/Featurette.eng.srt
#     ./movie/moviename.eng.srt
#     ./movie/moviename.ita.srt
#     ./movie/moviename.spa.sdh.srt
#     ./movie/moviename.mkv
#
#   Directory tree before:
#     ./movie/
#     ./movie/Extras/
#     ./movie/Extras/Featurette.mkv
#     ./movie/Extras/eng.srt
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/ITA.srt
#     ./movie/moviename_1.mkv
#     ./movie/moviename_2.mkv
#   Directory tree after running `subtitle_filename_uniformity.py -r ./movie`:
#     ./movie/
#     ./movie/Extras/
#     ./movie/Extras/Featurette.mkv
#     ./movie/Extras/Featurette.eng.srt
#     ./movie/Subs/
#     ./movie/Subs/ENG.srt
#     ./movie/Subs/unknown_SDH.SPA.HI.srt
#     ./movie/ITA.srt
#     ./movie/moviename_1.mkv
#     ./movie/moviename_2.mkv
#   And Exit Code 1 & error message

import argparse
import logging
import sys
import re
from pathlib import Path


__version__ = "0.1.0"
__usage__ = "subtitle_filename_uniformity.py [--dry_run] [-rv] [--unsafe_matcher] dir1 dir2"

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description=__usage__)
parser.add_argument(
    "directories",
    action="extend",
    default=None,
    nargs="*",
    type=str,
    help="Directories to search",
)
parser.add_argument(
    "infile",
    default=(None if sys.stdin.isatty() else sys.stdin),
    nargs="?",
    type=argparse.FileType("r"),
    help="Read directories to search via stdin",
)
parser.add_argument(
    "-r",
    "--recursive",
    action="store_true",
    help="Search recursively and delete empty folders",
)
parser.add_argument(
    "-v", "--verbose", action="count", default=0, help="Enable verbose output"
)
parser.add_argument(
    "--dry_run", action="store_true", help="Modify nothing; print potential changes"
)
parser.add_argument(
    "-u",
    "--unsafe_matcher",
    action="store_true",
    default=False,
    help="Automatically check 2-letter codes against filenames",
)
parser.add_argument(
    "--increment_on_collision",
    action="store_true",
    default=True,
    help="Add a number to the filename to avoid file collisions; else, skip renaming files that would collide",
)
parser.add_argument(
    "--default_language_code",
    default=None,
    help="Use given language code for all subtitles where one couldn't be automatically detected",
)
args = parser.parse_args()

_VIDEO_EXTENSIONS: list[str] = [
    "avi",
    "mkv",
    "mov",
    "mp4",
    "webm",
]

_SUBTITLE_EXTENSIONS: list[str] = [
    "srt",
    "ass",
    "sub",
    "idx",
]

# Columns in same order as https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
_LANGUAGE_CODES: dict[str, dict[str, list]] = {
    "ara": {"name": ["arabic"], "set1": ["ar"], "set2": ["ara"]},
    "bod": {"name": ["tibetan"], "set1": ["bo"], "set2": ["bod", "tib", "bod"]},
    "cat": {"name": ["catalan", "valencian"], "set1": ["ca"], "set2": ["cat"]},
    "ces": {"name": ["czech"], "set1": ["cs"], "set2": ["ces", "cze"]},
    "chi": {"name": ["chinese"], "set1": ["zh"], "set2": ["zho", "chi"]},
    "cym": {"name": ["welsh"], "set1": ["cy"], "set2": ["cym", "wel"]},
    "dan": {"name": ["danish"], "set1": ["da"], "set2": ["dan"]},
    "deu": {"name": ["german"], "set1": ["de"], "set2": ["deu", "ger"]},
    "ell": {"name": ["greek"], "set1": ["el"], "set2": ["ell", "gre"]},
    "eng": {"name": ["english"], "set1": ["en"], "set2": ["eng"]},
    "est": {"name": ["estonian"], "set1": ["et"], "set2": ["est"]},
    "fas": {"name": ["persian"], "set1": ["fa"], "set2": ["fas", "per"]},
    "fin": {"name": ["finnish"], "set1": ["fi"], "set2": ["fin"]},
    "fra": {"name": ["french"], "set1": ["fr"], "set2": ["fra", "fre"]},
    "gla": {"name": ["gaelic"], "set1": ["gd"], "set2": ["gla"]},
    "guj": {"name": ["gujarati"], "set1": ["gu"], "set2": ["guj"]},
    "heb": {"name": ["hebrew"], "set1": ["he"], "set2": ["heb"]},
    "hin": {"name": ["hindi"], "set1": ["hi"], "set2": ["hin"]},
    "hrv": {"name": ["croatian"], "set1": ["hr"], "set2": ["hrv"]},
    "hun": {"name": ["hungarian"], "set1": ["hu"], "set2": ["hun"]},
    "ind": {"name": ["indonesian"], "set1": ["id"], "set2": ["ind"]},
    "isl": {"name": ["icelandic"], "set1": ["is"], "set2": ["isl", "ice"]},
    "ita": {"name": ["italian"], "set1": ["it"], "set2": ["ita"]},
    "jpn": {"name": ["japanese"], "set1": ["ja"], "set2": ["jpn"]},
    "kat": {"name": ["georgian"], "set1": ["ka"], "set2": ["kat", "geo"]},
    "kor": {"name": ["korean"], "set1": ["ko"], "set2": ["kor"]},
    "lit": {"name": ["lithuanian"], "set1": ["lt"], "set2": ["lit"]},
    "msa": {"name": ["malay"], "set1": ["ms"], "set2": ["msa", "may"]},
    "nld": {"name": ["dutch"], "set1": ["nl"], "set2": ["nld", "dut"]},
    "nor": {"name": ["norwegian"], "set1": ["no"], "set2": ["nor"]},
    "nob": {"name": ["bokmal", "bokmål"], "set1": ["nb"], "set2": ["nob"]},
    "nno": {"name": ["nynorsk"], "set1": ["nn"], "set2": ["nno"]},
    "pan": {"name": ["punjabi", "panjabi"], "set1": ["pa"], "set2": ["pan"]},
    "pol": {"name": ["polish"], "set1": ["pl"], "set2": ["pol"]},
    "por": {
        "name": ["portuguese"],
        "set1": ["pt"],
        "set2": ["por", "ptb", "ptbr", "pt-br"],
    },
    "pus": {"name": ["pashto", "pushto"], "set1": ["ps"], "set2": ["pus"]},
    "rum": {
        "name": ["romanian", "moldavian", "moldovan"],
        "set1": ["ro"],
        "set2": ["ron", "rum", "rom"],
    },
    "rus": {"name": ["russian"], "set1": ["ru"], "set2": ["rus"]},
    "slv": {"name": ["slovenian"], "set1": ["sl"], "set2": ["slv"]},
    "spa": {"name": ["spanish"], "set1": ["es", "sp"], "set2": ["spa", "esp"]},
    "srp": {"name": ["serbian"], "set1": ["sr"], "set2": ["srp"]},
    "swa": {"name": ["swahili"], "set1": ["sw"], "set2": ["swa"]},
    "swe": {"name": ["swedish"], "set1": ["sv"], "set2": ["swe"]},
    "tam": {"name": ["tamil"], "set1": ["ta"], "set2": ["tam"]},
    "tgl": {"name": ["tagalog"], "set1": ["tl"], "set2": ["fil", "tgl"]},
    "tel": {"name": ["telugu"], "set1": ["te"], "set2": ["tel"]},
    "tha": {"name": ["thai"], "set1": ["th"], "set2": ["tha"]},
    "tur": {"name": ["turkish"], "set1": ["tr"], "set2": ["tur"]},
    "ukr": {"name": ["ukrainian"], "set1": ["uk"], "set2": ["ukr"]},
    "urd": {"name": ["urdu"], "set1": ["ur"], "set2": ["urd"]},
    "vie": {"name": ["vietnamese"], "set1": ["vi"], "set2": ["vie"]},
    "zha": {"name": ["zhuang", "chuang"], "set1": ["za"], "set2": ["zha"]},
    "multi": {
        "name": ["multi", "mult"],
        "set1": [],
        "set2": [],
    },  # Subtitle files with more than one language; unique to idx/sub companion files
}

_ROLE_CODES: dict[str, list] = {
    "simplified": ["simplified"],  # Specific to chinese
    "traditional": ["traditional"],  # Specific to chinese
    "forced": ["forced"],  # Subtitles for only foreign-language audio
    "SDH": ["sdh", "hi", "cc"],  # Subtitles for the Deaf and Hard of hearing
}


def find_files_with_extensions(directory: Path, extensions: list[str]) -> list[Path]:
    """
    Finds all files matching given extensions in given directory.

    Args:
        directory: directory to search

    Returns:
        sorted list of matching files

    Raises:
        RuntimeError if passed a non-directory
    """
    if not directory.is_dir():
        raise RuntimeError(f"Unexpected non-directory: {directory}")

    filepaths: list[Path] = []
    for ext in extensions:
        filepaths += directory.glob(f"[!.]*.{ext}")

    return sorted(filepaths)


def find_videos(directory: Path) -> list[Path]:
    return find_files_with_extensions(directory, _VIDEO_EXTENSIONS)


def find_subtitles(directory: Path) -> list[Path]:
    return find_files_with_extensions(directory, _SUBTITLE_EXTENSIONS)


def get_language_code(filepath: Path) -> str | None:
    """
    Matches a filename to a language code by checking first full language names,
    then 3-letter codes, then 2-letter codes.

    Args:
        filepath: Path to check against. Only checks against Path.stem, but uses
        the whole path for debugging.

    Returns:
        First matched language code if found or None otherwise
    """
    filename = filepath.stem.lower()
    for key in ["name", "set2", "set1"]:
        if key == "set1" and not args.unsafe_matcher:
            # Already reading from stdin; input() will either read erroneos data
            # or raise EOFError
            if not sys.stdin.isatty():
                return None

            # TODO sez: add delete option
            while True:
                user_input = input(
                    "\n"
                    f"No 3-letter+ language codes found in '{filepath}'.\n"
                    "➜ [S]kip, [A]bort, [C]heck 2-letter codes, [P]rint contents,\n"
                    "➜ leave [U]nspecified, label [E]nglish, [I]nput label? "
                ).lower()
                if user_input == "e":
                    return ".eng"
                elif user_input == "i":
                    return f".{input("Enter language code:\n➜ ")}"
                elif user_input == "u":
                    return ""
                elif user_input == "c":
                    # TODO sez: re-prompt if no 2-letter code is found
                    break
                elif user_input == "a":
                    sys.exit(2)
                elif user_input == "s":
                    return None
                elif user_input == "p":
                    # TODO sez: it's late; i'm tired... fix this
                    try:
                        with open(filepath, mode="r") as file:
                            for _ in range(20):
                                print(file.readline())
                    except UnicodeDecodeError as e:
                        try:
                            with open(filepath, mode="r", encoding="ascii") as file:
                                for _ in range(20):
                                    print(file.readline())
                        except UnicodeDecodeError as e:
                            try:
                                with open(
                                    filepath, mode="r", encoding="latin_1"
                                ) as file:
                                    for _ in range(20):
                                        print(file.readline())
                            except UnicodeDecodeError as e:
                                logger.error(
                                    f"coudn't open subtitle file '{filepath}' as utf-8, ASCII, or Latin-1; giving up."
                                )

        for language in _LANGUAGE_CODES:
            for language_code in _LANGUAGE_CODES[language][key]:
                # TODO sez: Profile.
                # Would it be better to precompile these? How much more memory
                # intensive is this than 'in'?
                pattern: re.Pattern = re.compile(f"(?:\\b|_){language_code}(?:\\b|_)")
                if pattern.search(filename):
                    return f".{language}"

    if args.default_language_code:
        return f".{args.default_language_code}"

    return None


def get_role_codes(filename: str) -> str | None:
    """
    Matches a filename to a role code, which is an optional modifyier like
    'forced' or 'HI'.

    Args:
        filename: string to check against known codes

    Returns:
        list of matched role codes
    """
    filename = filename.lower()
    codes: list[str] = []
    for role in _ROLE_CODES:
        for role_code in _ROLE_CODES[role]:
            pattern: re.Pattern = re.compile(f"(?:\\b|_){role_code}(?:\\b|_)")
            if pattern.search(filename):
                codes.append(role)
                # Many subtitles are names ~'SDH.eng.HI'. Avoid renaming to 'eng.SDH.SDH'
                break
    if not codes:
        return None
    else:
        return f".{'.'.join(codes)}"


def recursive_rename_subtitles(directory: Path, recursive: bool = False) -> list[Path]:
    """
    Recursively renames all subtitle filetypes to match video filetype in
    directory.

    Args:
        directory: Path to search

    Returns:
        list of subtitles to rename if no video found, or an empty list if
        either no subtitles were found or all were successfully renamed

    Raises:
        RuntimeError if passed an non-directory
    """
    if not directory.is_dir():
        raise RuntimeError(f"Unexpected non-directory: '{directory}'")

    subtitles: list[Path] = []
    # TODO sez: is this necessary, to declare outside of conditional?
    # TODO sez: rename consistently (sub_ -> subtitle_; subtitles -> subtitle_paths)
    sub_directories: list[Path] = []
    if recursive:
        sub_directories = sorted(directory.glob("[!.]*/"))

        logger.debug(f"found {len(sub_directories)} directories in {directory}")
        logger.debug(sub_directories)

        for sub_directory in sub_directories:
            subtitles += recursive_rename_subtitles(sub_directory)

    subtitles += find_subtitles(directory)
    logging.debug(f"processing {len(subtitles)} subtitles in directory {directory}")

    videos: list[Path] = find_videos(directory)
    if len(videos) == 0:
        return subtitles
    elif len(videos) > 1:
        logger.warning(f"Too many videos found in {directory}: {videos}")
        return []
    base_name: str = videos[0].stem

    for subtitle in subtitles:
        language_code: str | None = get_language_code(subtitle)
        role_codes: str | None = get_role_codes(str(subtitle.stem))
        if language_code == None:
            logger.warning(f"No language code matched for file '{subtitle}'. Skipping.")
            continue

        # TODO sez: clean, deduplicate
        new_subtitle: Path = directory.joinpath(
            f"{base_name}{language_code}{role_codes if role_codes else ''}{subtitle.suffix}"
        )
        # TODO sez: more reliably handle subtitle collisions, it currently
        # renames everything every time.
        if new_subtitle == subtitle:
            continue
        if args.increment_on_collision and new_subtitle.exists():
            count: int = 0
            while new_subtitle.exists():
                count += 1
                new_subtitle = directory.joinpath(
                    f"{base_name}{language_code}{role_codes if role_codes else ''}.{count}{subtitle.suffix}"
                )
                if new_subtitle == subtitle:
                    break
            # TODO sez: figure it out; python doesn't support break-to or
            # continue-to, so I have to break then immediately continue
            if new_subtitle == subtitle:
                continue

        logger.info(f"Renaming {subtitle} to {new_subtitle}")
        if not args.dry_run:
            subtitle.rename(new_subtitle)

    if recursive:
        for sub_directory in sub_directories:
            if not args.dry_run:
                logger.info(f"attempting to remove '{sub_directory}'...")
                try:
                    sub_directory.rmdir()
                except OSError as e:
                    if e.errno == 39:
                        # TODO sez: prompt to ls/rm anyway
                        logger.info(f"directory not empty: '{sub_directory}'")
                    else:
                        raise e
    return []


def main(args):
    if args.verbose == 0:
        log_level = logging.WARNING
    elif args.verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if args.dry_run:
        logger.info("Running in dry-run mode...")

    # TODO sez: error codes
    # print(f"cli: {args.directories}, stdin: {args.infile}")
    if args.directories is not None:
        for directory in args.directories:
            directory = directory.rstrip()
            logger.debug(f"Scanning location '{directory}'...")
            leftovers: list[Path] = recursive_rename_subtitles(Path(directory).resolve(), args.recursive)
            if leftovers:
                logger.warning(f"Failed to process {len(leftovers)} files: {leftovers}")
                return 1
    # Can't combine blocks because the following one doesn't load all of stdin
    # into memory. Adding to a list would be wasteful.
    if args.infile is not None:
        for directory in args.infile:
            directory = directory.rstrip()
            logger.debug(f"Scanning location '{directory}'...")
            leftovers: list[Path] = recursive_rename_subtitles(Path(directory).resolve(), args.recursive)
            if leftovers:
                logger.warning(f"Failed to process {len(leftovers)} files: {leftovers}")
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(args))
