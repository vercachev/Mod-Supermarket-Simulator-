"""Тесты Cookie Clicker SaveHandler."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from samples.sample_save_data import make_export_string, write_samples  # noqa: E402
from save_handler import SaveHandler  # noqa: E402
from utils.validator import ValidationError, validate_cookies  # noqa: E402


class CookieSaveTests(unittest.TestCase):
    def test_load_and_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_samples(Path(tmp))
            h = SaveHandler()
            h.load(path)
            self.assertEqual(h.get_snapshot().cookies, 12345)
            h.set_cookies(1_000_000_000)
            out = Path(tmp) / "edited.txt"
            h.save(out)
            h2 = SaveHandler()
            h2.load(out)
            self.assertEqual(h2.get_snapshot().cookies, 1_000_000_000)

    def test_paste_string(self) -> None:
        text = make_export_string(999)
        h = SaveHandler()
        h.load_text(text)
        self.assertEqual(h.get_snapshot().cookies, 999)
        h.set_cookies(42)
        again = h.to_export_string()
        h3 = SaveHandler()
        h3.load_text(again)
        self.assertEqual(h3.get_snapshot().cookies, 42)

    def test_unescaped(self) -> None:
        text = make_export_string(55, escaped=False)
        h = SaveHandler()
        h.load_text(text)
        self.assertEqual(h.get_snapshot().cookies, 55)


class ValidatorTests(unittest.TestCase):
    def test_ok(self) -> None:
        self.assertEqual(validate_cookies("1e12"), 1e12)

    def test_bad(self) -> None:
        with self.assertRaises(ValidationError):
            validate_cookies(-5)


if __name__ == "__main__":
    unittest.main()
