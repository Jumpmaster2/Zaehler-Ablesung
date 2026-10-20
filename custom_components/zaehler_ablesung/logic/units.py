"""Meter types, units and the unit of the derived rate."""

from __future__ import annotations

from dataclasses import dataclass

TYPE_HEAT = "heat"
TYPE_WATER = "water"
TYPE_GAS = "gas"
TYPE_ELECTRICITY = "electricity"
TYPE_OTHER = "other"
METER_TYPES = [TYPE_HEAT, TYPE_WATER, TYPE_GAS, TYPE_ELECTRICITY, TYPE_OTHER]

ENERGY_UNITS = {"Wh": 0.001, "kWh": 1.0, "MWh": 1000.0, "MJ": 1 / 3.6, "GJ": 1000 / 3.6}
VOLUME_UNITS = {"L": 0.001, "m³": 1.0}
UNITS = [*ENERGY_UNITS, *VOLUME_UNITS]


@dataclass(frozen=True, slots=True)
class TypeDefaults:
    unit: str
    decimals: int
    max_rate: float  # in the meter unit per hour
    max_correction: float  # in the meter unit
    interval: int  # minutes
    icon: str


TYPE_DEFAULTS: dict[str, TypeDefaults] = {
    # 50 kW continuous heat = 0.05 MWh per hour
    TYPE_HEAT: TypeDefaults("MWh", 3, 0.05, 0.05, 60, "mdi:radiator"),
    # 3 m³ per hour is far above a household's peak flow
    TYPE_WATER: TypeDefaults("m³", 3, 3.0, 0.05, 60, "mdi:water"),
    TYPE_GAS: TypeDefaults("m³", 3, 5.0, 0.05, 60, "mdi:fire"),
    TYPE_ELECTRICITY: TypeDefaults("kWh", 1, 30.0, 1.0, 60, "mdi:flash"),
    TYPE_OTHER: TypeDefaults("kWh", 2, 100.0, 1.0, 60, "mdi:counter"),
}


def rate_unit(unit: str) -> tuple[str, float]:
    """Unit of the mean rate and the factor from meter unit per hour to it."""
    if unit in ENERGY_UNITS:
        return "kW", ENERGY_UNITS[unit]
    if unit in VOLUME_UNITS:
        # litres per hour are easier to read than m³/h for household meters
        return "L/h", VOLUME_UNITS[unit] * 1000
    return f"{unit}/h" if unit else "/h", 1.0


def is_energy(unit: str) -> bool:
    return unit in ENERGY_UNITS


def is_volume(unit: str) -> bool:
    return unit in VOLUME_UNITS
