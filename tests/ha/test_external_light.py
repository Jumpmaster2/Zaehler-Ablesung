"""External light (light or switch entity) around the pictures of a run."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .conftest import HEAT_METER, setup_entry

LAMP = "light.meter_lamp"
SWITCH = "switch.meter_lamp"


def _switches(hass: HomeAssistant, calls: list[tuple[str, dict]]) -> None:
    """switch.turn_on/off recorded with the light calls; after the setup, which loads the
    switch integration (its services would replace these)."""

    async def turn_on(call: ServiceCall) -> None:
        calls.append(("switch_on", dict(call.data)))

    async def turn_off(call: ServiceCall) -> None:
        calls.append(("switch_off", dict(call.data)))

    hass.services.async_register("switch", "turn_on", turn_on)
    hass.services.async_register("switch", "turn_off", turn_off)


async def _meter(hass: HomeAssistant, **external):
    entry = await setup_entry(hass, meters=[("Heat", {**HEAT_METER, **external})])
    meter = next(iter(entry.runtime_data.meters.values()))
    meter.set_automatic(False)
    return meter


def _external(calls: list[tuple[str, dict]], entity_id: str) -> list[tuple[str, dict]]:
    return [call for call in calls if call[1]["entity_id"] == entity_id]


CAM_ON = ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 60})
CAM_OFF = ("off", {"entity_id": "light.heat_cam_led"})


async def test_without_external_light(hass: HomeAssistant, base, ai, lights) -> None:
    meter = await _meter(hass)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    # exactly as before: only the light of the camera
    assert lights == [CAM_ON, CAM_OFF]


async def test_only_while_taking_pictures(hass: HomeAssistant, base, ai, lights, caplog) -> None:
    hass.states.async_set(LAMP, "off")
    meter = await _meter(
        hass,
        external_light=LAMP,
        external_light_brightness=80,
        external_light_lead_time=2.5,
    )
    real_sleep = asyncio.sleep

    async def sleep(delay, *args, **kwargs):
        if delay == 2.5:
            lights.append(("wait", {"entity_id": LAMP, "seconds": delay}))
        await real_sleep(0)

    ai.answers = ["1.261"] * 4
    with patch("custom_components.zaehler_ablesung.meter.asyncio.sleep", side_effect=sleep):
        assert await meter.async_read() == "ok"
    # on with its brightness, lead time, then the camera light and the pictures, then off
    assert lights == [
        ("on", {"entity_id": LAMP, "brightness_pct": 80}),
        ("wait", {"entity_id": LAMP, "seconds": 2.5}),
        CAM_ON,
        CAM_OFF,
        ("off", {"entity_id": LAMP}),
    ]
    assert "external light" not in caplog.text


async def test_switch_without_brightness(hass: HomeAssistant, base, ai, lights) -> None:
    hass.states.async_set(SWITCH, "off")
    meter = await _meter(hass, external_light=SWITCH, external_light_lead_time=0)
    _switches(hass, lights)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    assert _external(lights, SWITCH) == [
        ("switch_on", {"entity_id": SWITCH}),
        ("switch_off", {"entity_id": SWITCH}),
    ]


async def test_stays_on_when_set(hass: HomeAssistant, base, ai, lights) -> None:
    hass.states.async_set(LAMP, "off")
    meter = await _meter(
        hass, external_light=LAMP, external_light_lead_time=0, external_light_turn_off=False
    )
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    assert _external(lights, LAMP) == [("on", {"entity_id": LAMP, "brightness_pct": 100})]


async def test_permanent(hass: HomeAssistant, base, ai, lights) -> None:
    hass.states.async_set(LAMP, "off")
    meter = await _meter(
        hass, external_light=LAMP, external_light_mode="permanent", external_light_lead_time=0
    )
    # off: switched on, and left on (switching off afterwards is only for the other mode)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    assert _external(lights, LAMP) == [("on", {"entity_id": LAMP, "brightness_pct": 100})]

    # already on: left alone
    lights.clear()
    hass.states.async_set(LAMP, "on")
    ai.answers = ["1.261"] * 2
    assert await meter.async_read() == "ok"
    assert _external(lights, LAMP) == []
    assert lights == [CAM_ON, CAM_OFF]


@pytest.mark.parametrize("state", ["unavailable", None])
async def test_not_available(hass: HomeAssistant, base, ai, lights, caplog, state) -> None:
    if state:
        hass.states.async_set(LAMP, state)
    meter = await _meter(hass, external_light=LAMP, external_light_lead_time=30)
    ai.answers = ["1.261"] * 4
    # read without it, and without waiting for it
    async with asyncio.timeout(5):
        assert await meter.async_read() == "ok"
    assert _external(lights, LAMP) == []
    assert "external light light.meter_lamp is not available" in caplog.text


async def test_service_fails(hass: HomeAssistant, base, ai, lights, caplog) -> None:
    hass.states.async_set(SWITCH, "off")
    calls = []

    async def broken(call: ServiceCall) -> None:
        calls.append(call.service)
        raise HomeAssistantError("Pi not reachable")

    meter = await _meter(hass, external_light=SWITCH, external_light_lead_time=30)
    hass.services.async_register("switch", "turn_on", broken)
    hass.services.async_register("switch", "turn_off", broken)
    ai.answers = ["1.261"] * 4
    async with asyncio.timeout(5):
        assert await meter.async_read() == "ok"
    # no lead time after a failed switch-on; still tried to switch it off
    assert calls == ["turn_on", "turn_off"]
    assert "could not switch the external light switch.meter_lamp on" in caplog.text
    assert "could not switch the external light switch.meter_lamp off" in caplog.text
    assert lights == [CAM_ON, CAM_OFF]


async def test_service_missing(hass: HomeAssistant, base, ai, caplog) -> None:
    # the entity has a state, but there is no light service (e.g. light not loaded)
    hass.states.async_set(LAMP, "off")
    meter = await _meter(hass, external_light=LAMP, external_light_lead_time=0)
    hass.services.async_remove("light", "turn_on")
    hass.services.async_remove("light", "turn_off")
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    assert "could not switch the external light light.meter_lamp on" in caplog.text
    assert "could not switch the external light light.meter_lamp off" in caplog.text


async def test_off_after_failed_reading(hass: HomeAssistant, base, ai, lights) -> None:
    hass.states.async_set(LAMP, "off")
    meter = await _meter(hass, external_light=LAMP, external_light_lead_time=0)
    # the AI fails: the reading ends with an error, the light goes off
    ai.answers = ["RAISE"] * 4
    assert await meter.async_read() == "error"
    assert _external(lights, LAMP)[-1] == ("off", {"entity_id": LAMP})

    # an unexpected error while taking the pictures: the light still goes off
    lights.clear()
    with (
        patch.object(meter, "async_take_picture", side_effect=RuntimeError("camera broke")),
        pytest.raises(RuntimeError),
    ):
        await meter.async_read()
    assert _external(lights, LAMP) == [
        ("on", {"entity_id": LAMP, "brightness_pct": 100}),
        ("off", {"entity_id": LAMP}),
    ]
    assert meter.busy is None


async def test_test_picture(hass: HomeAssistant, base, lights, cam) -> None:
    hass.states.async_set(LAMP, "off")
    meter = await _meter(hass, external_light=LAMP, external_light_lead_time=0)
    assert await meter.async_picture_only()
    assert _external(lights, LAMP) == [
        ("on", {"entity_id": LAMP, "brightness_pct": 100}),
        ("off", {"entity_id": LAMP}),
    ]
