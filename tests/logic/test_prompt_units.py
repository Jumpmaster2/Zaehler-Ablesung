"""Instructions for the AI and units."""

from __future__ import annotations

from logic.prompt import build_instructions, default_hints, example
from logic.units import rate_unit


def test_instructions_german() -> None:
    text = build_instructions("heat", "MWh", 3, "Die Linie oben ist der Rahmen.", "de")
    assert "Wärmezählers" in text
    assert "in MWh mit 3 Nachkommastellen" in text
    assert "Die Linie oben ist der Rahmen.\n" in text
    assert text.endswith("antworte nur: unlesbar")


def test_instructions_english_without_decimals() -> None:
    text = build_instructions("water", "m³", 0, "", "en-GB")
    assert "water meter" in text
    assert "without decimals" in text
    assert "with all decimals" not in text
    assert "\n\n" not in text
    assert text.endswith("answer only: unreadable")


def test_example_and_hints() -> None:
    assert example(0) == "1234"
    assert example(3) == "1234.567"
    assert "Rollenzählwerk" in default_hints("water", "de")
    assert default_hints("other", "en") == ""


def test_rate_units() -> None:
    assert rate_unit("MWh") == ("kW", 1000.0)
    assert rate_unit("kWh") == ("kW", 1.0)
    assert rate_unit("m³") == ("L/h", 1000.0)
    assert rate_unit("L") == ("L/h", 1.0)
    assert rate_unit("Stück") == ("Stück/h", 1.0)
