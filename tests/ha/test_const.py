"""Stored meter data of older versions."""

from __future__ import annotations

from custom_components.zaehler_ablesung.const import meter_values


def test_meter_values_converts_old_rotation() -> None:
    # older versions cropped first and turned the cropped picture by a right angle
    old = {
        "meter_type": "water",
        "crop_left": 10,
        "crop_top": 20,
        "crop_right": 70,
        "crop_bottom": 90,
        "rotate": "90",
    }
    values = meter_values(old)
    assert values["rotate"] == 90
    assert (
        values["crop_left"],
        values["crop_top"],
        values["crop_right"],
        values["crop_bottom"],
    ) == (10, 10, 80, 70)
    assert values["exposure"] == 100
    # new data stays as it is
    new = {**old, "rotate": -3.5}
    values = meter_values(new)
    assert values["rotate"] == -3.5
    assert values["crop_left"] == 10 and values["crop_bottom"] == 90
