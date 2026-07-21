"""Сэмпл и генератор минимального Cookie Clicker сейва."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from save_handler import SaveHandler, _js_escape, utf8_to_b64  # noqa: E402


def make_plain_save(cookies: float = 1000.0) -> str:
    version = "2.052"
    empty = ""
    run = "1700000000000;1700000000000;1700000000000;TestBakery;abcde"
    prefs = "1" * 20
    misc = f"{int(cookies)};{int(cookies)};0;0;0;0;0;0;0;0;0;0;0;-1;0;0;0;0;0;0;0;-1;0;;0;0;0;0;0;0;0"
    return "|".join(
        [version, empty, run, prefs, misc, "", "", "", "", ""]
    )


def make_export_string(cookies: float = 1000.0, escaped: bool = True) -> str:
    plain = make_plain_save(cookies)
    raw = utf8_to_b64(plain) + "!END!"
    return _js_escape(raw) if escaped else raw


def write_samples(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "cookie_clicker_sample.txt"
    path.write_text(make_export_string(12345), encoding="utf-8")
    return path


if __name__ == "__main__":
    p = write_samples(Path(__file__).resolve().parent)
    h = SaveHandler()
    h.load(p)
    print("sample", p, "cookies", h.get_snapshot().cookies)
