"""WebSocket API for the panel: read the configuration, change options and meters."""

from __future__ import annotations

import base64
from functools import cache
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import Selector

from .config_flow import _main_schema, clean_meter, meter_sections, validate_meter
from .const import (
    CONF_HINTS,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT,
    DEFAULTS,
    DOMAIN,
    METER_SECTIONS,
    SUBENTRY_METER,
    meter_defaults,
    meter_values,
)
from .logic.prompt import build_instructions, default_hints
from .logic.units import METER_TYPES, rate_unit

DATA_WS = f"{DOMAIN}_ws_registered"

# entity keys of a meter (unique id suffix) for the panel
METER_ENTITY_KEYS = {
    "reading": "sensor",
    "rate": "sensor",
    "status": "sensor",
    "last_check": "sensor",
    "next_check": "sensor",
    "last_image": "camera",
    "read_now": "button",
    "test_picture": "button",
    "automatic": "switch",
}


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_WS):
        return
    hass.data[DATA_WS] = True
    for command in (
        ws_original,
        ws_config,
        ws_save_options,
        ws_save_meter,
        ws_delete_meter,
        ws_set_reading,
        ws_prompt,
    ):
        websocket_api.async_register_command(hass, command)


def _entry(hass: HomeAssistant) -> ConfigEntry | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry
    entries = hass.config_entries.async_entries(DOMAIN)
    return entries[0] if entries else None


def _fields(schema: vol.Schema) -> dict[str, Selector]:
    return {str(marker): value for marker, value in schema.schema.items()}


@cache
def option_fields() -> dict[str, Selector]:
    return _fields(_main_schema({}))


@cache
def meter_fields() -> dict[str, dict[str, Selector]]:
    """Selectors of the meter dialog per section."""
    return {key: _fields(schema) for key, schema in meter_sections({}).items()}


def _flat_meter_fields() -> dict[str, Selector]:
    fields: dict[str, Selector] = {}
    for section_fields in meter_fields().values():
        fields.update(section_fields)
    return fields


def _spec(selector: Selector) -> dict[str, Any]:
    kind, config = next(iter(selector.serialize()["selector"].items()))
    return {"selector": kind, **dict(config)}


class PanelError(Exception):
    """Error key for the panel, optionally with the field it belongs to."""

    def __init__(self, code: str, field: str | None = None) -> None:
        super().__init__(f"{code}:{field}" if field else code)


