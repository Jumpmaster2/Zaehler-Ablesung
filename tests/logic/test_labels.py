"""Translations: same keys in all languages, panel labels up to date."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "custom_components" / "zaehler_ablesung"


def _keys(data, prefix=""):
    if isinstance(data, dict):
        out = set()
        for key, value in data.items():
            out |= _keys(value, f"{prefix}{key}.")
        return out
    return {prefix}


def test_same_keys() -> None:
    strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
    for lang in ("en", "de"):
        data = json.loads((COMPONENT / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
        assert _keys(data) == _keys(strings), lang


def test_labels_up_to_date() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_labels.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout
