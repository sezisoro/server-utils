#!/usr/bin/env python
# -*- coding: utf-8 -*- (PEP 263)

import os
import shutil
from pathlib import Path
from unittest import TestCase, main

from ..deluge_hooks import Exporter

# TODO: consider /tmp/ instead
TC_SOURCE_DIRECTORY = "./tmp/source/"
TC_DEST_DIRECTORY = "./tmp/dest/"


class TestWithFiles(TestCase):
    test_source_path: Path
    test_dest_path: Path

    def setUp(self) -> None:
        self.test_source_path = Path(TC_SOURCE_DIRECTORY)
        self.test_dest_path = Path(TC_DEST_DIRECTORY)
        self.test_source_path.mkdir(parents=True)
        self.test_source_path.mkdir(parents=True)
        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_source_path)
        shutil.rmtree(self.test_dest_path)
        return super().tearDown()


class TestArguments(TestWithFiles):
    def test_dry_run_does_nothing(self):
        mock_media_name = "movie.mkv"
        mock_media_source_path = self.test_source_path / mock_media_name
        mock_media_dest_path = self.test_source_path / mock_media_name
        mock_media_source_path.touch()
        Exporter.hardlink_to_destination(mock_media_source_path, self.test_dest_path)
        self.assertFalse(mock_media_dest_path.exists())
        self.assertEqual(mock_media_source_path.stat().st_nlink, 0)
        self.assertRaises(self.test_dest_path.iterdir().__next__(), StopIteration)


class TestInfersMediaType(TestCase):
    def test_infers_single_book(self):
        pass

    def test_infers_single_comic(self):
        pass

    def test_infers_single_movie(self):
        pass

    def test_infers_movie_with_extras(self):
        pass

    def test_infers_single_music(self):
        pass

    def test_infers_serial_season_directory(self):
        pass

    def test_infers_serial_season_with_extras(self):
        pass

    def test_infers_serial_similar_videos(self):
        pass


class TestGetsMediaTypeFromDeluge(TestCase):
    def test_deluge_api_works(self):
        pass


class TestLinksFile(TestWithFiles):
    def test_creates_media_type_dirs(self):
        pass

    def test_checks_download_is_complete(self):
        pass

    def test_wrap_individual_files(self):
        pass


class TestFailureModes(TestCase):
    def test_error_on_collision(self):
        pass


if __name__ == "__main__":
    main()