def _coerce(selector: Selector, value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
    if value is None or value == "":
        return None
    return selector(value)


def apply_options(current: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    fields = option_fields()
    options = dict(current)
    for key, value in changes.items():
        if key not in fields:
            raise PanelError("unknown_option", key)
        try:
            coerced = _coerce(fields[key], value)
        except (vol.Invalid, TypeError, ValueError) as err:
            raise PanelError("invalid_value", key) from err
        if coerced is None:
            raise PanelError("required", key)
        options[key] = coerced
    return options


def meter_data(title: str, data: dict[str, Any]) -> dict[str, Any]:
    """Validated data of a meter (without the name); raises PanelError."""
    fields = _flat_meter_fields()
    values: dict[str, Any] = {}
    meter_type = data.get(CONF_TYPE, "heat")
    if meter_type not in METER_TYPES:
        raise PanelError("invalid_value", CONF_TYPE)
    for key, value in data.items():
        if key not in fields:
            continue
        try:
            coerced = _coerce(fields[key], value)
        except (vol.Invalid, TypeError, ValueError) as err:
            raise PanelError("invalid_value", key) from err
        if coerced is not None:
            values[key] = coerced
    values = clean_meter({CONF_NAME: title.strip(), CONF_TYPE: meter_type, **values})
    errors = validate_meter(values)
    if error := errors.get(CONF_NAME):
        raise PanelError(error)
    if error := errors.get("base"):
        raise PanelError(error)
    values.pop(CONF_NAME)
    return {
        **{k: v for k, v in meter_defaults(meter_type).items() if k in fields or k == CONF_TYPE},
        **values,
    }


def config_payload(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    registry = er.async_get(hass)
    manager = getattr(entry, "runtime_data", None)
    meters = []
    for sub_id, sub in entry.subentries.items():
        if sub.subentry_type != SUBENTRY_METER:
            continue
        entities = {
            key: entity_id
            for key, domain in METER_ENTITY_KEYS.items()
            if (entity_id := registry.async_get_entity_id(domain, DOMAIN, f"{sub_id}_{key}"))
        }
        meter = manager.meters.get(sub_id) if manager else None
        data = meter_values(sub.data)
        meters.append(
            {
                "id": sub_id,
                "title": sub.title,
                "data": data,
                "entities": entities,
                "rate_unit": rate_unit(str(data.get(CONF_UNIT) or ""))[0],
                "busy": meter.busy if meter else None,
            }
        )
    language = hass.config.language
    return {
        "entry_id": entry.entry_id,
        "options": {**DEFAULTS, **entry.options},
        "meters": meters,
        "option_specs": {key: _spec(sel) for key, sel in option_fields().items()},
        "meter_sections": [
            {"id": sec, "fields": {k: _spec(s) for k, s in meter_fields()[sec].items()}}
            for sec in METER_SECTIONS
        ],
        "meter_types": METER_TYPES,
        "type_defaults": {
            t: {**meter_defaults(t), CONF_HINTS: default_hints(t, language)} for t in METER_TYPES
        },
    }


def _not_set_up(connection: websocket_api.ActiveConnection, msg_id: int) -> None:
    connection.send_error(msg_id, "not_found", "Zähler-Ablesung is not set up")


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/config"})
@websocket_api.require_admin
@callback
def ws_config(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg["id"])
        return
    connection.send_result(msg["id"], config_payload(hass, entry))


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/save_options", vol.Required("options"): dict}
)
@websocket_api.require_admin
@callback
def ws_save_options(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg["id"])
        return
    try:
        options = apply_options(dict(entry.options), msg["options"])
    except PanelError as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"], config_payload(hass, entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_meter",
        vol.Optional("subentry_id"): str,
        vol.Required("title"): str,
        vol.Required("data"): dict,
    }
)
@websocket_api.require_admin
@callback
def ws_save_meter(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg["id"])
        return
    try:
        data = meter_data(msg["title"], msg["data"])
    except PanelError as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    title = msg["title"].strip()
    if sub_id := msg.get("subentry_id"):
        subentry = entry.subentries.get(sub_id)
        if subentry is None or subentry.subentry_type != SUBENTRY_METER:
            connection.send_error(msg["id"], "not_found", "meter not found")
            return
        hass.config_entries.async_update_subentry(entry, subentry, data=data, title=title)
    else:
        subentry = ConfigSubentry(
            data=MappingProxyType(data), subentry_type=SUBENTRY_METER, title=title, unique_id=None
        )
        hass.config_entries.async_add_subentry(entry, subentry)
        sub_id = subentry.subentry_id
    connection.send_result(
        msg["id"], {"subentry_id": sub_id, "config": config_payload(hass, entry)}
    )


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/delete_meter", vol.Required("subentry_id"): str}
)
@websocket_api.require_admin
@callback
def ws_delete_meter(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry = _entry(hass)
    subentry = entry.subentries.get(msg["subentry_id"]) if entry else None
    if entry is None or subentry is None or subentry.subentry_type != SUBENTRY_METER:
        connection.send_error(msg["id"], "not_found", "meter not found")
        return
    hass.config_entries.async_remove_subentry(entry, msg["subentry_id"])
    connection.send_result(msg["id"], config_payload(hass, entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_reading",
        vol.Required("subentry_id"): str,
        vol.Required("value"): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)
@websocket_api.require_admin
@callback
def ws_set_reading(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    entry = _entry(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    meter = manager.meters.get(msg["subentry_id"]) if manager else None
    if entry is None or meter is None:
        connection.send_error(msg["id"], "not_found", "meter not found")
        return
    meter.set_reading(msg["value"])
    connection.send_result(msg["id"], config_payload(hass, entry))


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/original", vol.Required("subentry_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_original(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Uncropped last picture of a meter (base64 JPEG) for choosing the crop."""
    entry = _entry(hass)
    manager = getattr(entry, "runtime_data", None) if entry else None
    meter = manager.meters.get(msg["subentry_id"]) if manager else None
    if meter is None:
        connection.send_error(msg["id"], "not_found", "meter not found")
        return
    content = await hass.async_add_executor_job(meter.load_original)
    image = base64.b64encode(content).decode() if content else None
    connection.send_result(msg["id"], {"image": image})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/prompt", vol.Required("data"): dict}
)
@websocket_api.require_admin
@callback
def ws_prompt(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Instructions the AI gets for these (unsaved) settings."""
    data = msg["data"]
    try:
        decimals = int(data.get("decimals") or 0)
    except (TypeError, ValueError):
        decimals = 0
    text = build_instructions(
        str(data.get(CONF_TYPE) or "other"),
        str(data.get(CONF_UNIT) or ""),
        decimals,
        str(data.get(CONF_HINTS) or ""),
        hass.config.language,
    )
    connection.send_result(msg["id"], {"instructions": text})
