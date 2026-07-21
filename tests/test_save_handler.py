"""Тесты Bitburner SaveHandler."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from samples.sample_save_data import write_samples  # noqa: E402
from save_handler import SaveHandler  # noqa: E402
from utils.backup import BackupManager  # noqa: E402
from utils.constants import EXPLOIT_EDIT_SAVE  # noqa: E402
from utils.validator import ValidationError, validate_money  # noqa: E402


class BitburnerSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.b64_path, self.gz_path = write_samples(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_load_base64(self) -> None:
        h = SaveHandler()
        h.load(self.b64_path)
        snap = h.get_snapshot()
        self.assertEqual(snap.money, 150000.0)
        self.assertEqual(snap.skills["hacking"], 42)
        self.assertEqual(snap.bit_node, 1)
        self.assertEqual(h.meta.format_kind, "base64")
        self.assertEqual(h.meta.game_version, "2.6.1")

    def test_load_gzip(self) -> None:
        h = SaveHandler()
        h.load(self.gz_path)
        self.assertEqual(h.get_snapshot().money, 150000.0)
        self.assertEqual(h.meta.format_kind, "gzip")

    def test_edit_and_roundtrip_gzip(self) -> None:
        h = SaveHandler()
        h.load(self.gz_path)
        h.set_money(9e15)
        h.set_all_skills(1000)
        h.add_edit_exploit()
        h.save()

        h2 = SaveHandler()
        h2.load(self.gz_path)
        snap = h2.get_snapshot()
        self.assertEqual(snap.money, 9e15)
        self.assertEqual(snap.skills["hacking"], 1000)
        self.assertIn(EXPLOIT_EDIT_SAVE, snap.exploits)

    def test_player_save_stays_string(self) -> None:
        h = SaveHandler()
        h.load(self.b64_path)
        h.set_money(123)
        h.save()
        # Перечитываем сырой decoded JSON через повторную загрузку
        h2 = SaveHandler()
        h2.load(self.b64_path)
        data = h2.unwrap(h2.root)
        self.assertIsInstance(data["PlayerSave"], str)
        player = json.loads(data["PlayerSave"])
        self.assertEqual(h2.unwrap(player)["money"], 123)

    def test_corrupt(self) -> None:
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_bytes(b"not-a-save")
        with self.assertRaises(ValueError):
            SaveHandler().load(bad)


class BackupTests(unittest.TestCase):
    def test_backup_json_gz(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _b64, gz = write_samples(Path(tmp))
            mgr = BackupManager(gz)
            info = mgr.create_backup()
            self.assertTrue(info.path.name.endswith(".json.gz"))
            self.assertTrue(info.path.exists())
            self.assertEqual(len(mgr.list_backups()), 1)


class ValidatorTests(unittest.TestCase):
    def test_money_sci(self) -> None:
        self.assertEqual(validate_money("1e6"), 1_000_000.0)

    def test_money_bad(self) -> None:
        with self.assertRaises(ValidationError):
            validate_money(-1)


if __name__ == "__main__":
    unittest.main()
