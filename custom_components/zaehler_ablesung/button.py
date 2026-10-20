"""Buttons: read now and take a test picture."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import MeterEntity
from .meter import Meter, MeterConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeterConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for meter in entry.runtime_data.meters.values():
        async_add_entities([ReadButton(meter), PictureButton(meter)], config_subentry_id=meter.id)


class ReadButton(MeterEntity, ButtonEntity):
    _attr_icon = "mdi:camera-iris"

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "read_now")

    async def async_press(self) -> None:
        self.meter.manager.start_reading(self.meter)


class PictureButton(MeterEntity, ButtonEntity):
    _attr_icon = "mdi:camera"

    def __init__(self, meter: Meter) -> None:
        super().__init__(meter, "test_picture")

    async def async_press(self) -> None:
        self.meter.manager.start_picture(self.meter)
