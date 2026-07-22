"""Тесты Supermarket Together SaveHandler + ES3."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from samples.sample_save_data import make_encrypted_bytes, write_samples  # noqa: E402
from save_handler import SaveHandler  # noqa: E402
from utils.constants import ES3_PASSWORD  # noqa: E402
from utils.es3_crypto import decrypt_raw, encrypt  # noqa: E402
from utils.validator import ValidationError, validate_funds  # noqa: E402


class Es3CryptoTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        plain = b'{"Funds":{"__type":"float","value":42}}\n'
        blob = encrypt(plain, ES3_PASSWORD, key_size=16)
        out, ks = decrypt_raw(blob, ES3_PASSWORD)
        self.assertEqual(ks, 16)
        self.assertEqual(out, plain)


class TogetherSaveTests(unittest.TestCase):
    def test_load_and_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_samples(Path(tmp))
            h = SaveHandler()
            h.load(path)
            self.assertEqual(h.get_snapshot().funds, 12345.0)
            h.set_funds(1_000_000)
            h.set_franchise_points(99)
            out = Path(tmp) / "edited.es3"
            h.save(out)
            h2 = SaveHandler()
            h2.load(out)
            self.assertEqual(h2.get_snapshot().funds, 1_000_000)
            self.assertEqual(h2.get_snapshot().franchise_points, 99)
            self.assertTrue(h2.meta.encrypted)

    def test_load_bytes(self) -> None:
        blob = make_encrypted_bytes(777)
        h = SaveHandler()
        h.load_bytes(blob)
        self.assertEqual(h.get_snapshot().funds, 777)

    def test_plain_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_samples(Path(tmp))
            json_path = Path(tmp) / "StoreFile0_sample.json"
            h = SaveHandler()
            h.load(json_path)
            self.assertFalse(h.meta.encrypted)
            h.set_funds(50)
            out = Path(tmp) / "plain_out.json"
            h.save(out)
            text = out.read_text(encoding="utf-8")
            self.assertIn('"value": 50', text)


class ValidatorTests(unittest.TestCase):
    def test_ok(self) -> None:
        self.assertEqual(validate_funds("100000"), 100000.0)

    def test_bad(self) -> None:
        with self.assertRaises(ValidationError):
            validate_funds(-5)


if __name__ == "__main__":
    unittest.main()
