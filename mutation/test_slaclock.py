# ai-generated: 85% - Claude Code wrote these tests from the docstrings of slaclock.py (not from its code), boundary by boundary; the author reviews them
"""Tests of slaclock, written against its docstrings (the specification).

Dates used: 2026-11-09 is a Monday, so the 14th is a Saturday and the 15th a Sunday.
Nothing here calls the module while the file is being imported (a collection error is not a kill).
"""

from datetime import datetime, timedelta

import pytest

from slaclock import (
    add_business_minutes,
    business_minutes_between,
    escalation_tier,
    is_business_time,
    parse_duration,
    priority_of,
    sla_state,
    targets,
)

MON = datetime(2026, 11, 9)
TUE = datetime(2026, 11, 10)
WED = datetime(2026, 11, 11)
THU = datetime(2026, 11, 12)
FRI = datetime(2026, 11, 13)
SAT = datetime(2026, 11, 14)
SUN = datetime(2026, 11, 15)
NEXT_MON = datetime(2026, 11, 16)


def at(day, hour, minute=0, second=0, microsecond=0):
    return day.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)


def weekdays_between(first, last):
    """The number of Monday-to-Friday dates from first to last, both inclusive (an independent count)."""
    count = 0
    day = first
    while day <= last:
        if day.weekday() < 5:
            count += 1
        day += timedelta(days=1)
    return count


# ------------------------------------------------------------------------------------------ priority_of

MATRIX = {
    (1, 1): "P1",
    (1, 2): "P2",
    (2, 1): "P2",
    (1, 3): "P3",
    (2, 2): "P3",
    (3, 1): "P3",
    (2, 3): "P4",
    (3, 2): "P4",
    (3, 3): "P4",
}


@pytest.mark.parametrize("cell,expected", sorted(MATRIX.items()))
def test_priority_matrix(cell, expected):
    assert priority_of(*cell) == expected
    assert priority_of(cell[0], cell[1], False) == expected
    assert priority_of(cell[0], cell[1], vip=False) == expected


@pytest.mark.parametrize("cell,base", sorted(MATRIX.items()))
def test_vip_is_never_below_p2(cell, base):
    expected = base if base in ("P1", "P2") else "P2"
    assert priority_of(cell[0], cell[1], True) == expected
    assert priority_of(cell[0], cell[1], vip=True) == expected


def test_vip_keeps_p1_and_p2_unchanged():
    assert priority_of(1, 1, vip=True) == "P1"
    assert priority_of(1, 2, vip=True) == "P2"
    assert priority_of(2, 1, vip=True) == "P2"


def test_vip_lifts_the_lowest_cell_to_p2_not_p1_or_p3():
    assert priority_of(3, 3, vip=True) == "P2"
    assert priority_of(2, 2, vip=True) == "P2"


BAD_LEVELS = [0, 4, -1, 100, 2.0, 1.0, True, False, "1", None, [1]]


@pytest.mark.parametrize("bad", BAD_LEVELS)
def test_impact_must_be_an_int_from_1_to_3(bad):
    with pytest.raises(ValueError):
        priority_of(bad, 1)
    with pytest.raises(ValueError):
        priority_of(bad, 3)
    with pytest.raises(ValueError):
        priority_of(bad, 1, vip=True)


@pytest.mark.parametrize("bad", BAD_LEVELS)
def test_urgency_must_be_an_int_from_1_to_3(bad):
    with pytest.raises(ValueError):
        priority_of(1, bad)
    with pytest.raises(ValueError):
        priority_of(3, bad)
    with pytest.raises(ValueError):
        priority_of(1, bad, vip=True)


def test_priority_boundaries_of_the_accepted_range_are_accepted():
    for impact in (1, 2, 3):
        for urgency in (1, 2, 3):
            assert priority_of(impact, urgency) in ("P1", "P2", "P3", "P4")


# ------------------------------------------------------------------------------------------ targets

