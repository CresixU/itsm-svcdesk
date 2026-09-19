# ai-generated: 90% - Claude Code drafted this from API.md section 4; the author chose the C1 = wallclock resolution
"""SLA due-instant computation: the wall-clock target and the business-hours target (API.md section 4),
and the C1 choice of which clock P1 uses (DECISIONS.md, section C1).
"""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from .config import C1

WARSAW = ZoneInfo("Europe/Warsaw")
BUSINESS_START = time(8, 0, 0)
BUSINESS_END = time(16, 0, 0)


def _is_business_day(dt: datetime) -> bool:
    return dt.weekday() < 5  # Monday .. Friday


def _start_of_business(dt: datetime) -> datetime:
    return dt.replace(hour=8, minute=0, second=0, microsecond=0)


def _end_of_business(dt: datetime) -> datetime:
    return dt.replace(hour=16, minute=0, second=0, microsecond=0)


def _next_business_day_open(dt: datetime) -> datetime:
    day = _start_of_business(dt)
    while True:
        day = day + timedelta(days=1)
        if _is_business_day(day):
            return day


def _advance_to_opening(local_dt: datetime) -> datetime:
    """The next instant at or after local_dt that lies inside a business window."""
    if _is_business_day(local_dt) and local_dt.time() < BUSINESS_END:
        if local_dt.time() < BUSINESS_START:
            return _start_of_business(local_dt)
        return local_dt
    return _next_business_day_open(local_dt)


def _add_business_minutes(start_utc: datetime, minutes: int) -> datetime:
    cur = _advance_to_opening(start_utc.astimezone(WARSAW))
    remaining = minutes
    while remaining > 0:
        close = _end_of_business(cur)
        available = round((close - cur).total_seconds() / 60)
        if remaining < available:
            cur = cur + timedelta(minutes=remaining)
            remaining = 0
        elif remaining == available:
            cur = close  # the tie rule: due exactly at closing, not 08:00 the next day
            remaining = 0
        else:
            remaining -= available
            cur = _next_business_day_open(cur)
    return cur.astimezone(timezone.utc)


def ack_clock_for(priority: str) -> str:
    return "wallclock" if priority == "P1" and C1 == "wallclock" else "business"


def resolve_clock_for(priority: str) -> str:
    return "wallclock" if priority == "P1" and C1 == "wallclock" else "business"


def due_at(created_at: datetime, minutes: int, clock: str) -> datetime:
    if clock == "wallclock":
        return created_at + timedelta(minutes=minutes)
    return _add_business_minutes(created_at, minutes)


def is_outside_business_hours(instant: datetime) -> bool:
    local = instant.astimezone(WARSAW)
    return not (_is_business_day(local) and BUSINESS_START <= local.time() < BUSINESS_END)
