"""Meters at runtime: take pictures, let the AI read them and keep the results."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.components import camera, persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CHECK_EVERY_MINUTES,
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
    CONF_EXPOSURE,
    CONF_HINTS,
    CONF_INTERVAL,
    CONF_INTERVAL_OFF,
    CONF_LIGHT,
    CONF_MAX_ATTEMPTS,
    CONF_MAX_CORRECTION,
    CONF_MAX_RATE,
    CONF_METER_AI_TASK,
    CONF_NOTIFY,
    CONF_ROTATE,
    CONF_TYPE,
    CONF_UNIT,
    CONF_WARMUP,
    DEFAULTS,
    DOMAIN,
    EVENT_READING,
    IMAGE_NAME,
    LOGGER,
    MEDIA_FOLDER,
    ORIGINAL_NAME,
    REJECTED_FOLDER,
    REJECTED_KEEP,
    SIGNAL_UPDATE,
    STORAGE_VERSION,
    SUBENTRY_METER,
    meter_values,
)
from .logic import reading as rd
from .logic.image import needs_processing, process, thumbnail
from .logic.prompt import build_instructions
from .logic.units import rate_unit

type MeterConfigEntry = ConfigEntry[MeterManager]

# Pause after the warm-up pictures before the picture that is read
SETTLE_SECONDS = 1.0
CAMERA_TIMEOUT = 15


@dataclass(slots=True)
class MeterState:
    """What is kept across restarts."""

    value: float | None = None
    value_time: datetime | None = None
    rate: float | None = None
    status: str | None = None
    last_check: datetime | None = None
    readings: list[str] | None = None
    automatic: bool = True
    # value the AI agreed on in the last run, also when it was rejected
    read_value: float | None = None
    # failed readings (camera, AI, unreadable) in a row
    failures: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "value_time": self.value_time.isoformat() if self.value_time else None,
            "rate": self.rate,
            "status": self.status,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "readings": self.readings,
            "automatic": self.automatic,
            "read_value": self.read_value,
            "failures": self.failures,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> MeterState:
        data = data or {}

        def when(key: str) -> datetime | None:
            return dt_util.parse_datetime(data[key]) if data.get(key) else None

        return cls(
            value=data.get("value"),
            value_time=when("value_time"),
            rate=data.get("rate"),
            status=data.get("status"),
            last_check=when("last_check"),
            readings=data.get("readings"),
            automatic=data.get("automatic", True),
            read_value=data.get("read_value"),
            failures=int(data.get("failures") or 0),
        )


class Meter:
    """One meter with its camera."""

    def __init__(self, manager: MeterManager, meter_id: str, title: str, data: dict) -> None:
        self.manager = manager
        self.hass = manager.hass
        self.id = meter_id
        self.title = title
        self.config = meter_values(data)
        self.state = MeterState()
        self.image: bytes | None = None
        self.image_time: datetime | None = None
        self.busy: str | None = None  # "reading" or "picture" while running
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------ settings

    def opt(self, key: str) -> Any:
        return self.config.get(key)

    @property
    def unit(self) -> str:
        return str(self.opt(CONF_UNIT) or "")

    @property
    def decimals(self) -> int:
        return int(self.opt(CONF_DECIMALS) or 0)

    @property
    def rate_unit(self) -> tuple[str, float]:
        return rate_unit(self.unit)

    @property
    def ai_task_entity(self) -> str | None:
        return self.opt(CONF_METER_AI_TASK) or self.manager.options.get(CONF_AI_TASK)

    @property
    def folder(self) -> Path:
        return self.manager.media_root / self.id

    @property
    def media_content_id(self) -> str:
        return f"media-source://media_source/local/{MEDIA_FOLDER}/{self.id}/{IMAGE_NAME}"

    def interval_minutes(self) -> float:
        """Interval now: the second interval applies while the condition entity is off,
        a failed reading is tried again sooner."""
        condition = self.opt(CONF_CONDITION)
        if condition and (st := self.hass.states.get(condition)) and st.state == "off":
            interval = float(self.opt(CONF_INTERVAL_OFF))
        else:
            interval = float(self.opt(CONF_INTERVAL))
        return rd.effective_interval(interval, self.state.status, self.state.failures)

    def next_check(self) -> datetime | None:
        if not self.state.automatic:
            return None
        if self.state.last_check is None:
            return dt_util.utcnow()
        return self.state.last_check + timedelta(minutes=self.interval_minutes())

    def is_due(self, now: datetime) -> bool:
        if not self.state.automatic or self.busy:
            return False
        minutes = (
            (now - self.state.last_check).total_seconds() / 60 if self.state.last_check else None
        )
        return rd.interval_due(minutes, self.interval_minutes())

    @callback
    def notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.id))

    # ------------------------------------------------------------ picture

    async def _light(self, on: bool) -> None:
        light = self.opt(CONF_LIGHT)
        if not light:
            return
        data: dict[str, Any] = {"entity_id": light}
        if on:
            data["brightness_pct"] = int(self.opt(CONF_BRIGHTNESS))
        await self.hass.services.async_call(
            "light", "turn_on" if on else "turn_off", data, blocking=True
        )

    async def _get_image(self) -> bytes:
        image = await camera.async_get_image(
            self.hass, self.opt(CONF_CAMERA), timeout=CAMERA_TIMEOUT
        )
        return image.content

    @contextlib.asynccontextmanager
    async def _session(self) -> AsyncIterator[None]:
        """Light on once for all pictures of a run, wait, skip the old buffered pictures.

        A light that was already on (e.g. for the live picture) stays on afterwards.
        """
        light = self.opt(CONF_LIGHT)
        state = self.hass.states.get(light) if light else None
        was_on = state is not None and state.state == "on"
        try:
            try:
                await self._light(True)
            except HomeAssistantError as err:
                LOGGER.warning("%s: could not switch the light on: %s", self.title, err)
            await asyncio.sleep(float(self.opt(CONF_WARMUP)))
            # the first pictures after a pause still come from the buffers (without light)
            for _ in range(int(self.opt(CONF_DISCARD))):
                with contextlib.suppress(HomeAssistantError, TimeoutError):
                    await self._get_image()
            if int(self.opt(CONF_DISCARD)):
                await asyncio.sleep(SETTLE_SECONDS)
            yield
        finally:
            if not was_on:
                try:
                    await self._light(False)
                except HomeAssistantError as err:
                    LOGGER.warning("%s: could not switch the light off: %s", self.title, err)

    async def async_take_picture(self) -> bytes | None:
        """One picture (inside a session), stored as original and as the picture the AI reads."""
        try:
            content = await self._get_image()
        except (HomeAssistantError, TimeoutError) as err:
            LOGGER.warning("%s: no picture from the camera: %s", self.title, err)
            return None
        image = await self.hass.async_add_executor_job(self._store_image, content)
        self.image = image
        self.image_time = dt_util.utcnow()
        self.notify()
        return image

    def _crop(self) -> tuple[float, float, float, float, float, float]:
        return (
            float(self.opt(CONF_CROP_LEFT)),
            float(self.opt(CONF_CROP_TOP)),
            float(self.opt(CONF_CROP_RIGHT)),
            float(self.opt(CONF_CROP_BOTTOM)),
            float(self.opt(CONF_ROTATE)),
            float(self.opt(CONF_EXPOSURE)),
        )

    def _store_image(self, content: bytes) -> bytes:
        """Keep the original picture and the cropped one the AI reads (executor)."""
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / ORIGINAL_NAME).write_bytes(content)
        image = process(content, *self._crop())
        (self.folder / IMAGE_NAME).write_bytes(image)
        return image

    def load_original(self) -> bytes | None:
        """Uncropped picture of the last run (executor), for choosing the crop."""
        path = self.folder / ORIGINAL_NAME
        if path.exists():
            return path.read_bytes()
        path = self.folder / IMAGE_NAME
        if path.exists() and not needs_processing(*self._crop()):
            return path.read_bytes()
        return None

    def _keep_rejected(self, stamp: str, status: str) -> None:
        """Copy the last picture of a rejected reading and keep only the newest ones."""
        source = self.folder / IMAGE_NAME
        if not source.exists():
            return
        target = self.folder / REJECTED_FOLDER
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{stamp}_{status}.jpg").write_bytes(source.read_bytes())
        for old in sorted(target.glob("*.jpg"))[:-REJECTED_KEEP]:
            old.unlink(missing_ok=True)

    def load_rejected(self) -> list[dict[str, Any]]:
        """Pictures of rejected readings, newest first, made small for the panel (executor)."""
        folder = self.folder / REJECTED_FOLDER
        if not folder.is_dir():
            return []
        result = []
        for path in sorted(folder.glob("*.jpg"), reverse=True)[:REJECTED_KEEP]:
            stamp, _, status = path.stem.partition("_")
            result.append(
                {
                    "name": path.name,
                    "stamp": stamp,
                    "status": status or None,
                    "image": thumbnail(path.read_bytes()),
                }
            )
        return result

    def load_image(self) -> None:
        """Picture of the last run (executor); cropped again in case the crop changed."""
        path = self.folder / IMAGE_NAME
        original = self.folder / ORIGINAL_NAME
        if original.exists():
            self.image = process(original.read_bytes(), *self._crop())
            path.write_bytes(self.image)
            self.image_time = dt_util.utc_from_timestamp(original.stat().st_mtime)
        elif path.exists():
            self.image = path.read_bytes()
            self.image_time = dt_util.utc_from_timestamp(path.stat().st_mtime)

    # ------------------------------------------------------------ reading

    async def _ask_ai(self) -> str:
        entity_id = self.ai_task_entity
        if not entity_id:
            LOGGER.warning("%s: no AI task entity configured", self.title)
            return rd.ERROR
        instructions = build_instructions(
            self.opt(CONF_TYPE),
            self.unit,
            self.decimals,
            self.opt(CONF_HINTS),
            self.hass.config.language,
        )
        de = (self.hass.config.language or "").startswith("de")
        task_name = f"{self.title} ablesen" if de else f"Read {self.title}"
        try:
            response = await self.hass.services.async_call(
                "ai_task",
                "generate_data",
                {
                    "task_name": task_name,
                    "entity_id": entity_id,
                    "instructions": instructions,
                    "attachments": [
                        {
                            "media_content_id": self.media_content_id,
                            "media_content_type": "image/jpeg",
                        }
                    ],
                },
                blocking=True,
                return_response=True,
            )
        except (HomeAssistantError, ValueError) as err:
            LOGGER.warning("%s: AI task failed: %s", self.title, err)
            return rd.ERROR
        answer = response.get("data") if isinstance(response, dict) else None
        LOGGER.debug("%s: AI answer %r", self.title, answer)
        return rd.normalize(answer)

    async def async_single(self) -> str:
        """One picture, read by the AI."""
        if await self.async_take_picture() is None:
            return rd.ERROR
        return await self._ask_ai()

    async def async_picture_only(self) -> bool:
        """Test picture (e.g. to try the light), not read."""
        if self._lock.locked():
            return False
        async with self._lock:
            self.busy = "picture"
            self.notify()
            try:
                async with self._session():
                    return await self.async_take_picture() is not None
            finally:
                self.busy = None
                self.notify()

    async def async_read(self) -> str | None:
        """Read the meter with a majority vote; returns the status (None when busy)."""
        if self._lock.locked():
            return None
        async with self._lock:
            self.busy = "reading"
            self.notify()
            try:
                async with self._session():
                    return await self._read()
            finally:
                self.busy = None
                self.notify()

    async def _read(self) -> str:
        now = dt_util.utcnow()
        readings: list[str] = []
        # pictures until one value was read twice
        for _ in range(int(self.opt(CONF_MAX_ATTEMPTS))):
            readings.append(await self.async_single())
            if rd.has_consensus(readings):
                break

        previous = self.state.value
        hours = (
            (now - self.state.value_time).total_seconds() / 3600 if self.state.value_time else None
        )
        status, value = rd.classify(readings, previous, hours, float(self.opt(CONF_MAX_RATE)))
        limit = float(self.opt(CONF_MAX_RATE)) * rd.plausibility_hours(hours)
        if rd.needs_confirmation(status, value, previous, float(self.opt(CONF_MAX_CORRECTION))):
            extra = [await self.async_single() for _ in range(int(self.opt(CONF_CONFIRMATIONS)))]
            readings.extend(extra)
            if value is not None and rd.confirmed(extra, value):
                status = rd.STATUS_CORRECTED
        elif rd.first_needs_confirmation(status, value, previous):
            extra = [await self.async_single() for _ in range(int(self.opt(CONF_CONFIRMATIONS)))]
            readings.extend(extra)
            if value is None or not rd.confirmed(extra, value):
                status = rd.STATUS_UNREADABLE

        valid = status in rd.VALID_STATUSES
        result = rd.rate(status, value, previous, hours, self.rate_unit[1])
        state = self.state
        state.last_check = now
        state.status = status
        state.readings = readings
        state.read_value = value
        state.failures = state.failures + 1 if status in rd.FAILED_STATUSES else 0
        if valid and value is not None:
            state.value = value
            state.value_time = now
            if not result.keep:
                state.rate = result.value
        self.manager.async_save()
        self.notify()

        self.hass.bus.async_fire(
            EVENT_READING,
            {
                "meter_id": self.id,
                "meter": self.title,
                "valid": valid,
                "status": status,
                "value": value,
                "previous": previous,
                "readings": readings,
                "unit": self.unit,
            },
        )
        if status != rd.STATUS_OK:
            stamp = dt_util.as_local(now).strftime("%Y%m%d-%H%M%S")
            await self.hass.async_add_executor_job(self._keep_rejected, stamp, status)
            if self.manager.options.get(CONF_NOTIFY, DEFAULTS[CONF_NOTIFY]) and rd.should_notify(
                status, state.failures
            ):
                self._notification(status, value, previous, readings, limit, now)
        else:
            persistent_notification.async_dismiss(self.hass, self._notification_id)
        return status

    @property
    def _notification_id(self) -> str:
        return f"{DOMAIN}_{self.id}"

    def _notification(
        self,
        status: str,
        value: float | None,
        previous: float | None,
        readings: list[str],
        limit: float,
        now: datetime,
    ) -> None:
        de = (self.hass.config.language or "").startswith("de")
        texts = STATUS_TEXT["de" if de else "en"]
        when = dt_util.as_local(now).strftime("%d.%m. %H:%M")
        unit = f" {self.unit}" if self.unit else ""
        lines = [f"{when}: {texts[status]}."]
        lines.append(("Lesungen: " if de else "Readings: ") + " / ".join(readings))
        if previous is not None:
            lines.append(("Vorheriger Wert: " if de else "Previous value: ") + f"{previous}{unit}")
        if status == rd.STATUS_CORRECTED:
            lines.append(("Neuer Wert: " if de else "New value: ") + f"{value}{unit}")
        elif status == rd.STATUS_TOO_LARGE:
            lines.append(("Grenze: +" if de else "Limit: +") + f"{round(limit, 3)}{unit}")
        title = (
            ("korrigiert" if de else "corrected")
            if status == rd.STATUS_CORRECTED
            else ("Ablesung verworfen" if de else "reading rejected")
        )
        persistent_notification.async_create(
            self.hass,
            "\n".join(lines),
            title=f"{self.title}: {title}",
            notification_id=self._notification_id,
        )

    # ------------------------------------------------------------ manual

    def set_reading(self, value: float) -> None:
        """Set the meter reading by hand (e.g. after a wrong reading)."""
        now = dt_util.utcnow()
        self.state.value = round(float(value), 6)
        self.state.value_time = now
        self.state.status = rd.STATUS_MANUAL
        self.state.rate = None
        self.state.failures = 0
        self.manager.async_save()
        self.notify()

    def set_automatic(self, on: bool) -> None:
        self.state.automatic = on
        self.manager.async_save()
        self.notify()


STATUS_TEXT = {
    "de": {
        rd.STATUS_OK: "gültig",
        rd.STATUS_CORRECTED: "kleinerer Wert mehrfach bestätigt und übernommen",
        rd.STATUS_UNREADABLE: "unlesbar",
        rd.STATUS_ERROR: "Kamera oder KI nicht erreichbar",
        rd.STATUS_SMALLER: "kleiner als der letzte Wert",
        rd.STATUS_TOO_LARGE: "Anstieg zu groß",
        rd.STATUS_MANUAL: "von Hand gesetzt",
    },
    "en": {
        rd.STATUS_OK: "valid",
        rd.STATUS_CORRECTED: "smaller value confirmed several times and taken",
        rd.STATUS_UNREADABLE: "unreadable",
        rd.STATUS_ERROR: "camera or AI not reachable",
        rd.STATUS_SMALLER: "smaller than the last value",
        rd.STATUS_TOO_LARGE: "increase too large",
        rd.STATUS_MANUAL: "set by hand",
    },
}


class MeterManager:
    """All meters of the config entry, the store and the schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.options = {**DEFAULTS, **entry.data, **entry.options}
        self.meters: dict[str, Meter] = {
            sub_id: Meter(self, sub_id, sub.title, dict(sub.data))
            for sub_id, sub in entry.subentries.items()
            if sub.subentry_type == SUBENTRY_METER
        }
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._unsub: Callable[[], None] | None = None
        media = hass.config.media_dirs.get("local") or hass.config.path("media")
        self.media_root = Path(media) / MEDIA_FOLDER

    async def async_setup(self) -> None:
        stored = await self._store.async_load() or {}
        for meter in self.meters.values():
            meter.state = MeterState.from_dict(stored.get("meters", {}).get(meter.id))
            await self.hass.async_add_executor_job(meter.load_image)
        self._unsub = async_track_time_interval(
            self.hass, self._async_tick, timedelta(minutes=CHECK_EVERY_MINUTES)
        )

    async def async_unload(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        await self._store.async_save(self._data())

    def _data(self) -> dict[str, Any]:
        return {"meters": {m.id: m.state.as_dict() for m in self.meters.values()}}

    @callback
    def async_save(self) -> None:
        self._store.async_delay_save(self._data, 1)

    @callback
    def _async_tick(self, now: datetime) -> None:
        for meter in self.meters.values():
            if meter.is_due(dt_util.utcnow()):
                self.start_reading(meter)

    @callback
    def start_reading(self, meter: Meter) -> None:
        self.entry.async_create_background_task(
            self.hass, meter.async_read(), f"{DOMAIN} read {meter.id}"
        )

    @callback
    def start_picture(self, meter: Meter) -> None:
        self.entry.async_create_background_task(
            self.hass, meter.async_picture_only(), f"{DOMAIN} picture {meter.id}"
        )

    async def async_remove_meter_files(self, meter_id: str) -> None:
        """Delete the pictures of a removed meter."""
        folder = self.media_root / meter_id
        await self.hass.async_add_executor_job(shutil.rmtree, folder, True)
