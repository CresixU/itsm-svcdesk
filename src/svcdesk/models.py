# ai-generated: 90% - Claude Code drafted this from REQUIREMENTS.md R-03 and API.md section 7
"""Request validation (R-03, R-20, API.md section 7). Server-owned and unknown fields are ignored,
never rejected (extra="ignore" on every model).
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ReporterIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: Optional[str] = None
    vip: bool = False

    @field_validator("name")
    @classmethod
    def _name_length(cls, v: str) -> str:
        if not (1 <= len(v) <= 100):
            raise ValueError("reporter.name must be 1..100 characters")
        return v


class CreateTicketIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    description: str = ""
    reporter: ReporterIn
    impact: int
    urgency: int
    related_to: Optional[str] = None

    @field_validator("title")
    @classmethod
    def _title_length(cls, v: str) -> str:
        if not (1 <= len(v) <= 200):
            raise ValueError("title must be 1..200 characters")
        return v

    @field_validator("description")
    @classmethod
    def _description_length(cls, v: str) -> str:
        if len(v) > 4000:
            raise ValueError("description must be at most 4000 characters")
        return v

    @field_validator("impact", "urgency")
    @classmethod
    def _in_range(cls, v: int) -> int:
        if isinstance(v, bool) or not (1 <= v <= 3):
            raise ValueError("must be an integer in 1..3")
        return v
