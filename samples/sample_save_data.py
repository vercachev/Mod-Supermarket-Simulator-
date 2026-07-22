"""Сэмпл и генератор минимального сейва Supermarket Together."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.constants import ES3_PASSWORD  # noqa: E402
from utils.es3_crypto import encrypt  # noqa: E402
from save_handler import SaveHandler  # noqa: E402


def make_save_dict(
    funds: float = 1000.0,
    *,
    day: int = 1,
    store_name: str = "TestMart",
) -> dict:
    return {
        "Difficulty": {"__type": "int", "value": 0},
        "StoreName": {"__type": "string", "value": store_name},
        "Day": {"__type": "int", "value": day},
        "FranchiseExperience": {"__type": "int", "value": 100},
        "FranchisePoints": {"__type": "int", "value": 5},
        "Funds": {"__type": "float", "value": float(funds)},
        "LastAwardedLevel": {"__type": "int", "value": 1},
        "SupermarketName": {"__type": "string", "value": store_name.upper()},
    }


def make_encrypted_bytes(funds: float = 1000.0) -> bytes:
    plain = (json.dumps(make_save_dict(funds), indent=4) + "\n").encode("utf-8")
    return encrypt(plain, ES3_PASSWORD, key_size=16)


def write_samples(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "StoreFile0_sample.es3"
    path.write_bytes(make_encrypted_bytes(12345.0))
    # также plaintext для отладки
    (out_dir / "StoreFile0_sample.json").write_text(
        json.dumps(make_save_dict(12345.0), indent=4) + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    p = write_samples(Path(__file__).resolve().parent)
    h = SaveHandler()
    h.load(p)
    print("sample", p, "funds", h.get_snapshot().funds)