@pytest.mark.parametrize(
    "priority,expected",
    [("P1", (15, 240)), ("P2", (60, 480)), ("P3", (240, 1440)), ("P4", (480, 4320))],
)
def test_targets(priority, expected):
    response, resolution = targets(priority)
    assert (response, resolution) == expected
    assert tuple(targets(priority)) == expected


@pytest.mark.parametrize("bad", ["p1", " P1", "P1 ", "P5", "P0", "", "P", "1", "PP1", "p2", "P 1"])
def test_targets_lookup_is_exact(bad):
    with pytest.raises(ValueError):
        targets(bad)


# ------------------------------------------------------------------------------------------ sla_state

@pytest.mark.parametrize(
    "elapsed,target,expected",
    [
        (0, 15, "ok"),
        (1, 15, "ok"),
        (11, 15, "ok"),
        (12, 15, "warning"),
        (13, 15, "warning"),
        (14, 15, "warning"),
        (15, 15, "warning"),
        (16, 15, "breached"),
        (1000, 15, "breached"),
        (0, 100, "ok"),
        (74, 100, "ok"),
        (75, 100, "warning"),
        (76, 100, "warning"),
        (99, 100, "warning"),
        (100, 100, "warning"),
        (101, 100, "breached"),
        (0, 4, "ok"),
        (2, 4, "ok"),
        (3, 4, "warning"),
        (4, 4, "warning"),
        (5, 4, "breached"),
        (0, 1, "ok"),
        (1, 1, "warning"),
        (2, 1, "breached"),
        (179, 240, "ok"),
        (180, 240, "warning"),
        (240, 240, "warning"),
        (241, 240, "breached"),
        (3239, 4320, "ok"),
        (3240, 4320, "warning"),
        (4320, 4320, "warning"),
        (4321, 4320, "breached"),
    ],
)
def test_sla_state(elapsed, target, expected):
    assert sla_state(elapsed, target) == expected


def test_equality_is_not_a_breach():
    for target in (1, 2, 15, 60, 240, 1440):
        assert sla_state(target, target) == "warning"
        assert sla_state(target + 1, target) == "breached"


def test_warning_starts_at_75_percent_without_rounding():
    # 11.25 minutes of 15: 11 is still ok, 12 is warning
    assert sla_state(11, 15) == "ok"
    assert sla_state(12, 15) == "warning"
    # 75 % of 8 is exactly 6
    assert sla_state(5, 8) == "ok"
    assert sla_state(6, 8) == "warning"
    # 75 % of 7 is 5.25
    assert sla_state(5, 7) == "ok"
    assert sla_state(6, 7) == "warning"


@pytest.mark.parametrize("elapsed,target", [(-1, 10), (-100, 10), (-1, 1), (0, 0), (5, 0), (5, -1), (0, -10), (-1, 0), (-1, -1)])
def test_sla_state_rejects_negative_elapsed_and_non_positive_target(elapsed, target):
    with pytest.raises(ValueError):
        sla_state(elapsed, target)


def test_zero_elapsed_is_accepted():
    assert sla_state(0, 1) == "ok"


# ------------------------------------------------------------------------------------------ is_business_time

@pytest.mark.parametrize("day", [MON, TUE, WED, THU, FRI])
def test_weekday_window_is_08_to_16_half_open(day):
    assert not is_business_time(at(day, 0, 0))
    assert not is_business_time(at(day, 7, 0))
    assert not is_business_time(at(day, 7, 59))
    assert is_business_time(at(day, 8, 0))
    assert is_business_time(at(day, 8, 1))
    assert is_business_time(at(day, 12, 0))
    assert is_business_time(at(day, 15, 59))
    assert not is_business_time(at(day, 16, 0))
    assert not is_business_time(at(day, 16, 1))
    assert not is_business_time(at(day, 23, 59))


@pytest.mark.parametrize("day", [SAT, SUN])
def test_weekend_is_never_business_time(day):
    for hour, minute in ((0, 0), (8, 0), (9, 30), (12, 0), (15, 59), (16, 0)):
        assert not is_business_time(at(day, hour, minute))


