"""Build frontend/labels.js for the panel from the translation files.

Field names and help texts come from the settings dialog and the meter
dialog, so both stay in one place. Run after changing a translation:

    python scripts/build_labels.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

COMPONENT = Path(__file__).resolve().parent.parent / "custom_components" / "zaehler_ablesung"
TARGET = COMPONENT / "frontend" / "labels.js"
LANGUAGES = ("de", "en")
HEADER = (
    "// Generated from the translation files by scripts/build_labels.py, do not edit by hand.\n"
)


def _add(fields: dict[str, list[str]], step: dict[str, Any]) -> None:
    descriptions = step.get("data_description", {})
    for key, name in step.get("data", {}).items():
        fields.setdefault(key, [name, descriptions.get(key, "")])


def labels(translation: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, list[str]] = {}
    _add(fields, translation["options"]["step"]["init"])
    meter = translation["config_subentries"]["meter"]
    _add(fields, meter["step"]["user"])
    details = meter["step"]["details"]
    for sec in details["sections"].values():
        _add(fields, sec)
    entity = translation["entity"]
    return {
        "fields": fields,
        "sections": {
            k: [v["name"], v.get("description", "")] for k, v in details["sections"].items()
        },
        "errors": meter["error"],
        "status": entity["sensor"]["status"]["state"],
        "types": translation["selector"]["meter_type"]["options"],
        "rotate": translation["selector"]["rotate"]["options"],
        "entities": {
            key: value["name"] for platform in entity.values() for key, value in platform.items()
        },
    }


def render() -> str:
    data = {}
    for language in LANGUAGES:
        path = COMPONENT / "translations" / f"{language}.json"
        data[language] = labels(json.loads(path.read_text(encoding="utf-8")))
    return f"{HEADER}export const LABELS = {json.dumps(data, ensure_ascii=False, indent=1)};\n"


def main() -> int:
    content = render()
    if "--check" in sys.argv:
        if TARGET.read_text(encoding="utf-8") != content:
            print(f"{TARGET} is out of date, run python scripts/build_labels.py")
            return 1
        return 0
    TARGET.parent.mkdir(exist_ok=True)
    TARGET.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
