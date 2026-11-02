from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from libs.mediatype import MediaType


@pytest.mark.parametrize(
    "filename,expected_mediatype",
    [
        (x, MediaType.Book)
        for x in [
            "test.epub",
            "test.mobi",
            "test.pdf",
            "test.djvu",
        ]
    ]
    + [
        (x, MediaType.Comic)
        for x in [
            "test.cbr",
            "test.cbz",
        ]
    ]
    + [
        (x, MediaType.Music)
        for x in [
            "test.aac",
            "test.aiff",
            "test.ape",
            "test.opus",
            "test.mp3",
            "test.m4a",
            "test.flac",
            "test.wav",
        ]
    ]
    + [
        (x, MediaType.Movie)
        for x in [
            "test.mov",
            "test.mp4",
            "test.mkv",
            "test.webm",
        ]
    ]
    + [
        (x, MediaType.Ignored)
        for x in [
            "test.txt",
            "test.nfo",
            "test.idx",
            "test.sub",
            "test.srt",
            "test.ass",
        ]
    ]
    + [
        (x, MediaType.Unknown)
        for x in [
            "test.rar",
            "test.zip",
            "test.conf",
        ]
    ]
    + [
        (x, MediaType.Serial)
        for x in [
            "test_S01E01.mkv",
            "test_EP01.mkv",
            "season 1/test.mkv",
        ]
    ]
    + [
        (x, MediaType.Book)
        for x in [
            "test_S01E01.epub",
            "test_EP01.epub",
            "season 1/test.epub",
        ]
    ],
)
def test_matches_mediatype_from_suffix(filename: str, expected_mediatype: MediaType):
    """Sanity check singleton files are correctly classified.

    Individual files won't trigger directory traversal, but still require
    the path to be a file.
    """
    assert MediaType.match_mediatype(Path(filename)) == expected_mediatype


@pytest.mark.parametrize(
    "root,filetree,expected_mediatype",
    [
        # Books
        ("test.epub", ["test.epub"], MediaType.Book),
        ("test/", ["test/b1.epub", "test/b2.epub", "test/info.nfo"], MediaType.Book),
        # Comics
        ("test.cbz", ["test.cbz"], MediaType.Comic),
        (
            "test/",
            [
                "test/v1.cbz",
                "test/v2.cbr",
                "test/info.nfo",
                "test/v1_cover.png",
                "test/v2_cover.png",
                "test/test_cover.png",
            ],
            MediaType.Comic,
        ),
        # Music
        ("record.wav", ["record.wav"], MediaType.Music),
        (
            "mixed_test/",
            [
                "mixed_test/01.mp3",
                "mixed_test/02.aac",
                "mixed_test/03.m4a",
                "mixed_test/04.wav",
                "mixed_test/05.aiff",
                "mixed_test/06.opus",
                "mixed_test/07.ape",
                "mixed_test/cover.png",
            ],
            MediaType.Music,
        ),
        # Movies
        ("movie.mkv", ["movie.mkv"], MediaType.Movie),
        ("movie/", ["movie/movie.mkv", "movie/sub.srt"], MediaType.Movie),
        (
            "movie/",
            [
                "movie/movie.mkv",
                "movie/sub_1.srt",
                "movie/sub_2.srt",
                "movie/poster.jpg",
            ],
            MediaType.Movie,
        ),
        (
            "movie/",
            [
                "movie/movie.mkv",
                "movie/extras/sample.avi",
                "movie/extras/trailer.avi",
                "movie/subs/sub_1.srt",
                "movie/subs/sub_2.srt",
                "movie/poster.jpg",
            ],
            MediaType.Movie,
        ),
    ],
)
def test_infers_mediatype_from_filetree(
    fs: FakeFilesystem, root: str, filetree: list[str], expected_mediatype: MediaType
):
    for file in filetree:
        fs.create_file(file)

    assert MediaType.infer_mediatype_from_filetree(Path(root)) == expected_mediatype


@pytest.mark.parametrize(
    "root,filetree,expected_mediatype",
    [
        (
            "test_histo/",
            [
                "test_histo/movie.mkv",
                "test_histo/errata1.txt",
                "test_histo/errata2.txt",
                "test_histo/errata3.txt",
            ],
            MediaType.Movie,
        ),
        (
            "test_mixed/",
            [
                "test_mixed/movie.mkv",
                "test_mixed/errata1.txt",
                "test_mixed/errata2.gif",
                "test_mixed/errata3.nfo",
                "test_mixed/errata4.doc",
                "test_mixed/errata5.md",
                "test_mixed/errata6.nfo",
                "test_mixed/errata7.rtf",
                "test_mixed/errata8.txt",
                "test_mixed/errata9.ass",
                "test_mixed/errata10.idx",
                "test_mixed/errata11.srt",
                "test_mixed/errata12.sub",
            ],
            MediaType.Movie,
        ),
    ],
)
def test_ignored_filetypes(
    fs: FakeFilesystem, root: str, filetree: list[str], expected_mediatype: MediaType
):
    for file in filetree:
        fs.create_file(file)

    assert MediaType.infer_mediatype_from_filetree(Path(root)) == expected_mediatype


@pytest.mark.parametrize(
    "root,filetree,expected_mediatype",
    [
        (
            "sanity/",
            [
                "sanity/movie.mkv",
                "sanity/errata1.pdf",
                "sanity/errata2.pdf",
                "sanity/errata3.pdf",
            ],
            MediaType.Book,
        ),
        (
            "test_histo/",
            [
                "test_histo/movie.mkv",
                "test_histo/extras/errata1.pdf",
                "test_histo/extras/errata2.pdf",
                "test_histo/extras/errata3.pdf",
            ],
            MediaType.Movie,
        ),
        (
            "test_mixed/",
            [
                "test_mixed/movie.mkv",
                "test_mixed/extras/errata1.pdf",
                "test_mixed/extras/errata2.pdf",
                "test_mixed/extras/errata3.pdf",
            ],
            MediaType.Movie,
        ),
        (
            "test_strict_ignored_name/",
            [
                "test_strict_ignored_name/movie.mkv",
                "test_strict_ignored_name/wrong_name_extras/errata1.pdf",
                "test_strict_ignored_name/wrong_name_extras/errata2.pdf",
                "test_strict_ignored_name/wrong_name_extras/errata3.pdf",
            ],
            MediaType.Book,
        ),
    ],
)
def test_ignored_directories(
    fs: FakeFilesystem, root: str, filetree: list[str], expected_mediatype: MediaType
):
    for file in filetree:
        fs.create_file(file)

    assert MediaType.infer_mediatype_from_filetree(Path(root)) == expected_mediatype


@pytest.mark.parametrize(
    "root,filetree,expected_mediatype",
    [
        (
            "movie/",
            [
                "movie/movie.avi",
                "movie/extras/subdir/01.mp3",
                "movie/extras/subdir/02.mp3",
                "movie/extras/subdir/03.mp3",
                "movie/extras/subdir/04.mp3",
            ],
            MediaType.Movie,
        ),
        (
            "album/",
            [
                "album/01.wav",
                "album/interviews/01.avi",
                "album/interviews/02.avi",
                "album/interviews/03.avi",
                "album/interviews/04.avi",
            ],
            MediaType.Music,
        ),
        (
            "movie_with_serialized_extras/",
            [
                "movie_with_serialized_extras/movie.avi",
                "movie_with_serialized_extras/extras/subdir/E01.avi",
                "movie_with_serialized_extras/extras/subdir/E02.avi",
                "movie_with_serialized_extras/extras/subdir/E03.avi",
                "movie_with_serialized_extras/extras/subdir/E04.avi",
            ],
            MediaType.Movie,
        ),
    ],
)
def test_ignores_extras_directories(
    fs: FakeFilesystem, root: str, filetree: list[str], expected_mediatype: MediaType
):
    for file in filetree:
        fs.create_file(file)

    assert MediaType.infer_mediatype_from_filetree(Path(root)) == expected_mediatype


@pytest.mark.parametrize(
    "root,filetree",
    [
        (
            "show_season_folder/",
            [
                "show_season_folder/test_name_Season_01/E01.avi",
                "show_season_folder/test_name_Season_01/E02.avi",
                "show_season_folder/test_name_Season_01/E03.avi",
                "show_season_folder/test_name_Season_01/E04.avi",
                "show_season_folder/extras/trailer.avi",
            ],
        ),
        (
            "show_season_folder_spaces/",
            [
                "show_season_folder_spaces/test_name_Season 01/E01.avi",
                "show_season_folder_spaces/test_name_Season 01/E02.avi",
                "show_season_folder_spaces/test_name_Season 01/E03.avi",
                "show_season_folder_spaces/test_name_Season 01/E04.avi",
                "show_season_folder_spaces/extras/trailer.avi",
            ],
        ),
        (
            "show_season_folder_short_name/",
            [
                "show_season_folder_short_name/test_name_S01/E01.avi",
                "show_season_folder_short_name/test_name_S01/E02.avi",
                "show_season_folder_short_name/test_name_S01/E03.avi",
                "show_season_folder_short_name/test_name_S01/E04.avi",
                "show_season_folder_short_name/extras/trailer.avi",
            ],
        ),
        (
            "show_serialized_name/",
            [
                "show_serialized_name/S01E01.avi",
                "show_serialized_name/S01E02.avi",
                "show_serialized_name/S01E03.avi",
                "show_serialized_name/S01E04.avi",
                "show_serialized_name/extras/trailer.avi",
            ],
        ),
        (
            "show_serialized_name_spaces/",
            [
                "show_serialized_name_spaces/S01 E01.avi",
                "show_serialized_name_spaces/S01 E02.avi",
                "show_serialized_name_spaces/S01 E03.avi",
                "show_serialized_name_spaces/S01 E04.avi",
                "show_serialized_name_spaces/extras/trailer.avi",
            ],
        ),
        (
            "show_serialized_short_name/",
            [
                "show_serialized_short_name/E01.avi",
                "show_serialized_short_name/E02.avi",
                "show_serialized_short_name/E03.avi",
                "show_serialized_short_name/E04.avi",
                "show_serialized_short_name/extras/trailer.avi",
            ],
        ),
    ],
)
def test_infers_serial_mediatype_from_filetree(
    fs: FakeFilesystem, root: str, filetree: list[str]
):
    for file in filetree:
        fs.create_file(file)

    assert MediaType.infer_mediatype_from_filetree(Path(root)) == MediaType.Serial
