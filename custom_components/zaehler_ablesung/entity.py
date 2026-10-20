"""Base entity of a meter."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import CONF_TYPE, DOMAIN, NAME, SIGNAL_UPDATE
from .meter import Meter

MODELS = {
    "heat": "Heat meter",
    "water": "Water meter",
    "gas": "Gas meter",
    "electricity": "Electricity meter",
    "other": "Meter",
}


class MeterEntity(Entity):
    """Entity of one meter; updated when the meter reports a change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, meter: Meter, key: str) -> None:
        self.meter = meter
        self._attr_translation_key = key
        self._attr_unique_id = f"{meter.id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, meter.id)},
            name=meter.title,
            manufacturer=NAME,
            model=MODELS.get(meter.opt(CONF_TYPE), "Meter"),
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self.meter.id), self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
