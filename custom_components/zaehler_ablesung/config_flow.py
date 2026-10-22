"""Config flow, options flow and the subentry flow for meters."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_AI_TASK,
    CONF_BRIGHTNESS,
    CONF_CAMERA,
    CONF_CONDITION,
    CONF_CONFIRMATIONS,
    CONF_CROP_BOTTOM,
    CONF_CROP_LEFT,
    CONF_CROP_RIGHT,
    CONF_CROP_TOP,
    CONF_DECIMALS,
    CONF_DISCARD,
    CONF_ENHANCE,
    CONF_EXPOSURE,
    CONF_HINTS,
    CONF_INTERVAL,
    CONF_INTERVAL_OFF,
    CONF_LIGHT,
    CONF_MAX_ATTEMPTS,
    CONF_MAX_CORRECTION,
    CONF_MAX_RATE,
    CONF_METER_AI_TASK,
    CONF_NAME,
    CONF_NOTIFY,
    CONF_NOTIFY_CORRECTED,
    CONF_NOTIFY_FAILED,
    CONF_NOTIFY_SMALLER,
    CONF_NOTIFY_TOO_LARGE,
    CONF_PROMPT,
    CONF_ROTATE,
    CONF_TYPE,
    CONF_UNIT,
    CONF_WARMUP,
    DEFAULTS,
    DOMAIN,
    METER_SECTIONS,
    NAME,
    SECTION_CAMERA,
    SECTION_CHECKS,
    SECTION_DISPLAY,
    SECTION_IMAGE,
    SECTION_NOTIFY,
    SECTION_SCHEDULE,
    SUBENTRY_METER,
    meter_defaults,
    meter_values,
)
from .logic.image import EXPOSURE_RANGE, MAX_ROTATION
from .logic.prompt import default_hints
from .logic.units import METER_TYPES, UNITS


def _number(minimum: float, maximum: float, step: float, unit: str | None = None) -> NumberSelector:
    config = NumberSelectorConfig(min=minimum, max=maximum, step=step, mode=NumberSelectorMode.BOX)
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def _entity(domains: list[str] | None = None) -> EntitySelector:
    config = EntitySelectorConfig()
    if domains:
        config["domain"] = domains
    return EntitySelector(config)


def _opt(key: str, values: dict[str, Any]) -> vol.Optional:
    """Optional field that can be cleared again."""
    return vol.Optional(key, description={"suggested_value": values.get(key)})


# ---------------------------------------------------------------- main entry


def _main_schema(v: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_AI_TASK, default=v.get(CONF_AI_TASK)): _entity(["ai_task"]),
            vol.Required(CONF_NOTIFY, default=v.get(CONF_NOTIFY, DEFAULTS[CONF_NOTIFY])): (
                BooleanSelector()
            ),
        }
    )


class ZaehlerAblesungConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up the integration once; meters are added as subentries."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ZaehlerAblesungOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_METER: MeterSubentryFlow}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={}, options=user_input)
        return self.async_show_form(step_id="user", data_schema=_main_schema({}))


class ZaehlerAblesungOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={**self.config_entry.options, **user_input})
        values = {**DEFAULTS, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_main_schema(values))


# ---------------------------------------------------------------- meter subentry


def _type_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=METER_TYPES, translation_key="meter_type", mode=SelectSelectorMode.DROPDOWN
        )
    )


def meter_start_schema(v: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=v.get(CONF_NAME, "")): TextSelector(),
            vol.Required(CONF_TYPE, default=v.get(CONF_TYPE, "heat")): _type_selector(),
        }
    )


def meter_sections(v: dict[str, Any]) -> dict[str, vol.Schema]:
    """Fields of a meter per section (also used by the panel)."""

    def req(key: str) -> vol.Required:
        return vol.Required(key, default=v.get(key))

    return {
        SECTION_CAMERA: vol.Schema(
            {
                vol.Required(CONF_CAMERA, default=v.get(CONF_CAMERA)): _entity(["camera"]),
                _opt(CONF_LIGHT, v): _entity(["light"]),
                req(CONF_BRIGHTNESS): _number(1, 100, 1, "%"),
                req(CONF_WARMUP): _number(0, 30, 0.5, "s"),
                req(CONF_DISCARD): _number(0, 5, 1),
            }
        ),
        SECTION_IMAGE: vol.Schema(
            {
                req(CONF_CROP_LEFT): _number(0, 100, 0.5, "%"),
                req(CONF_CROP_TOP): _number(0, 100, 0.5, "%"),
                req(CONF_CROP_RIGHT): _number(0, 100, 0.5, "%"),
                req(CONF_CROP_BOTTOM): _number(0, 100, 0.5, "%"),
                req(CONF_ROTATE): _number(-MAX_ROTATION, MAX_ROTATION, 0.5, "°"),
                req(CONF_EXPOSURE): _number(*EXPOSURE_RANGE, 5, "%"),
                req(CONF_ENHANCE): BooleanSelector(),
            }
        ),
        SECTION_DISPLAY: vol.Schema(
            {
                req(CONF_UNIT): SelectSelector(
                    SelectSelectorConfig(
                        options=UNITS, custom_value=True, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                req(CONF_DECIMALS): _number(0, 6, 1),
                _opt(CONF_HINTS, v): TextSelector(TextSelectorConfig(multiline=True)),
                _opt(CONF_PROMPT, v): TextSelector(TextSelectorConfig(multiline=True)),
            }
        ),
        SECTION_SCHEDULE: vol.Schema(
            {
                req(CONF_INTERVAL): _number(5, 1440, 5, "min"),
                _opt(CONF_CONDITION, v): _entity(),
                req(CONF_INTERVAL_OFF): _number(5, 1440, 5, "min"),
            }
        ),
        SECTION_CHECKS: vol.Schema(
            {
                req(CONF_MAX_RATE): _number(0, 100000, 0.001),
                req(CONF_MAX_CORRECTION): _number(0, 100000, 0.001),
                req(CONF_MAX_ATTEMPTS): _number(2, 10, 1),
                req(CONF_CONFIRMATIONS): _number(1, 5, 1),
                _opt(CONF_METER_AI_TASK, v): _entity(["ai_task"]),
            }
        ),
        SECTION_NOTIFY: vol.Schema(
            {
                req(CONF_NOTIFY_SMALLER): _number(0, 50, 1),
                req(CONF_NOTIFY_TOO_LARGE): _number(0, 50, 1),
                req(CONF_NOTIFY_CORRECTED): _number(0, 50, 1),
                req(CONF_NOTIFY_FAILED): _number(0, 50, 1),
            }
        ),
    }


COLLAPSED = {SECTION_IMAGE, SECTION_CHECKS, SECTION_NOTIFY}


def meter_schema(v: dict[str, Any], with_name: bool) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if with_name:
        fields.update(meter_start_schema(v).schema)
    for key, schema in meter_sections(v).items():
        fields[vol.Required(key)] = section(schema, {"collapsed": key in COLLAPSED})
    return vol.Schema(fields)


INT_KEYS = (
    CONF_BRIGHTNESS,
    CONF_DISCARD,
    CONF_DECIMALS,
    CONF_MAX_ATTEMPTS,
    CONF_CONFIRMATIONS,
    CONF_NOTIFY_SMALLER,
    CONF_NOTIFY_TOO_LARGE,
    CONF_NOTIFY_CORRECTED,
    CONF_NOTIFY_FAILED,
)


def clean_meter(data: dict[str, Any]) -> dict[str, Any]:
    """Flatten the sections, drop empty optional values, whole numbers as int."""
    flat: dict[str, Any] = {}
    for key, value in data.items():
        if key in METER_SECTIONS and isinstance(value, dict):
            flat.update(value)
        else:
            flat[key] = value
    result: dict[str, Any] = {}
    for key, value in flat.items():
        if isinstance(value, str):
            value = value.strip()
        if value is None or value == "":
            continue
        if key in INT_KEYS:
            value = int(value)
        result[key] = value
    return result


def validate_meter(data: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not data.get(CONF_NAME):
        errors[CONF_NAME] = "name_required"
    if not data.get(CONF_CAMERA):
        errors["base"] = "camera_required"
    return errors


def new_meter_values(name: str, meter_type: str, language: str | None) -> dict[str, Any]:
    values = {CONF_NAME: name, **meter_defaults(meter_type)}
    if hints := default_hints(meter_type, language):
        values[CONF_HINTS] = hints
    return values


class MeterSubentryFlow(ConfigSubentryFlow):
    """Add or change one meter."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip()
            if not name:
                errors[CONF_NAME] = "name_required"
            else:
                self._values = new_meter_values(
                    name, user_input[CONF_TYPE], self.hass.config.language
                )
                return await self.async_step_details()
        return self.async_show_form(
            step_id="user", data_schema=meter_start_schema(user_input or {}), errors=errors
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = clean_meter(
                {
                    CONF_NAME: self._values[CONF_NAME],
                    CONF_TYPE: self._values[CONF_TYPE],
                    **user_input,
                }
            )
            errors = validate_meter(data)
            if not errors:
                return self.async_create_entry(title=data.pop(CONF_NAME), data=data)
            self._values = data
        return self.async_show_form(
            step_id="details",
            data_schema=meter_schema(self._values, with_name=False),
            errors=errors,
            description_placeholders={"name": self._values[CONF_NAME]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        subentry = self._get_reconfigure_subentry()
        values = {CONF_NAME: subentry.title, **meter_values(subentry.data)}
        errors: dict[str, str] = {}
        if user_input is not None:
            data = clean_meter(user_input)
            errors = validate_meter(data)
            if not errors:
                title = data.pop(CONF_NAME)
                return self.async_update_and_abort(
                    self._get_entry(), subentry, title=title, data=data
                )
            values = data
        return self.async_show_form(
            step_id="reconfigure", data_schema=meter_schema(values, with_name=True), errors=errors
        )