def test_is_business_time_ignores_seconds():
    assert is_business_time(at(MON, 15, 59, 59))
    assert not is_business_time(at(MON, 7, 59, 59))
    assert not is_business_time(at(MON, 16, 0, 0))
    assert is_business_time(at(MON, 8, 0, 0))


def test_is_business_time_returns_a_bool():
    assert is_business_time(at(MON, 9)) is True
    assert is_business_time(at(SAT, 9)) is False
    assert is_business_time(at(MON, 17)) is False


# ------------------------------------------------------------------------------------------ add_business_minutes

def test_add_inside_business_hours():
    assert add_business_minutes(at(MON, 9), 60) == at(MON, 10)
    assert add_business_minutes(at(MON, 9, 15), 1) == at(MON, 9, 16)
    assert add_business_minutes(at(MON, 8), 1) == at(MON, 8, 1)
    assert add_business_minutes(at(MON, 15), 59) == at(MON, 15, 59)


def test_zero_minutes_inside_business_hours_is_the_start_itself():
    assert add_business_minutes(at(MON, 9, 17), 0) == at(MON, 9, 17)
    assert add_business_minutes(at(MON, 8), 0) == at(MON, 8)
    assert add_business_minutes(at(MON, 15, 59), 0) == at(MON, 15, 59)


def test_zero_minutes_outside_business_hours_is_the_next_opening():
    assert add_business_minutes(at(MON, 7, 0), 0) == at(MON, 8)
    assert add_business_minutes(at(MON, 7, 59), 0) == at(MON, 8)
    assert add_business_minutes(at(MON, 16, 0), 0) == at(TUE, 8)
    assert add_business_minutes(at(MON, 22, 30), 0) == at(TUE, 8)
    assert add_business_minutes(at(FRI, 16, 0), 0) == at(NEXT_MON, 8)
    assert add_business_minutes(at(SAT, 10), 0) == at(NEXT_MON, 8)
    assert add_business_minutes(at(SUN, 23, 59), 0) == at(NEXT_MON, 8)
    assert add_business_minutes(at(MON, 0, 0), 0) == at(MON, 8)


def test_start_before_opening_moves_to_08_of_the_same_day():
    assert add_business_minutes(at(MON, 6), 30) == at(MON, 8, 30)
    assert add_business_minutes(at(WED, 0, 0), 1) == at(WED, 8, 1)
    assert add_business_minutes(at(MON, 7, 59), 1) == at(MON, 8, 1)


def test_start_after_closing_moves_to_the_next_business_day():
    assert add_business_minutes(at(MON, 17), 30) == at(TUE, 8, 30)
    assert add_business_minutes(at(MON, 16, 0), 30) == at(TUE, 8, 30)
    assert add_business_minutes(at(THU, 23, 59), 1) == at(FRI, 8, 1)


def test_start_on_friday_evening_or_the_weekend_moves_to_monday():
    assert add_business_minutes(at(FRI, 17), 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(FRI, 16, 0), 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(SAT, 10), 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(SAT, 0, 0), 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(SUN, 12), 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(SUN, 23, 59), 1) == at(NEXT_MON, 8, 1)


def test_a_target_ending_exactly_at_closing_is_due_at_16_that_day():
    assert add_business_minutes(at(MON, 9), 420) == at(MON, 16)
    assert add_business_minutes(at(MON, 8), 480) == at(MON, 16)
    assert add_business_minutes(at(MON, 15, 30), 30) == at(MON, 16)
    assert add_business_minutes(at(FRI, 8), 480) == at(FRI, 16)
    assert add_business_minutes(at(FRI, 15), 60) == at(FRI, 16)


def test_one_minute_past_closing_spills_to_the_next_business_day():
    assert add_business_minutes(at(MON, 9), 421) == at(TUE, 8, 1)
    assert add_business_minutes(at(MON, 8), 481) == at(TUE, 8, 1)
    assert add_business_minutes(at(MON, 15, 59), 2) == at(TUE, 8, 1)
    assert add_business_minutes(at(FRI, 15, 59), 2) == at(NEXT_MON, 8, 1)


