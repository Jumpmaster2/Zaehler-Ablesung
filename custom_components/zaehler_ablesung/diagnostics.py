"""Diagnostics: settings and the stored state of every meter."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .meter import MeterConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MeterConfigEntry
) -> dict[str, Any]:
    manager = entry.runtime_data
    return {
        "entry": entry.as_dict(),
        "meters": {
            meter.id: {
                "title": meter.title,
                "config": meter.config,
                "state": meter.state.as_dict(),
                "busy": meter.busy,
                "has_image": meter.image is not None,
            }
            for meter in manager.meters.values()
        },
    }
