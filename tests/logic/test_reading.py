"""Majority vote, plausibility check and rate (same rules as the original scripts)."""

from __future__ import annotations

import pytest
from logic import reading as rd


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("1.261", "1.261"),
        (" 1,261 \n", "1.261"),
        ("`00123.456`", "00123.456"),
        ("unlesbar", rd.UNREADABLE),
        ("Unreadable.", rd.UNREADABLE),
        ("about 1.26 MWh", rd.UNREADABLE),
        ("1.261 MWh", "1.261"),
        ("1234,5 m³", "1234.5"),
        ("Zählerstand: 1234.567", "1234.567"),
        ("1.234,567", rd.UNREADABLE),
        ("1.2 oder 1.3", rd.UNREADABLE),
        ("", rd.ERROR),
        (None, rd.ERROR),
        (1.261, "1.261"),
        # an explanation before the result: the last line counts
        ("Erste Ziffer: 1\nZweite Ziffer: 2, also 1.2xx\n\n1.269", "1.269"),
        ("Digits: 1, 2, 6, 9.\n**Ergebnis:** 1.269", "1.269"),
        ("The last digit is too dark.\nunreadable", rd.UNREADABLE),
        ("Ziffern: 1, 2, 6 und 9 oder 5", rd.UNREADABLE),
        ("1.269 or 1.268?\nmaybe", rd.UNREADABLE),
    ],
)
def test_normalize(answer, expected) -> None:
    assert rd.normalize(answer) == expected


def test_consensus_needs_two_equal_values() -> None:
    assert rd.consensus(["1.261"]) is None
    assert rd.consensus(["1.261", "1.267"]) is None
    assert rd.consensus(["1.261", "1.267", "1.261"]) == 1.261
    # first value that reaches two wins, leading zeros do not matter
    assert rd.consensus(["5", "7", "7", "5"]) == 5.0
    assert rd.consensus(["00123.456", rd.UNREADABLE, "123.456"]) == 123.456
    assert rd.consensus([rd.UNREADABLE, rd.UNREADABLE]) is None


def test_classify() -> None:
    # first reading ever
    assert rd.classify(["1.2", "1.2"], None, None, 0.05) == (rd.STATUS_OK, 1.2)
    # normal increase
    assert rd.classify(["1.27", "1.27"], 1.261, 1.0, 0.05) == (rd.STATUS_OK, 1.27)
    # smaller
    assert rd.classify(["1.255", "1.255"], 1.261, 1.0, 0.05) == (rd.STATUS_SMALLER, 1.255)
    # too large: 0.1 in 1 h with 0.05/h
    assert rd.classify(["1.361", "1.361"], 1.261, 1.0, 0.05)[0] == rd.STATUS_TOO_LARGE
    # the window is at least 0.5 h: 0.02 after 6 min is fine with 0.05/h
    assert rd.classify(["1.281", "1.281"], 1.261, 0.1, 0.05)[0] == rd.STATUS_OK
    # no consensus
    assert (
        rd.classify(["1.2", rd.UNREADABLE, "1.3", rd.ERROR], 1.0, 1.0, 1)[0] == rd.STATUS_UNREADABLE
    )
    assert rd.classify([rd.ERROR] * 4, 1.0, 1.0, 1)[0] == rd.STATUS_ERROR


def test_plausibility_hours() -> None:
    assert rd.plausibility_hours(None) == 2.0
    assert rd.plausibility_hours(0.1) == 0.5
    assert rd.plausibility_hours(6) == 6


def test_correction() -> None:
    assert rd.needs_confirmation(rd.STATUS_SMALLER, 1.261, 1.267, 0.05)
    assert not rd.needs_confirmation(rd.STATUS_SMALLER, 1.1, 1.267, 0.05)
    assert not rd.needs_confirmation(rd.STATUS_OK, 1.27, 1.267, 0.05)
    assert rd.confirmed(["1.261", "1.261"], 1.261)
    assert not rd.confirmed(["1.261", "1.267"], 1.261)
    assert not rd.confirmed(["1.261", rd.UNREADABLE], 1.261)
    assert not rd.confirmed([], 1.261)