def test_minutes_are_consumed_from_consecutive_windows():
    assert add_business_minutes(at(MON, 9), 480) == at(TUE, 9)
    assert add_business_minutes(at(MON, 8), 960) == at(TUE, 16)
    assert add_business_minutes(at(MON, 8), 961) == at(WED, 8, 1)
    assert add_business_minutes(at(MON, 8), 1440) == at(WED, 16)
    assert add_business_minutes(at(MON, 8), 2400) == at(FRI, 16)
    assert add_business_minutes(at(MON, 8), 2401) == at(NEXT_MON, 8, 1)
    assert add_business_minutes(at(MON, 8), 2880) == at(NEXT_MON, 16)


def test_the_weekend_does_not_count():
    assert add_business_minutes(at(FRI, 15), 120) == at(NEXT_MON, 9)
    assert add_business_minutes(at(FRI, 15), 60) == at(FRI, 16)
    assert add_business_minutes(at(FRI, 9), 7 * 60 + 30) == at(NEXT_MON, 8, 30)
    assert add_business_minutes(at(FRI, 8), 481) == at(NEXT_MON, 8, 1)
    assert add_business_minutes(at(THU, 15), 60 + 480 + 30) == at(NEXT_MON, 8, 30)


def test_seconds_and_microseconds_of_the_start_are_ignored():
    assert add_business_minutes(at(MON, 9, 0, 45, 500000), 60) == at(MON, 10)
    assert add_business_minutes(at(MON, 9, 0, 59, 999999), 0) == at(MON, 9)
    assert add_business_minutes(at(MON, 15, 59, 59), 1) == at(MON, 16)
    assert add_business_minutes(at(MON, 15, 59, 59), 0) == at(MON, 15, 59)
    assert add_business_minutes(at(MON, 7, 59, 59), 0) == at(MON, 8)


def test_the_result_is_a_whole_minute_datetime():
    due = add_business_minutes(at(MON, 9, 0, 30, 123), 90)
    assert isinstance(due, datetime)
    assert due.second == 0 and due.microsecond == 0
    assert due == at(MON, 10, 30)


@pytest.mark.parametrize("minutes", [-1, -2, -60, -100000])
def test_negative_minutes_are_rejected(minutes):
    with pytest.raises(ValueError):
        add_business_minutes(at(MON, 9), minutes)
    with pytest.raises(ValueError):
        add_business_minutes(at(SAT, 9), minutes)


def test_the_due_date_may_be_366_days_after_the_start_but_not_367():
    start = at(MON, 8)
    last_allowed_day = datetime(start.year, start.month, start.day) + timedelta(days=366)
    business_days = weekdays_between(datetime(start.year, start.month, start.day), last_allowed_day)
    allowed = business_days * 480
    due = add_business_minutes(start, allowed)
    assert due.date() == last_allowed_day.date()
    assert due == last_allowed_day.replace(hour=16)
    with pytest.raises(ValueError):
        add_business_minutes(start, allowed + 1)
    with pytest.raises(ValueError):
        add_business_minutes(start, allowed + 480)
    with pytest.raises(ValueError):
        add_business_minutes(start, 10_000_000)


def test_the_limit_is_counted_in_calendar_days_from_the_start_date():
    start = at(MON, 15, 59)
    last_allowed_day = datetime(MON.year, MON.month, MON.day) + timedelta(days=366)
    business_days = weekdays_between(datetime(MON.year, MON.month, MON.day), last_allowed_day)
    # the first day offers a single minute, the rest are full days
    allowed = 1 + (business_days - 1) * 480
    assert add_business_minutes(start, allowed) == last_allowed_day.replace(hour=16)
    with pytest.raises(ValueError):
        add_business_minutes(start, allowed + 1)


