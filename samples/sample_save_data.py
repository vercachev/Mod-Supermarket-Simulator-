"""Минимальный валидный экспорт Bitburner для тестов."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

PLAYER = {
    "ctor": "PlayerObject",
    "data": {
        "money": 150000.0,
        "skills": {
            "hacking": 42,
            "strength": 10,
            "defense": 10,
            "dexterity": 10,
            "agility": 10,
            "charisma": 5,
            "intelligence": 1,
        },
        "bitNodeN": 1,
        "karma": -10.5,
        "exploits": [],
        "factions": ["CyberSec"],
        "totalPlaytime": 3_600_000,
        "augmentations": [],
        "achievements": [],
        "sourceFiles": [],
        "identifier": "test-player",
        "lastSave": 0,
    },
}

ROOT = {
    "ctor": "BitburnerSaveObject",
    "data": {
        "PlayerSave": json.dumps(PLAYER, separators=(",", ":")),
        "AllServersSave": "{}",
        "CompaniesSave": "{}",
        "FactionsSave": "{}",
        "AliasesSave": "{}",
        "GlobalAliasesSave": "{}",
        "StockMarketSave": "",
        "StaneksGiftSave": "",
        "SettingsSave": "{}",
        "VersionSave": json.dumps("2.6.1"),
        "LastExportBonus": "0",
        "GoSave": "{}",
        "DarknetSave": "{}",
        "InfiltrationsSave": "{}",
    },
}


def write_samples(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(ROOT, separators=(",", ":"))

    b64_path = out_dir / "bitburnerSave_sample_BN1x1.json"
    b64_path.write_bytes(base64.b64encode(json_text.encode("utf-8")))

    gz_path = out_dir / "bitburnerSave_sample_BN1x1.json.gz"
    gz_path.write_bytes(gzip.compress(json_text.encode("utf-8")))
    return b64_path, gz_path


if __name__ == "__main__":
    write_samples(Path(__file__).resolve().parent)
    print("samples written")
