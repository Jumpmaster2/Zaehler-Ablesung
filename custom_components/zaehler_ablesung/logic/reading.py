"""Evaluation of meter readings: majority vote, plausibility check and rate.

Pure functions without Home Assistant so they can be tested on their own.
A reading counts when the same value was read on two pictures. A value below
the previous one is only taken as a correction after further pictures confirm it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Result of one picture: a number as text, or one of these markers
UNREADABLE = "unreadable"
ERROR = "error"

STATUS_OK = "ok"
STATUS_CORRECTED = "corrected"
STATUS_UNREADABLE = "unreadable"
STATUS_ERROR = "error"
STATUS_SMALLER = "smaller"
STATUS_TOO_LARGE = "too_large"
STATUS_MANUAL = "manual"
STATUSES = [
    STATUS_OK,
    STATUS_CORRECTED,
    STATUS_UNREADABLE,
    STATUS_ERROR,
    STATUS_SMALLER,
    STATUS_TOO_LARGE,
    STATUS_MANUAL,
]
VALID_STATUSES = (STATUS_OK, STATUS_CORRECTED, STATUS_MANUAL)

# without a previous valid reading the plausibility window is 2 h, and never below 0.5 h
DEFAULT_HOURS = 2.0
MIN_HOURS = 0.5
# below this time span no rate is calculated (too inaccurate)
MIN_RATE_HOURS = 0.05

_NUMBER = re.compile(r"^\d+(\.\d+)?$")
# a number with a label before it ("Zählerstand: ...") or a unit after it
_LABELLED = re.compile(
    r"^(?:[^\d:]*:\s*)?(\d+(?:[.,]\d+)?)\s*(?:m³|m3|kwh|mwh|wh|gj|mj|l|liter|litre)?\.?$",
    re.IGNORECASE,
)

# after a failed reading (camera, AI or unreadable) the next try comes sooner
RETRY_MINUTES = 15.0
FAILED_STATUSES = (STATUS_ERROR, STATUS_UNREADABLE)
# rejected or corrected values, counted in a row for the notification
STREAK_STATUSES = (STATUS_SMALLER, STATUS_TOO_LARGE, STATUS_CORRECTED)


def _single(text: str) -> str | None:
    """A number text or UNREADABLE for one line of the answer, None when it is neither."""
    # markdown emphasis and code marks around the result
    text = text.replace("*", "").strip().strip("`_").strip().replace(",", ".")
    if _NUMBER.match(text):
        return text
    if match := _LABELLED.match(text):
        return match.group(1)
    if text.lower().rstrip(".") in ("unlesbar", "unreadable"):
        return UNREADABLE
    return None


def normalize(answer: object) -> str:
    """One answer of the AI as a number text, UNREADABLE or ERROR.

    Some models explain their reading before the result although they were told
    not to; then the last line counts.
    """
    if answer is None:
        return ERROR
    text = str(answer).strip()
    if (result := _single(text)) is not None:
        return result
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > 1 and (result := _single(lines[-1])) is not None:
        return result
    return UNREADABLE if text else ERROR


def is_number(value: str) -> bool:
    return bool(_NUMBER.match(value))


def consensus(readings: list[str]) -> float | None:
    """First value (in order of appearance) that was read at least twice."""
    numbers = [float(r) for r in readings if is_number(r)]
    for value in dict.fromkeys(numbers):
        if numbers.count(value) >= 2:
            return value
    return None


def has_consensus(readings: list[str]) -> bool:
    return consensus(readings) is not None


def plausibility_hours(hours_since_valid: float | None) -> float:
    """Time window for the plausibility check."""
    if hours_since_valid is None:
        return DEFAULT_HOURS
    return max(hours_since_valid, MIN_HOURS)


def classify(
    readings: list[str],
    previous: float | None,
    hours_since_valid: float | None,
    max_rate: float,
) -> tuple[str, float | None]:
    """Status and the agreed value of a reading (before a possible confirmation)."""
    value = consensus(readings)
    if value is None:
        if readings and all(r == ERROR for r in readings):
            return STATUS_ERROR, None
        return STATUS_UNREADABLE, None
    if previous is None:
        return STATUS_OK, value
    if value < previous:
        return STATUS_SMALLER, value
    if value - previous > max_rate * plausibility_hours(hours_since_valid):
        return STATUS_TOO_LARGE, value
    return STATUS_OK, value


def needs_confirmation(
    status: str, value: float | None, previous: float | None, max_correction: float
) -> bool:
    """A smaller value within the allowed correction is checked with more pictures."""
    return (
        status == STATUS_SMALLER
        and value is not None
        and previous is not None
        and previous - value <= max_correction
    )


def first_needs_confirmation(status: str, value: float | None, previous: float | None) -> bool:
    """The very first value has nothing to be checked against: more pictures confirm it.

    A wrong first value (e.g. the decimal point missed) would make every later correct
    reading look smaller and be rejected.
    """
    return status == STATUS_OK and value is not None and previous is None


def confirmed(extra_readings: list[str], value: float) -> bool:
    """All extra pictures show the agreed value."""
    return bool(extra_readings) and all(is_number(r) and float(r) == value for r in extra_readings)


@dataclass(frozen=True, slots=True)
class RateResult:
    """New rate: a number, reset (None with reset=True) or keep the old one."""

    value: float | None = None
    reset: bool = False
    keep: bool = False


def rate(
    status: str,
    value: float | None,
    previous: float | None,
    hours_exact: float | None,
    factor: float,
) -> RateResult:
    """Mean rate since the previous valid reading, converted with ``factor``."""
    if status in (STATUS_CORRECTED, STATUS_MANUAL):
        return RateResult(reset=True)
    if (
        status == STATUS_OK
        and value is not None
        and previous is not None
        and hours_exact is not None
        and hours_exact > MIN_RATE_HOURS
    ):
        return RateResult(value=round((value - previous) * factor / hours_exact, 3))
    return RateResult(keep=True)


def effective_interval(interval_minutes: float, status: str | None, failures: int) -> float:
    """Interval until the next reading: shorter after a failed one."""
    if failures and status in FAILED_STATUSES:
        return min(interval_minutes, RETRY_MINUTES)
    return interval_minutes


def streak(status: str, last_status: str | None, count: int) -> tuple[str | None, int]:
    """Status of the current run of rejected or corrected values and how long it is.

    The same status again makes the run longer, a valid reading ends it. A failed
    reading (camera, AI, unreadable) shows no value and leaves the run as it is;
    failures are counted on their own.
    """
    if status in FAILED_STATUSES:
        return last_status, count
    if status in STREAK_STATUSES:
        return status, count + 1 if status == last_status else 1
    return None, 0


def should_notify(status: str, count: int, after: int) -> bool:
    """Reported from the ``after``-th time in a row on (0: never)."""
    return status != STATUS_OK and after > 0 and count >= after


def interval_due(
    minutes_since_check: float | None, interval_minutes: float, tolerance_minutes: float = 2
) -> bool:
    """A new reading is due (a few minutes early is fine, the check runs every 5 min)."""
    if minutes_since_check is None:
        return True
    return minutes_since_check >= interval_minutes - tolerance_minutes