def test_the_limit_applies_to_a_start_on_a_weekend_too():
    start = at(SAT, 10)
    day_366 = datetime(SAT.year, SAT.month, SAT.day) + timedelta(days=366)
    business_days = weekdays_between(datetime(SAT.year, SAT.month, SAT.day), day_366)
    allowed = business_days * 480
    assert add_business_minutes(start, allowed).date() <= day_366.date()
    with pytest.raises(ValueError):
        add_business_minutes(start, allowed + 1)


# ------------------------------------------------------------------------------------------ business_minutes_between

def test_between_the_same_instant_is_zero():
    assert business_minutes_between(at(MON, 9), at(MON, 9)) == 0
    assert business_minutes_between(at(SAT, 9), at(SAT, 9)) == 0
    assert business_minutes_between(at(MON, 20), at(MON, 20)) == 0


@pytest.mark.parametrize(
    "start,end",
    [
        (at(MON, 9), at(MON, 8, 59)),
        (at(MON, 9), at(MON, 8)),
        (at(TUE, 9), at(MON, 17)),
        (at(SAT, 9), at(FRI, 9)),
        (at(MON, 9, 1), at(MON, 9, 0)),
    ],
)
def test_between_rejects_an_end_before_the_start(start, end):
    with pytest.raises(ValueError):
        business_minutes_between(start, end)


def test_between_inside_one_day():
    assert business_minutes_between(at(MON, 9), at(MON, 10)) == 60
    assert business_minutes_between(at(MON, 9), at(MON, 9, 1)) == 1
    assert business_minutes_between(at(MON, 8), at(MON, 16)) == 480
    assert business_minutes_between(at(MON, 12, 30), at(MON, 15, 45)) == 195


def test_between_ignores_time_outside_business_hours():
    assert business_minutes_between(at(MON, 7), at(MON, 9)) == 60
    assert business_minutes_between(at(MON, 15), at(MON, 17)) == 60
    assert business_minutes_between(at(MON, 0, 0), at(MON, 23, 59)) == 480
    assert business_minutes_between(at(MON, 6), at(MON, 7)) == 0
    assert business_minutes_between(at(MON, 17), at(MON, 20)) == 0


def test_between_is_half_open_at_both_edges_of_the_window():
    assert business_minutes_between(at(MON, 15, 59), at(MON, 16)) == 1
    assert business_minutes_between(at(MON, 16), at(MON, 16, 1)) == 0
    assert business_minutes_between(at(MON, 7, 59), at(MON, 8)) == 0
    assert business_minutes_between(at(MON, 8), at(MON, 8, 1)) == 1
    assert business_minutes_between(at(MON, 7, 59), at(MON, 8, 1)) == 1
    assert business_minutes_between(at(MON, 15, 59), at(MON, 16, 1)) == 1


def test_between_across_days():
    assert business_minutes_between(at(MON, 16), at(TUE, 8)) == 0
    assert business_minutes_between(at(MON, 15), at(TUE, 9)) == 120
    assert business_minutes_between(at(MON, 9), at(TUE, 9)) == 480
    assert business_minutes_between(at(MON, 8), at(WED, 8)) == 960
    assert business_minutes_between(at(MON, 12), at(THU, 12)) == 3 * 480


def test_between_skips_the_weekend():
    assert business_minutes_between(at(FRI, 15), at(NEXT_MON, 9)) == 120
    assert business_minutes_between(at(FRI, 16), at(NEXT_MON, 8)) == 0
    assert business_minutes_between(at(SAT, 0, 0), at(SUN, 23, 59)) == 0
    assert business_minutes_between(at(SAT, 9), at(SAT, 17)) == 0
    assert business_minutes_between(at(SUN, 9), at(NEXT_MON, 9)) == 60
    assert business_minutes_between(at(SAT, 9), at(NEXT_MON, 9)) == 60
    assert business_minutes_between(at(FRI, 8), at(NEXT_MON, 8)) == 480


def test_between_a_whole_week_is_five_business_days():
    assert business_minutes_between(at(MON, 0, 0), at(NEXT_MON, 0, 0)) == 5 * 480
    assert business_minutes_between(at(MON, 8), at(NEXT_MON, 8)) == 5 * 480
    assert business_minutes_between(at(SAT, 0, 0), at(datetime(2026, 11, 21), 0, 0)) == 5 * 480


