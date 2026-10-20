"""Zähler-Ablesung: read meters with a camera and an AI task."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, STORAGE_VERSION, SUBENTRY_METER
from .meter import MeterConfigEntry, MeterManager
from .panel import async_register_panel, async_unregister_panel
from .services import async_setup_services
from .websocket import async_register_websocket

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services and the panel commands once."""
    async_setup_services(hass)
    async_register_websocket(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MeterConfigEntry) -> bool:
    manager = MeterManager(hass, entry)
    await manager.async_setup()
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await async_register_panel(hass, entry.entry_id)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: MeterConfigEntry) -> None:
    """Options or meters changed: remove the pictures of deleted meters, then reload."""
    manager = entry.runtime_data
    current = {k for k, s in entry.subentries.items() if s.subentry_type == SUBENTRY_METER}
    for meter_id in set(manager.meters) - current:
        await manager.async_remove_meter_files(meter_id)
    hass.config_entries.async_schedule_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: MeterConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_unload()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the stored readings and the panel (the pictures stay in the media folder)."""
    async_unregister_panel(hass)
    await Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()