def test_rate() -> None:
    # MWh -> kW: 0.012 MWh in 2 h = 6 kW
    assert rd.rate(rd.STATUS_OK, 1.273, 1.261, 2.0, 1000) == rd.RateResult(value=6.0)
    assert rd.rate(rd.STATUS_CORRECTED, 1.261, 1.267, 2.0, 1000).reset
    assert rd.rate(rd.STATUS_MANUAL, 1.261, None, None, 1000).reset
    assert rd.rate(rd.STATUS_OK, 1.261, None, None, 1000).keep
    assert rd.rate(rd.STATUS_OK, 1.262, 1.261, 0.01, 1000).keep
    assert rd.rate(rd.STATUS_UNREADABLE, None, 1.261, 2.0, 1000).keep


def test_interval_due() -> None:
    assert rd.interval_due(None, 60)
    assert rd.interval_due(58, 60)
    assert not rd.interval_due(57.9, 60)


def test_first_needs_confirmation() -> None:
    assert rd.first_needs_confirmation(rd.STATUS_OK, 1.2, None)
    assert not rd.first_needs_confirmation(rd.STATUS_OK, 1.2, 1.1)
    assert not rd.first_needs_confirmation(rd.STATUS_UNREADABLE, None, None)


def test_retry_and_notify() -> None:
    assert rd.effective_interval(60, rd.STATUS_ERROR, 1) == rd.RETRY_MINUTES
    assert rd.effective_interval(60, rd.STATUS_UNREADABLE, 2) == rd.RETRY_MINUTES
    assert rd.effective_interval(10, rd.STATUS_ERROR, 1) == 10
    assert rd.effective_interval(60, rd.STATUS_TOO_LARGE, 0) == 60
    assert rd.effective_interval(60, rd.STATUS_OK, 0) == 60
    assert not rd.should_notify(rd.STATUS_OK, 0, 1)
    assert not rd.should_notify(rd.STATUS_ERROR, 2, 3)
    assert rd.should_notify(rd.STATUS_ERROR, 3, 3)
    assert rd.should_notify(rd.STATUS_ERROR, 4, 3)
    assert rd.should_notify(rd.STATUS_SMALLER, 1, 1)
    assert rd.should_notify(rd.STATUS_CORRECTED, 1, 1)
    assert not rd.should_notify(rd.STATUS_SMALLER, 2, 3)
    # 0: never
    assert not rd.should_notify(rd.STATUS_SMALLER, 10, 0)


def test_streak() -> None:
    assert rd.streak(rd.STATUS_SMALLER, None, 0) == (rd.STATUS_SMALLER, 1)
    assert rd.streak(rd.STATUS_SMALLER, rd.STATUS_SMALLER, 1) == (rd.STATUS_SMALLER, 2)
    # another kind starts again
    assert rd.streak(rd.STATUS_TOO_LARGE, rd.STATUS_SMALLER, 2) == (rd.STATUS_TOO_LARGE, 1)
    assert rd.streak(rd.STATUS_CORRECTED, rd.STATUS_CORRECTED, 1) == (rd.STATUS_CORRECTED, 2)
    # no value read: the run goes on
    assert rd.streak(rd.STATUS_UNREADABLE, rd.STATUS_SMALLER, 2) == (rd.STATUS_SMALLER, 2)
    assert rd.streak(rd.STATUS_ERROR, rd.STATUS_SMALLER, 2) == (rd.STATUS_SMALLER, 2)
    # a valid reading ends it
    assert rd.streak(rd.STATUS_OK, rd.STATUS_SMALLER, 2) == (None, 0)
    assert rd.streak(rd.STATUS_MANUAL, rd.STATUS_SMALLER, 2) == (None, 0)
