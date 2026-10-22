"""Config flow and meter subentry flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.zaehler_ablesung.const import DOMAIN, SUBENTRY_METER

from .conftest import setup_entry

DETAILS = {
    "camera_section": {
        "camera": "camera.water_cam",
        "light_brightness": 40,
        "warmup": 3,
        "discard_frames": 2,
    },
    "image_section": {
        "crop_left": 0,
        "crop_top": 40,
        "crop_right": 100,
        "crop_bottom": 100,
        "rotate": -3.5,
        "exposure": 80,
    },
    "display_section": {"unit": "m³", "decimals": 3, "hints": "  "},
    "schedule_section": {"interval": 60, "interval_off": 360},
    "checks_section": {
        "max_rate": 3,
        "max_correction": 0.05,
        "max_attempts": 4,
        "confirmations": 2,
    },
    "notify_section": {
        "notify_smaller": 3,
        "notify_too_large": 1,
        "notify_corrected": 0,
        "notify_failed": 5.0,
    },
}


async def test_user_flow(hass: HomeAssistant, base) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"ai_task_entity": "ai_task.claude", "notify_rejected": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {"ai_task_entity": "ai_task.claude", "notify_rejected": False}
    # only once
    again = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert again["type"] is FlowResultType.ABORT


async def test_meter_subentry(hass: HomeAssistant, base) -> None:
    entry = await setup_entry(hass, meters=[])
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_METER), context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Water", "meter_type": "water"}
    )
    assert result["step_id"] == "details"
    # the type set its defaults
    schema = result["data_schema"].schema
    display = next(v for k, v in schema.items() if str(k) == "display_section").schema.schema
    unit = next(k for k in display if str(k) == "unit")
    assert unit.default() == "m³"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], DETAILS)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    sub = next(iter(entry.subentries.values()))
    assert sub.title == "Water"
    assert sub.data["meter_type"] == "water"
    assert sub.data["light_brightness"] == 40
    assert "hints" not in sub.data
    assert sub.data["crop_top"] == 40
    assert sub.data["rotate"] == -3.5
    assert sub.data["exposure"] == 80
    assert sub.data["notify_smaller"] == 3
    assert sub.data["notify_corrected"] == 0
    # whole numbers are stored as int
    assert sub.data["notify_failed"] == 5
    assert isinstance(sub.data["notify_failed"], int)
    assert hass.states.get("sensor.water_meter_reading")

    # reconfigure: rename and change the decimals
    result = await entry.start_subentry_reconfigure_flow(hass, sub.subentry_id)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            **DETAILS,
            "name": "Cold water",
            "meter_type": "water",
            "display_section": {"unit": "m³", "decimals": 2},
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[sub.subentry_id].title == "Cold water"
    assert entry.subentries[sub.subentry_id].data["decimals"] == 2


async def test_options_flow(hass: HomeAssistant, base) -> None:
    entry = await setup_entry(hass, meters=[])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"ai_task_entity": "ai_task.other", "notify_rejected": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["ai_task_entity"] == "ai_task.other"
