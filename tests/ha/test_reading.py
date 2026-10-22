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
    ai.answers = ["1.261", "1,261", "1.261 MWh", "1.261"]
    status = await _meter(entry).async_read()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert status == "ok"
    assert hass.states.get(READING).state == "1.261"
    assert hass.states.get(STATUS).state == "ok"
    # the first value has nothing to be checked against: 2 more pictures confirm it
    assert hass.states.get(STATUS).attributes["readings"] == ["1.261"] * 4
    assert hass.states.get(STATUS).attributes["read_value"] == 1.261
    # light on once with brightness, 2 discarded pictures, 4 pictures, light off
    assert cam == ["camera.heat_cam"] * 6
    assert lights == [
        ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 60}),
        ("off", {"entity_id": "light.heat_cam_led"}),
    ]
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
    ai.answers = ["1.261"] * 4
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
    assert files[0].stem.endswith("_too_large")
    pictures = await hass.async_add_executor_job(meter.load_rejected)
    assert [p["status"] for p in pictures] == ["too_large"]


async def test_majority_vote(hass: HomeAssistant, base, ai) -> None:
    entry = await setup_entry(hass)
    meter = _meter(entry)
    ai.answers = ["1.267", "1.261", "unlesbar", "1.261", "1.261", "1.261"]
    assert await meter.async_read() == "ok"
    assert meter.state.value == 1.261
    assert meter.state.readings == ["1.267", "1.261", "unreadable", "1.261", "1.261", "1.261"]

    # never twice the same value: unreadable after 4 pictures
    ai.answers = ["1.27", "1.28", "unlesbar", "1.29", "1.27"]
    assert await meter.async_read() == "unreadable"
    assert len(meter.state.readings) == 4
    assert meter.state.value == 1.261


async def test_correction(hass: HomeAssistant, base, ai, freezer) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    ai.answers = ["1.267"] * 4
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
    meter = _manual(entry)
    ai.answers = ["RAISE"] * 4
    assert await meter.async_read() == "error"
    assert meter.state.value is None
    assert meter.state.failures == 1
    # tried again after 15 min instead of the interval of 30 min
    assert meter.interval_minutes() == 15
    # reported only when it keeps failing
    assert not _notified(hass)
    for _ in range(2):
        ai.answers = ["RAISE"] * 4
        await meter.async_read()
    assert meter.state.failures == 3
    assert _notified(hass)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"
    assert meter.state.failures == 0
    assert meter.interval_minutes() == 30


async def test_notify_per_meter(hass: HomeAssistant, base, ai) -> None:
    meter_data = {**HEAT_METER, "notify_smaller": 3, "notify_failed": 0}
    entry = await setup_entry(hass, meters=[("Heat", meter_data)])
    meter = _manual(entry)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"

    # smaller twice, an unreadable one in between neither counts nor ends the run
    ai.answers = ["1.0", "1.0"]
    assert await meter.async_read() == "smaller"
    ai.answers = ["unlesbar"] * 4
    assert await meter.async_read() == "unreadable"
    ai.answers = ["1.0", "1.0"]
    assert await meter.async_read() == "smaller"
    assert meter.state.streak == 2
    assert not _notified(hass)

    # the third time in a row is reported
    ai.answers = ["1.0", "1.0"]
    assert await meter.async_read() == "smaller"
    assert _notified(hass)
    assert "3 times in a row" in _message(hass)

    # a valid reading removes the notification and starts the count again
    ai.answers = ["1.261", "1.261"]
    assert await meter.async_read() == "ok"
    assert not _notified(hass)
    assert meter.state.streak == 0
    ai.answers = ["1.0", "1.0"]
    assert await meter.async_read() == "smaller"
    assert not _notified(hass)

    # failures are never reported for this meter
    for _ in range(4):
        ai.answers = ["RAISE"] * 4
        assert await meter.async_read() == "error"
    assert meter.state.failures == 4
    assert not _notified(hass)


