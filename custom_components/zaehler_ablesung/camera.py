"""Last picture of a meter."""

from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import MeterEntity
from .meter import Meter, MeterConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeterConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    for meter in entry.runtime_data.meters.values():
        async_add_entities([LastImageCamera(meter)], config_subentry_id=meter.id)


class LastImageCamera(MeterEntity, Camera):
    """Shows the picture of the last reading or test picture."""

    _attr_content_type = "image/jpeg"

    def __init__(self, meter: Meter) -> None:
        MeterEntity.__init__(self, meter, "last_image")
        Camera.__init__(self)
        # the base classes set different defaults; keep the meter entity ones
        self._attr_translation_key = "last_image"
        self._attr_unique_id = f"{meter.id}_last_image"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return self.meter.image

    @callback
    def _handle_update(self) -> None:
        # a new picture: new access token so the frontend loads it again
        self.async_update_token()
        super()._handle_update()
