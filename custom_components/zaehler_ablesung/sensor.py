"""Sensors of a meter: reading, mean rate, status, last and next reading."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_CONDITION, CONF_TYPE
from .entity import MeterEntity
from .logic.reading import STATUSES, VALID_STATUSES
from .logic.units import TYPE_DEFAULTS, TYPE_GAS, TYPE_WATER, is_energy, is_volume
from .meter import Meter, MeterConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeterConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for meter in entry.runtime_data.meters.values():
        async_add_entities(
            [
                ReadingSensor(meter),
                RateSensor(meter),
                StatusSensor(meter),
                LastCheckSensor(meter),
                NextCheckSensor(meter),
            ],
            config_subentry_id=meter.id,
        )


class ReadingSensor(MeterEntity, SensorEntity):
    """Last valid meter reading (unchanged after a rejected reading)."""

    # total instead of total_increasing: a correction downwards is not a meter reset
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "reading")
        unit = meter.unit
        self._attr_native_unit_of_measurement = unit or None
        self._attr_suggested_display_precision = meter.decimals
        meter_type = meter.opt(CONF_TYPE)
        if is_energy(unit):
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif is_volume(unit) and meter_type == TYPE_WATER:
            self._attr_device_class = SensorDeviceClass.WATER
        elif is_volume(unit) and meter_type == TYPE_GAS:
            self._attr_device_class = SensorDeviceClass.GAS
        elif is_volume(unit):
            self._attr_device_class = SensorDeviceClass.VOLUME_STORAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = TYPE_DEFAULTS[meter_type].icon if meter_type in TYPE_DEFAULTS else None

    @property
    def native_value(self) -> float | None:
        return self.meter.state.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        t = self.meter.state.value_time
        return {"last_valid_reading": t.isoformat() if t else None}


class RateSensor(MeterEntity, SensorEntity):
    """Mean power or flow since the previous valid reading."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "rate")
        unit, _ = meter.rate_unit
        self._attr_native_unit_of_measurement = unit
        if unit == "kW":
            self._attr_translation_key = "rate_power"
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_suggested_display_precision = 2
        elif unit == "L/h":
            self._attr_translation_key = "rate_flow"
            self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
            self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> float | None:
        return self.meter.state.rate


class StatusSensor(MeterEntity, SensorEntity):
    """Result of the last reading."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "status")

    @property
    def native_value(self) -> str | None:
        return self.meter.state.status

    @property
    def icon(self) -> str:
        if self.meter.busy:
            return "mdi:camera-iris"
        if self.native_value in VALID_STATUSES:
            return "mdi:check-circle-outline"
        return "mdi:alert-circle-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.meter.state
        return {
            "readings": s.readings or [],
            "running": self.meter.busy,
            "image_time": self.meter.image_time.isoformat() if self.meter.image_time else None,
        }


class LastCheckSensor(MeterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "last_check")

    @property
    def native_value(self) -> datetime | None:
        return self.meter.state.last_check


class NextCheckSensor(MeterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "next_check")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # the interval can depend on a condition entity
        if condition := self.meter.opt(CONF_CONDITION):
            self.async_on_remove(
                async_track_state_change_event(self.hass, [condition], self._condition_changed)
            )

    @callback
    def _condition_changed(self, _event: Event[EventStateChangedData]) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        return self.meter.next_check()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"interval": self.meter.interval_minutes()}
