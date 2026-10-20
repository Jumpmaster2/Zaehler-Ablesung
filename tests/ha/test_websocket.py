"""WebSocket API of the panel."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.zaehler_ablesung.const import DOMAIN

from .conftest import setup_entry


async def _send(client, **msg):
    await client.send_json_auto_id(msg)
    return await client.receive_json()


async def test_config_payload(hass: HomeAssistant, base, hass_ws_client) -> None:
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    msg = await _send(client, type=f"{DOMAIN}/config")
    assert msg["success"], msg
    cfg = msg["result"]
    heat = next(m for m in cfg["meters"] if m["title"] == "Heat")
    assert heat["entities"]["reading"] == "sensor.heat_meter_reading"
    assert heat["entities"]["last_image"] == "camera.heat_last_picture"
    assert heat["rate_unit"] == "kW"
    assert heat["data"]["max_attempts"] == 4
    sections = {s["id"]: s["fields"] for s in cfg["meter_sections"]}
    assert sections["camera_section"]["camera"]["domain"] == ["camera"]
    assert sections["display_section"]["hints"]["multiline"] is True
    assert cfg["type_defaults"]["water"]["unit"] == "m³"
    assert cfg["option_specs"]["ai_task_entity"]["domain"] == ["ai_task"]


async def test_save_and_delete_meter(hass: HomeAssistant, base, hass_ws_client) -> None:
    entry = await setup_entry(hass, meters=[])
    client = await hass_ws_client(hass)

    msg = await _send(client, type=f"{DOMAIN}/save_meter", title=" ", data={"camera": "camera.x"})
    assert not msg["success"]
    assert msg["error"]["message"] == "name_required"
    msg = await _send(client, type=f"{DOMAIN}/save_meter", title="W", data={"meter_type": "water"})
    assert msg["error"]["message"] == "camera_required"
    msg = await _send(
        client,
        type=f"{DOMAIN}/save_meter",
        title="Water",
        data={
            "meter_type": "water",
            "camera": "camera.water_cam",
            "decimals": "2",
            "light": "",
            "unknown": 1,
        },
    )
    assert msg["success"], msg
    await hass.async_block_till_done()
    sub_id = msg["result"]["subentry_id"]
    data = entry.subentries[sub_id].data
    assert data["unit"] == "m³"
    assert data["decimals"] == 2
    assert "light" not in data
    assert "unknown" not in data
    assert hass.states.get("sensor.water_meter_reading")

    msg = await _send(
        client,
        type=f"{DOMAIN}/save_meter",
        subentry_id=sub_id,
        title="Water",
        data={**data, "light_brightness": 500},
    )
    assert msg["error"]["message"] == "invalid_value:light_brightness"

    msg = await _send(client, type=f"{DOMAIN}/set_reading", subentry_id=sub_id, value=12.5)
    assert msg["success"], msg
    await hass.async_block_till_done()
    assert hass.states.get("sensor.water_meter_reading").state == "12.5"

    msg = await _send(client, type=f"{DOMAIN}/delete_meter", subentry_id=sub_id)
    assert msg["success"]
    await hass.async_block_till_done()
    assert not entry.subentries
    assert hass.states.get("sensor.water_meter_reading") is None


async def test_options_and_prompt(hass: HomeAssistant, base, hass_ws_client) -> None:
    entry = await setup_entry(hass, meters=[])
    client = await hass_ws_client(hass)
    msg = await _send(client, type=f"{DOMAIN}/save_options", options={"notify_rejected": False})
    assert msg["success"], msg
    assert entry.options["notify_rejected"] is False
    msg = await _send(client, type=f"{DOMAIN}/save_options", options={"ai_task_entity": ""})
    assert msg["error"]["message"] == "required:ai_task_entity"

    msg = await _send(
        client,
        type=f"{DOMAIN}/prompt",
        data={"meter_type": "heat", "unit": "MWh", "decimals": 3, "hints": "Frame line."},
    )
    assert "MWh" in msg["result"]["instructions"]
    assert "Frame line." in msg["result"]["instructions"]