def test_between_ignores_seconds_and_microseconds():
    assert business_minutes_between(at(MON, 9, 0, 59), at(MON, 10, 0, 1)) == 60
    assert business_minutes_between(at(MON, 9, 0, 0, 999999), at(MON, 9, 1, 0, 1)) == 1
    assert business_minutes_between(at(MON, 15, 59, 59), at(MON, 16, 0, 59)) == 1
    assert business_minutes_between(at(MON, 9, 0, 30), at(MON, 9, 0, 45)) == 0


def test_between_the_limit_is_366_calendar_days_apart():
    start = at(MON, 8)
    day_366 = datetime(MON.year, MON.month, MON.day) + timedelta(days=366)
    business_days = weekdays_between(datetime(MON.year, MON.month, MON.day), day_366)
    assert business_minutes_between(start, day_366.replace(hour=16)) == business_days * 480
    with pytest.raises(ValueError):
        business_minutes_between(start, (day_366 + timedelta(days=1)).replace(hour=9))
    with pytest.raises(ValueError):
        business_minutes_between(start, at(MON, 8) + timedelta(days=1000))


def test_between_the_limit_is_counted_in_dates_not_in_elapsed_time():
    # 366 days and 15 hours apart, but only 366 calendar days: accepted
    day_366 = datetime(MON.year, MON.month, MON.day) + timedelta(days=366)
    assert business_minutes_between(at(MON, 23, 0), day_366.replace(hour=23, minute=59)) >= 0
    # 366 days and 1 hour of elapsed time, but 367 calendar days apart: rejected
    day_367 = day_366 + timedelta(days=1)
    with pytest.raises(ValueError):
        business_minutes_between(at(MON, 23, 0), day_367.replace(hour=0, minute=0))


@pytest.mark.parametrize("start", [at(MON, 9), at(MON, 7), at(MON, 16), at(FRI, 15, 30), at(SAT, 11), at(SUN, 8), at(WED, 15, 59), at(TUE, 0, 0)])
@pytest.mark.parametrize("minutes", [0, 1, 59, 60, 420, 479, 480, 481, 960, 1000, 2400, 2401, 5000])
def test_between_is_the_inverse_of_add(start, minutes):
    due = add_business_minutes(start, minutes)
    assert business_minutes_between(start, due) == minutes


# ------------------------------------------------------------------------------------------ escalation_tier

def expected_tier(priority, breached, reopens):
    tier = 1 if priority in ("P1", "P2") else 0
    if breached:
        tier += 1
        if priority == "P1":
            tier += 1
    if reopens >= 2:
        tier += 1
    return min(tier, 3)


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
@pytest.mark.parametrize("breached", [False, True])
@pytest.mark.parametrize("reopens", [0, 1, 2, 3, 4, 10])
def test_escalation_tier_table(priority, breached, reopens):
    assert escalation_tier(priority, breached, reopens) == expected_tier(priority, breached, reopens)


@pytest.mark.parametrize(
    "priority,breached,reopens,expected",
    [
        ("P1", False, 0, 1),
        ("P1", False, 1, 1),
        ("P1", False, 2, 2),
        ("P1", True, 0, 3),
        ("P1", True, 1, 3),
        ("P1", True, 2, 3),
        ("P2", False, 0, 1),
        ("P2", False, 2, 2),
        ("P2", True, 0, 2),
        ("P2", True, 1, 2),
        ("P2", True, 2, 3),
        ("P3", False, 0, 0),
        ("P3", False, 1, 0),
        ("P3", False, 2, 1),
        ("P3", True, 0, 1),
        ("P3", True, 2, 2),
        ("P4", False, 0, 0),
        ("P4", False, 5, 1),
        ("P4", True, 0, 1),
        ("P4", True, 1, 1),
        ("P4", True, 2, 2),
    ],
)
def test_escalation_tier_examples(priority, breached, reopens, expected):
    assert escalation_tier(priority, breached, reopens) == expected


