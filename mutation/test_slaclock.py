# ai-generated: 100% - Written from mutation/README.md docstrings to target specified behavior and boundary mutations
from datetime import datetime, timedelta

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"), (2, 1, "P2"),
        (1, 3, "P3"), (2, 2, "P3"), (3, 1, "P3"),
        (2, 3, "P4"), (3, 2, "P4"), (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency) == expected


def test_vip_promotes_only_priorities_below_p2():
    assert slaclock.priority_of(1, 1, vip=True) == "P1"
    assert slaclock.priority_of(1, 2, vip=True) == "P2"
    assert slaclock.priority_of(1, 3, vip=True) == "P2"
    assert slaclock.priority_of(3, 3, vip=True) == "P2"


@pytest.mark.parametrize("value", [0, 4, -1, 2.0, True, "1", None])
def test_priority_rejects_non_integer_or_out_of_range_values(value):
    with pytest.raises(ValueError):
        slaclock.priority_of(value, 1)
    with pytest.raises(ValueError):
        slaclock.priority_of(1, value)


def test_targets_are_exact_and_reject_unknown_priorities():
    assert [slaclock.targets(p) for p in ("P1", "P2", "P3", "P4")] == [
        (15, 240), (60, 480), (240, 1440), (480, 4320)
    ]
    for priority in ("p1", " P1", "P5", "", None):
        with pytest.raises(ValueError):
            slaclock.targets(priority)


def test_sla_thresholds_and_invalid_inputs():
    assert slaclock.sla_state(0, 15) == "ok"
    assert slaclock.sla_state(11, 15) == "ok"
    assert slaclock.sla_state(12, 15) == "warning"
    assert slaclock.sla_state(15, 15) == "warning"
    assert slaclock.sla_state(16, 15) == "breached"
    for elapsed, target in ((-1, 15), (0, 0), (0, -1)):
        with pytest.raises(ValueError):
            slaclock.sla_state(elapsed, target)


def test_business_time_includes_open_and_excludes_close_and_weekends():
    monday = datetime(2026, 11, 16)
    assert not slaclock.is_business_time(monday + timedelta(hours=7, minutes=59))
    assert slaclock.is_business_time(monday + timedelta(hours=8))
    assert slaclock.is_business_time(monday + timedelta(hours=15, minutes=59))
    assert not slaclock.is_business_time(monday + timedelta(hours=16))
    assert not slaclock.is_business_time(datetime(2026, 11, 14, 10))
    assert not slaclock.is_business_time(datetime(2026, 11, 15, 10))
    assert slaclock.is_business_time(monday.replace(hour=8, second=59, microsecond=999999))


def test_add_business_minutes_respects_window_boundaries_and_weekends():
    monday = datetime(2026, 11, 16, 8)
    assert slaclock.add_business_minutes(monday, 0) == monday
    assert slaclock.add_business_minutes(monday, 480) == monday + timedelta(hours=8)
    assert slaclock.add_business_minutes(datetime(2026, 11, 16, 15, 59), 1) == datetime(2026, 11, 16, 16)
    assert slaclock.add_business_minutes(datetime(2026, 11, 16, 16), 0) == datetime(2026, 11, 17, 8)
    assert slaclock.add_business_minutes(datetime(2026, 11, 16, 7), 0) == datetime(2026, 11, 16, 8)
    assert slaclock.add_business_minutes(datetime(2026, 11, 14, 12), 1) == datetime(2026, 11, 16, 8, 1)
    assert slaclock.add_business_minutes(datetime(2026, 11, 20, 15), 120) == datetime(2026, 11, 23, 9)
    assert slaclock.add_business_minutes(
        datetime(2026, 11, 16, 8, 0, 59, 999999), 1
    ) == datetime(2026, 11, 16, 8, 1)
    assert slaclock.add_business_minutes(monday, 263 * 480) == datetime(2027, 11, 17, 16)
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(monday, -1)
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(monday, 366 * 24 * 60)


def test_business_minutes_between_is_half_open_and_matches_added_duration():
    monday = datetime(2026, 11, 16, 8)
    assert slaclock.business_minutes_between(monday, monday) == 0
    assert slaclock.business_minutes_between(monday, monday + timedelta(hours=8)) == 480
    assert slaclock.business_minutes_between(
        monday.replace(second=59), monday.replace(minute=1, second=1)
    ) == 1
    assert slaclock.business_minutes_between(
        datetime(2026, 11, 16, 15), datetime(2026, 11, 17, 9)
    ) == 120
    assert slaclock.business_minutes_between(
        datetime(2026, 11, 13, 15), datetime(2026, 11, 16, 9)
    ) == 120
    assert slaclock.business_minutes_between(monday, monday + timedelta(days=366)) == 262 * 480
    for minutes in (0, 1, 60, 480, 481, 2400):
        due = slaclock.add_business_minutes(datetime(2026, 11, 16, 15, 30), minutes)
        assert slaclock.business_minutes_between(datetime(2026, 11, 16, 15, 30), due) == minutes
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(monday, monday - timedelta(minutes=1))
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(monday, monday + timedelta(days=367))


@pytest.mark.parametrize(
    ("priority", "breached", "reopens", "expected"),
    [
        ("P1", False, 0, 1), ("P2", False, 0, 1),
        ("P3", False, 0, 0), ("P4", False, 0, 0),
        ("P1", True, 0, 3), ("P2", True, 0, 2),
        ("P3", True, 0, 1), ("P4", True, 0, 1),
        ("P1", False, 2, 2), ("P3", False, 2, 1),
        ("P2", True, 2, 3), ("P1", True, 2, 3),
    ],
)
def test_escalation_tier_matrix(priority, breached, reopens, expected):
    assert slaclock.escalation_tier(priority, breached, reopens) == expected


def test_escalation_reopen_boundary_and_invalid_inputs():
    assert slaclock.escalation_tier("P3", False, 1) == 0
    assert slaclock.escalation_tier("P3", False, 2) == 1
    for priority, reopens in (("P5", 0), ("P1", -1)):
        with pytest.raises(ValueError):
            slaclock.escalation_tier(priority, False, reopens)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", 90), ("4h", 240), ("1h30m", 90), ("2d", 2880),
        ("1d4h", 1680), ("1d0h5m", 1445), ("1h59m", 119),
        ("60m", 60), ("0h60m", 60), ("  15m  ", 15),
    ],
)
def test_parse_duration_accepts_documented_forms(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "0m", "1.5h", "30m1h", "-5m", "1 h", "1h60m", "1d60m", "1m1m", "1H", "0d0h0m"],
)
def test_parse_duration_rejects_invalid_forms(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)
