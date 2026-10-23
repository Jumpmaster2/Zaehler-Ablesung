"""Constants."""

from __future__ import annotations

import logging

from homeassistant.const import Platform

from .logic.image import crop_after_rotation, rotation
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
# second picture of a run with other light brightness
SECOND_IMAGE_NAME = "letztes_2.jpg"
# valid readings the AI gets for a plausibility check
HISTORY_KEEP = 3
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
CONF_BRIGHTNESS_2 = "light_brightness_2"
CONF_WARMUP = "warmup"
CONF_DISCARD = "discard_frames"
# external light (light or switch entity) besides the light of the camera
CONF_EXTERNAL_LIGHT = "external_light"
CONF_EXTERNAL_LIGHT_MODE = "external_light_mode"
CONF_EXTERNAL_LIGHT_BRIGHTNESS = "external_light_brightness"
CONF_EXTERNAL_LIGHT_LEAD_TIME = "external_light_lead_time"
CONF_EXTERNAL_LIGHT_TURN_OFF = "external_light_turn_off"
# only during the pictures, or on all the time (only switched on when it is off)
EXTERNAL_LIGHT_CAPTURE = "capture"
EXTERNAL_LIGHT_PERMANENT = "permanent"
EXTERNAL_LIGHT_MODES = [EXTERNAL_LIGHT_CAPTURE, EXTERNAL_LIGHT_PERMANENT]
CONF_CROP_LEFT = "crop_left"
CONF_CROP_TOP = "crop_top"
CONF_CROP_RIGHT = "crop_right"
CONF_CROP_BOTTOM = "crop_bottom"
CONF_ROTATE = "rotate"
CONF_EXPOSURE = "exposure"
CONF_ENHANCE = "enhance"
CONF_UNIT = "unit"
CONF_DECIMALS = "decimals"
CONF_HINTS = "hints"
CONF_PROMPT = "prompt"
CONF_INTERVAL = "interval"
CONF_CONDITION = "condition_entity"
CONF_INTERVAL_OFF = "interval_off"
CONF_MAX_RATE = "max_rate"
CONF_MAX_CORRECTION = "max_correction"
CONF_MAX_ATTEMPTS = "max_attempts"
CONF_CONFIRMATIONS = "confirmations"
CONF_METER_AI_TASK = "meter_ai_task_entity"
CONF_HISTORY_HINT = "history_hint"
# from the how-many-th time in a row a notification is sent (0: never)
CONF_NOTIFY_SMALLER = "notify_smaller"
CONF_NOTIFY_TOO_LARGE = "notify_too_large"
CONF_NOTIFY_CORRECTED = "notify_corrected"
CONF_NOTIFY_FAILED = "notify_failed"

SECTION_CAMERA = "camera_section"
SECTION_EXTERNAL_LIGHT = "external_light_section"
SECTION_IMAGE = "image_section"
SECTION_DISPLAY = "display_section"
SECTION_SCHEDULE = "schedule_section"
SECTION_CHECKS = "checks_section"
SECTION_NOTIFY = "notify_section"
METER_SECTIONS = (
    SECTION_CAMERA,
    SECTION_EXTERNAL_LIGHT,
    SECTION_IMAGE,
    SECTION_DISPLAY,
    SECTION_SCHEDULE,
    SECTION_CHECKS,
    SECTION_NOTIFY,
)

METER_DEFAULTS = {
    CONF_TYPE: TYPE_HEAT,
    CONF_BRIGHTNESS: 60,
    CONF_BRIGHTNESS_2: 0,
    CONF_WARMUP: 3,
    CONF_DISCARD: 2,
    CONF_EXTERNAL_LIGHT_MODE: EXTERNAL_LIGHT_CAPTURE,
    CONF_EXTERNAL_LIGHT_BRIGHTNESS: 100,
    CONF_EXTERNAL_LIGHT_LEAD_TIME: 2,
    CONF_EXTERNAL_LIGHT_TURN_OFF: True,
    CONF_CROP_LEFT: 0,
    CONF_CROP_TOP: 0,
    CONF_CROP_RIGHT: 100,
    CONF_CROP_BOTTOM: 100,
    CONF_ROTATE: 0,
    CONF_EXPOSURE: 100,
    CONF_ENHANCE: False,
    CONF_INTERVAL: 60,
    CONF_INTERVAL_OFF: 360,
    CONF_MAX_ATTEMPTS: 4,
    CONF_CONFIRMATIONS: 2,
    CONF_HISTORY_HINT: False,
    CONF_NOTIFY_SMALLER: 1,
    CONF_NOTIFY_TOO_LARGE: 1,
    CONF_NOTIFY_CORRECTED: 1,
    CONF_NOTIFY_FAILED: 3,
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
    """Stored meter data with the defaults; older versions are converted.

    They stored the rotation as text ("90") and turned the picture after cropping.
    """
    values = {**meter_defaults(data.get(CONF_TYPE, TYPE_HEAT)), **data}
    rotate = values.get(CONF_ROTATE)
    if isinstance(rotate, str):
        crop = (CONF_CROP_LEFT, CONF_CROP_TOP, CONF_CROP_RIGHT, CONF_CROP_BOTTOM)
        turned = crop_after_rotation(*(float(values[k]) for k in crop), rotate)
        values.update(zip(crop, turned, strict=True))
    values[CONF_ROTATE] = rotation(rotate)
    return values
