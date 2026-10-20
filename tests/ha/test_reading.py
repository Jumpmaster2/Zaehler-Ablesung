"""Reading a meter: pictures, majority vote, plausibility, rate, schedule."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zaehler_ablesung.const import DOMAIN, EVENT_READING

from .conftest import HEAT_METER, setup_entry

READING = "sensor.heat_meter_reading"
POWER = "sensor.heat_mean_power"
STATUS = "sensor.heat_status"


def _meter(entry, title="Heat"):
    return next(m for m in entry.runtime_data.meters.values() if m.title == title)


def _manual(entry, title="Heat"):
    """No automatic readings (moving the clock would start them)."""
    for meter in entry.runtime_data.meters.values():
        meter.set_automatic(False)
    return _meter(entry, title)


async def test_entities(hass: HomeAssistant, base) -> None:
    await setup_entry(hass)
    for entity_id in (
        READING,
        POWER,
        STATUS,
        "sensor.heat_last_reading",
        "sensor.heat_next_reading",
        "camera.heat_last_picture",
        "button.heat_read_now",
        "button.heat_test_picture",
        "switch.heat_automatic",
        "sensor.water_meter_reading",
        "sensor.water_mean_flow",
    ):
        assert hass.states.get(entity_id), entity_id
    reading = hass.states.get(READING)
    assert reading.attributes["unit_of_measurement"] == "MWh"
    assert reading.attributes["device_class"] == "energy"
    assert reading.attributes["state_class"] == "total"
    water = hass.states.get("sensor.water_meter_reading")
    assert water.attributes["device_class"] == "water"
    assert hass.states.get("sensor.water_mean_flow").attributes["unit_of_measurement"] == "L/h"
    # entities belong to the meter subentry
    entity = er.async_get(hass).async_get(READING)
    assert entity.config_subentry_id in hass.config_entries.async_entries(DOMAIN)[0].subentries


async def test_first_reading(hass: HomeAssistant, base, ai, lights, cam) -> None:
    entry = await setup_entry(hass)
    events = []
    hass.bus.async_listen(EVENT_READING, events.append)
    ai.answers = ["1.261", "1,261"]
    status = await _meter(entry).async_read()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert status == "ok"
    assert hass.states.get(READING).state == "1.261"
    assert hass.states.get(STATUS).state == "ok"
    assert hass.states.get(STATUS).attributes["readings"] == ["1.261", "1.261"]
    # 2 pictures: each with 2 discarded pictures, light on with brightness, then off
    assert cam == ["camera.heat_cam"] * 6
    assert lights[0] == ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 60})
    assert lights[1] == ("off", {"entity_id": "light.heat_cam_led"})
    assert len(lights) == 4
    call = ai.calls[0]
    assert call["entity_id"] == "ai_task.claude"
    assert "Line above the digits is the frame." in call["instructions"]
    assert call["attachments"][0]["media_content_id"].endswith(
        f"/zaehler_ablesung/{_meter(entry).id}/letztes.jpg"
    )
    assert events[0].data["valid"] is True
    assert events[0].data["value"] == 1.261
    assert _meter(entry).image == b"jpeg-camera.heat_cam-6"
    # the picture is stored in the media folder
    path = _meter(entry).folder / "letztes.jpg"
    assert await hass.async_add_executor_job(path.read_bytes) == b"jpeg-camera.heat_cam-6"


async def test_rate_and_plausibility(hass: HomeAssistant, base, ai, freezer) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    ai.answers = ["1.261", "1.261"]
    await meter.async_read()
    freezer.tick(timedelta(hours=2))
    ai.answers = ["1.273", "1.273"]
    assert await meter.async_read() == "ok"
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(POWER).state == "6.0"

    # +0.2 MWh in 1 h is more than 0.05 MWh/h: rejected, value and rate stay
    freezer.tick(timedelta(hours=1))
    ai.answers = ["1.473", "1.473"]
    assert await meter.async_read() == "too_large"
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(READING).state == "1.273"
    assert hass.states.get(POWER).state == "6.0"
    rejected = meter.folder / "verworfen"
    files = await hass.async_add_executor_job(lambda: list(rejected.glob("*.jpg")))
    assert len(files) == 1


async def test_majority_vote(hass: HomeAssistant, base, ai) -> None:
    entry = await setup_entry(hass)
    meter = _meter(entry)
    ai.answers = ["1.267", "1.261", "unlesbar", "1.261"]
    assert await meter.async_read() == "ok"
    assert meter.state.value == 1.261
    assert meter.state.readings == ["1.267", "1.261", "unreadable", "1.261"]

    # never twice the same value: unreadable after 4 pictures
    ai.answers = ["1.27", "1.28", "unlesbar", "1.29", "1.27"]
    assert await meter.async_read() == "unreadable"
    assert len(meter.state.readings) == 4
    assert meter.state.value == 1.261


async def test_correction(hass: HomeAssistant, base, ai, freezer) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    ai.answers = ["1.267", "1.267"]
    await meter.async_read()
    freezer.tick(timedelta(hours=1))
    ai.answers = ["1.273", "1.273"]
    await meter.async_read()
    assert meter.state.rate == 6.0

    # smaller value, but the confirmation pictures disagree: rejected
    freezer.tick(timedelta(hours=1))
    ai.answers = ["1.261", "1.261", "1.261", "1.267"]
    assert await meter.async_read() == "smaller"
    assert meter.state.value == 1.273

    # smaller value confirmed by 2 more pictures: corrected, rate reset
    ai.answers = ["1.261", "1.261", "1.261", "1.261"]
    assert await meter.async_read() == "corrected"
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(READING).state == "1.261"
    assert hass.states.get(POWER).state == "unknown"

    # far below the allowed correction: no confirmation pictures
    ai.answers = ["1.0", "1.0"]
    assert await meter.async_read() == "smaller"
    assert len(meter.state.readings) == 2


async def test_errors(hass: HomeAssistant, base, ai) -> None:
    entry = await setup_entry(hass)
    meter = _meter(entry)
    ai.answers = ["RAISE"] * 4
    assert await meter.async_read() == "error"
    assert meter.state.value is None


async def test_schedule_and_condition(hass: HomeAssistant, base, ai, freezer) -> None:
    entry = await setup_entry(hass)
    heat = _meter(entry)
    water = _meter(entry, "Water")
    water.set_automatic(False)
    ai.answers = ["1.261", "1.261"]
    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert heat.state.value == 1.261
    assert water.state.last_check is None

    # heating day: every 30 min
    assert heat.interval_minutes() == 30
    assert not heat.is_due(heat.state.last_check + timedelta(minutes=25))
    assert heat.is_due(heat.state.last_check + timedelta(minutes=28))
    # no heating day: 360 min
    hass.states.async_set("binary_sensor.heating_day", "off")
    await hass.async_block_till_done(wait_background_tasks=True)
    assert heat.interval_minutes() == 360
    state = hass.states.get("sensor.heat_next_reading").state
    expected = heat.state.last_check + timedelta(minutes=360)
    assert dt_util.parse_datetime(state) == expected.replace(microsecond=0)

    # automatic off: no next reading
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.heat_automatic"}, blocking=True
    )
    assert hass.states.get("sensor.heat_next_reading").state == "unknown"
    assert not heat.is_due(heat.state.last_check + timedelta(days=1))


async def test_buttons(hass: HomeAssistant, base, ai, cam) -> None:
    entry = await setup_entry(hass)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.heat_test_picture"}, blocking=True
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(cam) == 3
    assert ai.calls == []
    assert _meter(entry).state.last_check is None

    ai.answers = ["1.261", "1.261"]
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.heat_read_now"}, blocking=True
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(READING).state == "1.261"


async def test_services_and_restart(hass: HomeAssistant, base, ai) -> None:
    entry = await setup_entry(hass)
    await hass.services.async_call(
        DOMAIN, "set_reading", {"entity_id": READING, "value": 1.5}, blocking=True
    )
    assert hass.states.get(READING).state == "1.5"
    assert hass.states.get(STATUS).state == "manual"

    ai.answers = ["1.501", "1.501"]
    await hass.services.async_call(
        DOMAIN, "read", {"entity_id": ["switch.heat_automatic"]}, blocking=True
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(READING).state == "1.501"

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(READING).state == "1.501"
    assert _meter(entry).image is not None


async def test_crop(hass: HomeAssistant, base, ai, hass_ws_client) -> None:
    import base64
    import io
    from unittest.mock import patch

    from homeassistant.components.camera import Image as CamImage
    from PIL import Image

    out = io.BytesIO()
    Image.new("RGB", (1000, 800), (0, 0, 0)).save(out, format="JPEG")
    jpeg = out.getvalue()
    heat = {**HEAT_METER, "crop_left": 10, "crop_top": 50, "crop_right": 60, "crop_bottom": 100}
    entry = await setup_entry(hass, meters=[("Heat", heat)])
    meter = _meter(entry)

    async def get_image(hass, entity_id, timeout=10, width=None, height=None):
        return CamImage("image/jpeg", jpeg)

    with patch(
        "custom_components.zaehler_ablesung.meter.camera.async_get_image", side_effect=get_image
    ):
        assert await meter.async_picture_only()
    # the AI and the camera entity get the crop, the original is kept for the panel
    assert Image.open(io.BytesIO(meter.image)).size == (500, 400)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/original", "subentry_id": meter.id})
    msg = await client.receive_json()
    assert base64.b64decode(msg["result"]["image"]) == jpeg
