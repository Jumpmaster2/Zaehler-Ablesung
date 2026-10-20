"""Service actions: read a meter now, set a meter reading by hand."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .meter import Meter

SERVICE_READ = "read"
SERVICE_SET_READING = "set_reading"
ATTR_VALUE = "value"

READ_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})
SET_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_ids, vol.Required(ATTR_VALUE): vol.Coerce(float)}
)


def meters_for(hass: HomeAssistant, entity_ids: list[str]) -> list[Meter]:
    """Meters of the given entities of this integration."""
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if not entries:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
    manager = entries[0].runtime_data
    registry = er.async_get(hass)
    meters: list[Meter] = []
    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        meter = (
            manager.meters.get(entry.config_subentry_id)
            if entry and entry.platform == DOMAIN
            else None
        )
        if meter is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_meter",
                translation_placeholders={"entity_id": entity_id},
            )
        if meter not in meters:
            meters.append(meter)
    return meters


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    async def read(call: ServiceCall) -> None:
        for meter in meters_for(hass, call.data[ATTR_ENTITY_ID]):
            meter.manager.start_reading(meter)

    async def set_reading(call: ServiceCall) -> None:
        if call.data[ATTR_VALUE] < 0:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="negative")
        for meter in meters_for(hass, call.data[ATTR_ENTITY_ID]):
            meter.set_reading(call.data[ATTR_VALUE])

    hass.services.async_register(DOMAIN, SERVICE_READ, read, schema=READ_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_READING, set_reading, schema=SET_SCHEMA)
