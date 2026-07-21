"""Автотесты SaveHandler / BackupManager / Validator (без GUI)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from samples.sample_save_data import SAMPLE_SAVE  # noqa: E402
from save_handler import SaveHandler  # noqa: E402
from utils.backup import BackupManager  # noqa: E402
from utils.constants import ALL_LICENSE_IDS, BASIC_LICENSE_ID  # noqa: E402
from utils.validator import ValidationError, validate_funds  # noqa: E402


class SaveHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "SaveFile.es3"
        self.path.write_text(
            json.dumps(SAMPLE_SAVE, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self.handler = SaveHandler()
        self.handler.load(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_load_money_and_day(self) -> None:
        snap = self.handler.get_snapshot()
        self.assertAlmostEqual(snap.money, 15420.5)
        self.assertEqual(snap.day, 7)
        self.assertEqual(snap.store_name, "Мой Маркет")
        self.assertEqual(snap.licenses, [21, 22])
        self.assertEqual(self.handler.meta.format_kind, "es3_typed")
        self.assertEqual(self.handler.meta.game_version, "0.9.0-sample")

    def test_set_money_preserves_es3_structure(self) -> None:
        self.handler.set_field("money", 999999.0)
        prog = self.handler.data["Progression"]
        self.assertIn("__type", prog)
        self.assertEqual(prog["value"]["Money"], 999999.0)

    def test_unlock_all_licenses(self) -> None:
        self.handler.set_all_licenses()
        snap = self.handler.get_snapshot()
        self.assertEqual(snap.licenses, ALL_LICENSE_IDS)

    def test_reset_licenses(self) -> None:
        self.handler.reset_licenses()
        self.assertEqual(self.handler.get_snapshot().licenses, [BASIC_LICENSE_ID])

    def test_save_roundtrip(self) -> None:
        self.handler.set_field("money", 12345)
        self.handler.set_field("day", 30)
        self.handler.save()
        h2 = SaveHandler()
        h2.load(self.path)
        snap = h2.get_snapshot()
        self.assertEqual(snap.money, 12345)
        self.assertEqual(snap.day, 30)

    def test_apply_raw_json(self) -> None:
        text = self.handler.to_pretty_json()
        data = json.loads(text)
        data["Progression"]["value"]["Money"] = 42
        self.handler.apply_raw_json(json.dumps(data))
        self.assertEqual(self.handler.get_snapshot().money, 42)

    def test_corrupt_file(self) -> None:
        bad = Path(self.tmp.name) / "bad.es3"
        bad.write_bytes(b"\x00\x01\x02encrypted")
        with self.assertRaises(ValueError):
            SaveHandler().load(bad)

    def test_plain_json_funds_alias(self) -> None:
        plain = Path(self.tmp.name) / "plain.es3"
        plain.write_text(
            json.dumps({"Funds": 100, "Day": 3, "UnlockedLicenses": [21]}, indent=2),
            encoding="utf-8",
        )
        h = SaveHandler()
        h.load(plain)
        snap = h.get_snapshot()
        self.assertEqual(snap.money, 100)
        self.assertEqual(snap.day, 3)


class BackupTests(unittest.TestCase):
    def test_backup_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save = Path(tmp) / "SaveFile.es3"
            save.write_text(json.dumps(SAMPLE_SAVE), encoding="utf-8")
            mgr = BackupManager(save)
            info = mgr.create_backup()
            self.assertTrue(info.path.exists())
            save.write_text("{}", encoding="utf-8")
            mgr.restore(info.path)
            data = json.loads(save.read_text(encoding="utf-8"))
            self.assertIn("Progression", data)
            self.assertEqual(len(mgr.list_backups()), 2)  # + auto before restore


class ValidatorTests(unittest.TestCase):
    def test_funds_ok(self) -> None:
        self.assertEqual(validate_funds("1000"), 1000.0)
        self.assertEqual(validate_funds("1 000,5"), 1000.5)

    def test_funds_too_big(self) -> None:
        with self.assertRaises(ValidationError):
            validate_funds(200_000_000)


if __name__ == "__main__":
    unittest.main()
