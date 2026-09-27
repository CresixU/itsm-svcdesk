# ai-generated: 90% - Claude Code drafted this; the author reviewed the RFC 3339 parsing rules
"""RFC 3339 instant parsing shared by the Lab 1 test clock and the Lab 2 DORA endpoint."""
from datetime import datetime, timezone


def parse_instant(raw: str) -> datetime:
    text = raw.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError("instant must include an offset")
    return dt.astimezone(timezone.utc)


def format_instant(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
