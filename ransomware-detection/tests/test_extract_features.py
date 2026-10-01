from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from src.extract_features import extract_file


class StaticFeatureExtractionTests(unittest.TestCase):
    def test_rejects_unsupported_file_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "document.pdf"
            source.write_bytes(b"%PDF")

            with self.assertRaisesRegex(ValueError, r"\.exe.*\.zip"):
                extract_file(source, ["md5"])

    def test_extracts_executables_from_zip_without_unpacking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "samples.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("one.exe", b"MZ first")
                archive.writestr("folder/two.exe", b"MZ second")
                archive.writestr("notes.txt", b"not an executable")

            def fake_row(data: bytes, source_file: str, schema: list[str]):
                return {
                    "source_file": source_file,
                    "md5": data.decode("ascii"),
                }

            with patch("src.extract_features._feature_row", side_effect=fake_row):
                result = extract_file(archive_path, ["md5"])

            self.assertEqual(
                result["source_file"].tolist(),
                ["samples.zip!one.exe", "samples.zip!folder/two.exe"],
            )
            self.assertEqual(result["md5"].tolist(), ["MZ first", "MZ second"])
            self.assertEqual(list(root.iterdir()), [archive_path])

    def test_rejects_zip_without_executables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "empty.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("notes.txt", "no executable")

            with self.assertRaisesRegex(ValueError, "Não foram encontrados"):
                extract_file(archive_path, ["md5"])

    def test_rejects_executable_without_mz_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "not-pe.exe"
            source.write_bytes(b"not a PE")

            with self.assertRaisesRegex(ValueError, "cabeçalho MZ"):
                extract_file(source, ["md5"])