def _message(hass: HomeAssistant) -> str:
    from homeassistant.components import persistent_notification

    return next(
        n["message"]
        for key, n in persistent_notification._async_get_or_create_notifications(hass).items()
        if key.startswith(DOMAIN)
    )


def _notified(hass: HomeAssistant) -> bool:
    from homeassistant.components import persistent_notification

    return any(
        n.startswith(DOMAIN)
        for n in persistent_notification._async_get_or_create_notifications(hass)
    )


async def test_first_reading_unconfirmed(hass: HomeAssistant, base, ai) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    # the decimal point missed twice, then read correctly: the first value is not taken
    ai.answers = ["1261", "1261", "1.261", "1.261"]
    assert await meter.async_read() == "unreadable"
    assert meter.state.value is None
    assert meter.state.read_value == 1261


async def test_light_already_on(hass: HomeAssistant, base, ai, lights) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    hass.states.async_set("light.heat_cam_led", "on")
    ai.answers = ["1.261"] * 4
    await meter.async_read()
    # the light stays on afterwards (e.g. for the live picture in the panel)
    assert [call[0] for call in lights] == ["on"]


async def test_schedule_and_condition(hass: HomeAssistant, base, ai, freezer) -> None:
    entry = await setup_entry(hass)
    heat = _meter(entry)
    water = _meter(entry, "Water")
    water.set_automatic(False)
    ai.answers = ["1.261"] * 4
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

    ai.answers = ["1.261"] * 4
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


async def test_own_instructions(hass: HomeAssistant, base, ai) -> None:
    heat = {**HEAT_METER, "prompt": "Read the display. Answer only with the number."}
    entry = await setup_entry(hass, meters=[("Heat", heat)])
    meter = _manual(entry)
    ai.answers = ["1.261"] * 4
    await meter.async_read()
    assert ai.calls[0]["instructions"] == "Read the display. Answer only with the number."


async def test_second_picture_and_history(hass: HomeAssistant, base, ai, lights, cam) -> None:
    heat = {**HEAT_METER, "light_brightness_2": 20, "history_hint": True}
    entry = await setup_entry(hass, meters=[("Heat", heat)])
    meter = _manual(entry)
    ai.answers = ["1.261"] * 4
    assert await meter.async_read() == "ok"

    # each attempt: picture at 60 %, second picture at 20 %, light back to 60 %
    assert lights[:4] == [
        ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 60}),
        ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 20}),
        ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 60}),
        ("on", {"entity_id": "light.heat_cam_led", "brightness_pct": 20}),
    ]
    call = ai.calls[0]
    assert [a["media_content_id"].rsplit("/", 1)[1] for a in call["attachments"]] == [
        "letztes.jpg",
        "letztes_2.jpg",
    ]
    assert "two pictures" in call["instructions"]
    # no value yet: no last readings
    assert "last readings" not in call["instructions"]
    second = meter.folder / "letztes_2.jpg"
    assert await hass.async_add_executor_job(second.exists)

    ai.calls.clear()
    ai.answers = ["1.262", "1.262"]
    assert await meter.async_read() == "ok"
    assert "last readings: 1.261 MWh (" in ai.calls[0]["instructions"]
    assert [v for _, v in meter.state.history] == [1.261, 1.262]

    # only the last 3 are kept, a value set by hand starts again
    for value in ("1.263", "1.264"):
        ai.answers = [value, value]
        await meter.async_read()
    assert [v for _, v in meter.state.history] == [1.262, 1.263, 1.264]
    meter.set_reading(1.27)
    assert [v for _, v in meter.state.history] == [1.27]


async def test_no_second_picture_by_default(hass: HomeAssistant, base, ai, lights) -> None:
    entry = await setup_entry(hass)
    meter = _manual(entry)
    ai.answers = ["1.261"] * 4
    await meter.async_read()
    assert len(ai.calls[0]["attachments"]) == 1
    assert "two pictures" not in ai.calls[0]["instructions"]
    assert "last readings" not in ai.calls[0]["instructions"]
    assert len(lights) == 2
