"""Filetype classifyer, specifically for a media server.

Main use case is providing a definitive media type (e.g. movies or music) for a
filetree. This module supports guessing based on the ratio of numbers of
filetypes and by pathname matching.
"""

import logging
import re
from collections.abc import Callable
from enum import Enum
from pathlib import Path

LOGGER = logging.getLogger(__name__)

# Min bin ratio to statistically assign MediaType
TYPE_RATIO_THRESHOLD = 0.7

# exact directory name match
IGNORED_PATHS = {
    "behind the scenes",
    "deleted scenes",
    "interviews",
    "scenes",
    "samples",
    "shorts",
    "featurettes",
    "clips",
    "other",
    "extras",
    "trailers",
    "theme-music",
    "backdrops",
}

IGNORED_SUFFIXES = [
    # textuals
    "doc",
    "md",
    "nfo",
    "rtf",
    "txt",
    # subtitles
    "ass",
    "idx",
    "srt",
    "sub",
    # images (assume it's album art or posters)
    "gif",
    "jpeg",
    "jpg",
    "png",
    "webp",
]


class MediaType(Enum):
    """Authoritative type for a given file or filetree.

    Enum has subdirectory field for placing media, and a boolean matcher
    function that takes a Path of a file to match.
    """

    def _match_path_suffix(path: Path, suffixes: set[str]):
        return path.suffix.lstrip(".") in suffixes

    # Parts is the pathlib.Path name for list of parent directories
    def _match_path_parts(path: Path, directories: set[str]):
        return len(directories.intersection(path.parts)) != 0
        # for part in path.parts:
        #    if part in directories:
        #        return True
        # return False

    def __init__(self, subdirectory: str, matcher: Callable[[Path], bool]):
        self.subdirectory: str = subdirectory
        self.matcher: Callable[[Path], bool] = matcher

    Unknown = ("unsorted", lambda _: False)
    Ignored = (
        "",
        lambda path: MediaType._match_path_suffix(
            path,
            set(IGNORED_SUFFIXES),
        ),
    )
    Book = (
        "books",
        lambda path: MediaType._match_path_suffix(
            path,
            {
                "djvu",
                "epub",
                "mobi",
                "pdf",
            },
        ),
    )
    Comic = ("comics", lambda path: MediaType._match_path_suffix(path, {"cbr", "cbz"}))
    Music = (
        "music",
        lambda path: MediaType._match_path_suffix(
            path,
            {
                "aac",
                "aiff",
                "ape",
                "flac",
                "mp3",
                "m4a",
                "opus",
                "wav",
            },
        ),
    )
    Movie = (
        "movies",
        lambda path: MediaType._match_path_suffix(
            path,
            {
                "avi",
                "mkv",
                "mov",
                "mp4",
                "webm",
            },
        ),
    )
    Serial = (
        "serials",
        lambda path: (
            (
                re.search(
                    "(_|\\b)(s.?\\d{1,2})?.?e.?\\d{1,2}(_|\\b)",
                    path.name,
                    re.IGNORECASE,
                )
                is not None
            )
            or (
                re.search(
                    "(_|\\b)s(eason)?.?\\d{1,2}(_|\\b)", path.__str__(), re.IGNORECASE
                )
                is not None
            )
        ),
    )
    Software = (
        "software",
        lambda path: MediaType._match_path_suffix(
            path, {"exe", "msi", "bin", "app", "pkg", "dmg"}
        ),
    )

    @classmethod
    def match_mediatype(cls, path: Path) -> "MediaType":
        for mediatype in cls:
            if mediatype.matcher(path):
                if (mediatype is MediaType.Movie) and (MediaType.Serial.matcher(path)):
                    LOGGER.debug(f"Identified serialized {path}")
                    return MediaType.Serial
                return mediatype

        LOGGER.debug(f"Failed to match mediatype for file: {path}")
        return MediaType.Unknown

    @staticmethod
    def infer_mediatype_from_filetree(filetree: Path) -> "MediaType":
        if not filetree.exists():
            raise RuntimeError(f"Filetree not found: {filetree}")

        if filetree.is_file():
            LOGGER.debug(f"Is a singleton: {filetree}")
            return MediaType.match_mediatype(filetree)

        # Create MediaType histogram
        type_counts: dict[MediaType, int] = {}
        for _, dirnames, files in filetree.walk(top_down=True):
            # list[:] is in-place modification
            # in-place modifying walk(top_down=True) skips traversal
            dirnames[:] = list(filter(lambda d: not d in IGNORED_PATHS, dirnames))

            for filename in files:
                mediatype = MediaType.match_mediatype(Path(filename))
                if mediatype == MediaType.Ignored:
                    continue
                if mediatype in type_counts:
                    type_counts[mediatype] += 1
                else:
                    type_counts[mediatype] = 1

        if len(type_counts) == 0:
            LOGGER.error(
                f"Filetree {filetree} empty, or all files are ignored."
                "\nCheck permissions or ignored suffixes list."
            )
            return MediaType.Unknown

        # If only one MediaType
        if len(type_counts) == 1:
            LOGGER.debug(f"Is a uniform tree: {filetree}")
            return type_counts.popitem()[0]  # gross

        # If top MediaType is at least a TYPE_THRESHOLD% majority
        LOGGER.debug("Inferring MediaType statistically...")
        all_count = sum(type_counts.values())
        top_type, top_count = max(type_counts.items(), key=lambda i: i[1])  # gross
        if (top_count / all_count) > TYPE_RATIO_THRESHOLD:
            return top_type
        LOGGER.debug(
            "Failed to infer MediaType statistically;"
            f" top type {top_type} only {100 * top_count / all_count:02.0f}% of files (needs {100 * TYPE_RATIO_THRESHOLD:02.0f}%)"
        )

        # Too much noise, or unsupported MediaType
        return MediaType.Unknown
