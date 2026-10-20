"""Fixtures for tests with a Home Assistant test instance."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.components.camera import Image
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zaehler_ablesung.const import (
    CONF_AI_TASK,
    CONF_NOTIFY,
    DOMAIN,
    SUBENTRY_METER,
    meter_defaults,
)

HEAT_METER = {
    **meter_defaults("heat"),
    "camera": "camera.heat_cam",
    "light": "light.heat_cam_led",
    "light_brightness": 60,
    "warmup": 0,
    "condition_entity": "binary_sensor.heating_day",
    "interval": 30,
    "interval_off": 360,
    "hints": "Line above the digits is the frame.",
}
WATER_METER = {**meter_defaults("water"), "camera": "camera.water_cam", "warmup": 0}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


@pytest.fixture(autouse=True)
def no_settle() -> Iterator[None]:
    with patch("custom_components.zaehler_ablesung.meter.SETTLE_SECONDS", 0):
        yield


class FakeAi:
    """ai_task.generate_data that answers from a list and records the calls."""

    def __init__(self) -> None:
        self.answers: list[str] = []
        self.calls: list[dict] = []

    async def handle(self, call: ServiceCall) -> dict:
        self.calls.append(dict(call.data))
        answer = self.answers.pop(0) if self.answers else "unlesbar"
        if answer == "RAISE":
            from homeassistant.exceptions import HomeAssistantError

            raise HomeAssistantError("AI down")
        return {"conversation_id": "x", "data": answer}


@pytest.fixture
def ai(hass: HomeAssistant) -> FakeAi:
    fake = FakeAi()
    hass.services.async_register(
        "ai_task", "generate_data", fake.handle, supports_response=SupportsResponse.ONLY
    )
    return fake


@pytest.fixture
def lights(hass: HomeAssistant) -> list[tuple[str, dict]]:
    calls: list[tuple[str, dict]] = []

    async def turn_on(call: ServiceCall) -> None:
        calls.append(("on", dict(call.data)))

    async def turn_off(call: ServiceCall) -> None:
        calls.append(("off", dict(call.data)))

    hass.services.async_register("light", "turn_on", turn_on)
    hass.services.async_register("light", "turn_off", turn_off)
    return calls


@pytest.fixture
def cam() -> Iterator[list[str]]:
    """Camera pictures; each call returns a new picture."""
    taken: list[str] = []

    async def get_image(hass, entity_id, timeout=10, width=None, height=None):
        taken.append(entity_id)
        return Image("image/jpeg", f"jpeg-{entity_id}-{len(taken)}".encode())

    with patch(
        "custom_components.zaehler_ablesung.meter.camera.async_get_image", side_effect=get_image
    ):
        yield taken


@pytest.fixture
def base(hass: HomeAssistant, ai, lights, cam) -> None:
    hass.states.async_set("camera.heat_cam", "idle")
    hass.states.async_set("camera.water_cam", "idle")
    hass.states.async_set("light.heat_cam_led", "off")
    hass.states.async_set("binary_sensor.heating_day", "on")
    hass.states.async_set("ai_task.claude", "unknown")


def make_entry(meters: list[tuple[str, dict]] | None = None, **options) -> MockConfigEntry:
    meters = [("Heat", HEAT_METER), ("Water", WATER_METER)] if meters is None else meters
    return MockConfigEntry(
        domain=DOMAIN,
        title="Zähler-Ablesung",
        data={},
        options={CONF_AI_TASK: "ai_task.claude", CONF_NOTIFY: True, **options},
        subentries_data=[
            ConfigSubentryData(data=data, subentry_type=SUBENTRY_METER, title=title, unique_id=None)
            for title, data in meters
        ],
    )


async def setup_entry(hass: HomeAssistant, **kwargs) -> MockConfigEntry:
    entry = make_entry(**kwargs)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