def test_escalation_tier_is_capped_at_3():
    assert escalation_tier("P1", True, 2) == 3
    assert escalation_tier("P1", True, 100) == 3


@pytest.mark.parametrize("bad", ["p1", "P5", "", " P1", "P0", "1"])
def test_escalation_tier_rejects_unknown_priorities(bad):
    for breached in (False, True):
        with pytest.raises(ValueError):
            escalation_tier(bad, breached, 0)
        with pytest.raises(ValueError):
            escalation_tier(bad, breached, 3)


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
def test_escalation_tier_rejects_negative_reopens(priority):
    with pytest.raises(ValueError):
        escalation_tier(priority, False, -1)
    with pytest.raises(ValueError):
        escalation_tier(priority, True, -5)
    assert escalation_tier(priority, False, 0) >= 0


# ------------------------------------------------------------------------------------------ parse_duration

@pytest.mark.parametrize(
    "text,expected",
    [
        ("90m", 90),
        ("1m", 1),
        ("59m", 59),
        ("60m", 60),
        ("61m", 61),
        ("4h", 240),
        ("1h", 60),
        ("24h", 1440),
        ("1h30m", 90),
        ("1h59m", 119),
        ("2d", 2880),
        ("1d", 1440),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("1d1h1m", 1501),
        ("1d2m", 1442),
        ("3d", 4320),
        ("0d1h", 60),
        ("0d0h5m", 5),
        ("0h60m", 60),
        ("0h90m", 90),
        ("0d90m", 90),
        ("0d0h60m", 60),
        ("0d0h120m", 120),
        ("00005m", 5),
        ("1000d", 1_440_000),
        ("1d59m", 1499),
        ("2h5m", 125),
        ("10h10m", 610),
    ],
)
def test_parse_duration_valid(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize("text", [" 90m ", "\t5m\n", "  1h30m", "2d  ", "\n1d4h\n"])
def test_parse_duration_ignores_surrounding_whitespace(text):
    assert parse_duration(text) == parse_duration(text.strip())


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "0m",
        "0h",
        "0d",
        "0h0m",
        "0d0h0m",
        "1.5h",
        "30m1h",
        "1h1d",
        "-5m",
        "1 h",
        "1h 30m",
        "5 m",
        "5",
        "m",
        "h",
        "d",
        "5M",
        "1H",
        "2D",
        "1h30",
        "1h1h",
        "1d1d",
        "5m5m",
        "m5",
        "1h60m",
        "1h61m",
        "1d60m",
        "1d0h60m",
        "2h60m",
        "0d2h60m",
        "1d99m",
        "abc",
        "1x",
        "1hm",
        "+5m",
        "5m.",
        "1,5h",
    ],
)
def test_parse_duration_invalid(text):
    with pytest.raises(ValueError):
        parse_duration(text)


def test_parse_duration_minutes_below_60_after_days_or_hours():
    assert parse_duration("1h59m") == 119
    assert parse_duration("1d59m") == 1499
    with pytest.raises(ValueError):
        parse_duration("1h60m")
    with pytest.raises(ValueError):
        parse_duration("1d60m")


def test_parse_duration_returns_an_int():
    assert isinstance(parse_duration("1h30m"), int)
    assert isinstance(parse_duration("90m"), int)


# ------------------------------------------------------------------------------------------ whole minutes (int)

@pytest.mark.parametrize(
    "start,end,expected",
    [
        (at(MON, 9), at(MON, 10), 60),
        (at(MON, 7), at(MON, 9), 60),
        (at(MON, 9), at(MON, 9), 0),
        (at(SAT, 9), at(SUN, 9), 0),
        (at(FRI, 15), at(NEXT_MON, 9), 120),
        (at(MON, 9, 0, 30), at(MON, 10, 0, 45), 60),
    ],
)
def test_business_minutes_are_whole_minutes_of_type_int(start, end, expected):
    result = business_minutes_between(start, end)
    assert result == expected
    assert type(result) is int
