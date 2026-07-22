"""Тесты Supermarket Together SaveHandler + ES3 + paths."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from samples.sample_save_data import make_encrypted_bytes, make_save_dict, write_samples  # noqa: E402
from save_handler import (  # noqa: E402
    SaveHandler,
    patch_es3_numeric_field,
)
from utils.backup import BackupManager  # noqa: E402
from utils.constants import ES3_PASSWORD  # noqa: E402
from utils.es3_crypto import decrypt_raw, encrypt  # noqa: E402
from utils.paths import (  # noqa: E402
    canonical_store_path,
    is_under_backups,
)
from utils.validator import ValidationError, validate_funds  # noqa: E402


class Es3CryptoTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        plain = b'{"Funds":{"__type":"float","value":42}}\n'
        blob = encrypt(plain, ES3_PASSWORD, key_size=16)
        out, ks = decrypt_raw(blob, ES3_PASSWORD)
        self.assertEqual(ks, 16)
        self.assertEqual(out, plain)


class PathTests(unittest.TestCase):
    def test_canonical_from_backup(self) -> None:
        p = Path("/tmp/DDTNL/Supermarket Together/backups/StoreFile1_backup_2024.es3")
        self.assertTrue(is_under_backups(p))
        self.assertEqual(
            canonical_store_path(p),
            Path("/tmp/DDTNL/Supermarket Together/StoreFile1.es3"),
        )

    def test_canonical_edited(self) -> None:
        p = Path("/tmp/StoreFile1_EDITED.es3")
        self.assertEqual(canonical_store_path(p), Path("/tmp/StoreFile1.es3"))


class PatchTests(unittest.TestCase):
    def test_surgical_preserves_rest(self) -> None:
        text = json.dumps(make_save_dict(100.5), indent=4)
        new = patch_es3_numeric_field(text, "Funds", 999999)
        self.assertIn('"value": 999999', new)
        self.assertIn('"StoreName"', new)
        self.assertIn("TestMart", new)
        # ключи кроме Funds value не должны пропасть
        self.assertIn("FranchisePoints", new)


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

    def test_surgical_keeps_unrelated_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_samples(Path(tmp))
            h = SaveHandler()
            h.load(path)
            before = h._plain_text
            h.set_funds(777)
            after = h.build_plaintext()
            self.assertNotEqual(before, after)
            self.assertIn('"Difficulty"', after)
            self.assertIn("TestMart", after)
            data = json.loads(after)
            self.assertEqual(data["Funds"]["value"], 777)

    def test_refuse_save_to_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Supermarket Together"
            backups = root / "backups"
            backups.mkdir(parents=True)
            src = write_samples(root)
            # move sample into backups-like name
            bad = backups / "StoreFile1_backup_x.es3"
            bad.write_bytes(src.read_bytes())
            h = SaveHandler()
            h.load(bad)
            with self.assertRaises(ValueError):
                h.save(bad)

    def test_apply_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Supermarket Together"
            root.mkdir()
            game = root / "StoreFile1.es3"
            game.write_bytes(make_encrypted_bytes(50))
            h = SaveHandler()
            h.load(game)
            h.set_funds(123456)
            h.save(game)
            h2 = SaveHandler()
            h2.load(game)
            self.assertEqual(h2.get_snapshot().funds, 123456)

    def test_backup_manager_rejects_backups_src(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            bdir = root / "backups"
            bdir.mkdir(parents=True)
            f = bdir / "StoreFile1_backup_x.es3"
            f.write_bytes(make_encrypted_bytes(1))
            mgr = BackupManager()
            with self.assertRaises(ValueError):
                mgr.create_backup(f)

    def test_backup_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "game"
            root.mkdir()
            f = root / "StoreFile1.es3"
            f.write_bytes(make_encrypted_bytes(10))
            info = BackupManager().create_backup(f)
            self.assertTrue(info.path.exists())
            self.assertEqual(info.path.parent.name, "backups")

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
