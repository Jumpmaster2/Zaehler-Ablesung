"""Constants."""

from __future__ import annotations

import logging

from homeassistant.const import Platform

from .logic.image import rotation
from .logic.units import TYPE_DEFAULTS, TYPE_HEAT

DOMAIN = "zaehler_ablesung"
NAME = "Zähler-Ablesung"
LOGGER = logging.getLogger(__package__)

PLATFORMS = [Platform.BUTTON, Platform.CAMERA, Platform.SENSOR, Platform.SWITCH]
STORAGE_VERSION = 1
SUBENTRY_METER = "meter"

# folder below the local media folder: <media>/zaehler_ablesung/<meter id>/
MEDIA_FOLDER = DOMAIN
IMAGE_NAME = "letztes.jpg"
ORIGINAL_NAME = "original.jpg"
REJECTED_FOLDER = "verworfen"
REJECTED_KEEP = 20

# how often due readings are looked for
CHECK_EVERY_MINUTES = 5

EVENT_READING = f"{DOMAIN}_reading"
SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"

# ---------------------------------------------------------------- global options
CONF_AI_TASK = "ai_task_entity"
CONF_NOTIFY = "notify_rejected"

DEFAULTS = {
    CONF_NOTIFY: True,
}

# ---------------------------------------------------------------- meter (subentry)
CONF_NAME = "name"
CONF_TYPE = "meter_type"
CONF_CAMERA = "camera"
CONF_LIGHT = "light"
CONF_BRIGHTNESS = "light_brightness"
CONF_WARMUP = "warmup"
CONF_DISCARD = "discard_frames"
CONF_CROP_LEFT = "crop_left"
CONF_CROP_TOP = "crop_top"
CONF_CROP_RIGHT = "crop_right"
CONF_CROP_BOTTOM = "crop_bottom"
CONF_ROTATE = "rotate"
CONF_EXPOSURE = "exposure"
CONF_UNIT = "unit"
CONF_DECIMALS = "decimals"
CONF_HINTS = "hints"
CONF_INTERVAL = "interval"
CONF_CONDITION = "condition_entity"
CONF_INTERVAL_OFF = "interval_off"
CONF_MAX_RATE = "max_rate"
CONF_MAX_CORRECTION = "max_correction"
CONF_MAX_ATTEMPTS = "max_attempts"
CONF_CONFIRMATIONS = "confirmations"
CONF_METER_AI_TASK = "meter_ai_task_entity"

SECTION_CAMERA = "camera_section"
SECTION_IMAGE = "image_section"
SECTION_DISPLAY = "display_section"
SECTION_SCHEDULE = "schedule_section"
SECTION_CHECKS = "checks_section"
METER_SECTIONS = (SECTION_CAMERA, SECTION_IMAGE, SECTION_DISPLAY, SECTION_SCHEDULE, SECTION_CHECKS)

METER_DEFAULTS = {
    CONF_TYPE: TYPE_HEAT,
    CONF_BRIGHTNESS: 60,
    CONF_WARMUP: 3,
    CONF_DISCARD: 2,
    CONF_CROP_LEFT: 0,
    CONF_CROP_TOP: 0,
    CONF_CROP_RIGHT: 100,
    CONF_CROP_BOTTOM: 100,
    CONF_ROTATE: 0,
    CONF_EXPOSURE: 100,
    CONF_INTERVAL: 60,
    CONF_INTERVAL_OFF: 360,
    CONF_MAX_ATTEMPTS: 4,
    CONF_CONFIRMATIONS: 2,
}


def type_defaults(meter_type: str) -> dict:
    """Defaults that depend on the meter type."""
    d = TYPE_DEFAULTS.get(meter_type, TYPE_DEFAULTS[TYPE_HEAT])
    return {
        CONF_UNIT: d.unit,
        CONF_DECIMALS: d.decimals,
        CONF_MAX_RATE: d.max_rate,
        CONF_MAX_CORRECTION: d.max_correction,
        CONF_INTERVAL: d.interval,
    }


def meter_defaults(meter_type: str) -> dict:
    return {**METER_DEFAULTS, **type_defaults(meter_type), CONF_TYPE: meter_type}


def meter_values(data: dict) -> dict:
    """Stored meter data with the defaults; the rotation of older versions as an angle."""
    values = {**meter_defaults(data.get(CONF_TYPE, TYPE_HEAT)), **data}
    values[CONF_ROTATE] = rotation(values.get(CONF_ROTATE))
    return values
