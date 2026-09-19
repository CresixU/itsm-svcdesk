# ai-generated: 90% - Claude Code drafted this from API.md section 3; the author chose the C3 = vip resolution
"""The priority matrix (R-04, API.md section 3) and the C3 VIP override (DECISIONS.md, section C3)."""
from .config import C3

MATRIX = {
    (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
    (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
    (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
}

# (acknowledge within minutes, resolve within minutes) - R-12 / API.md section 4.
TARGET_MINUTES = {
    "P1": (15, 240),
    "P2": (60, 480),
    "P3": (240, 1440),
    "P4": (480, 4320),
}


def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    base = MATRIX[(impact, urgency)]
    if C3 == "vip" and vip and base in ("P3", "P4"):
        return "P2"
    return base


def targets_for(priority: str) -> tuple[int, int]:
    return TARGET_MINUTES[priority]
