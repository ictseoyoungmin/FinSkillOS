"""Shared Pydantic schemas — Slice 13.6.

Camel-case aliases on every field so frontend consumers can read the
JSON without re-mapping. ``model_config = ConfigDict(populate_by_name=
True)`` keeps Python-side construction with snake_case fields safe.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# --- helpers --------------------------------------------------------------


def _camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.title() for part in parts[1:])


class CamelModel(BaseModel):
    """Base model that aliases snake_case → camelCase on serialisation."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_camel,
    )


# --- public common schemas -----------------------------------------------


class SystemStatus(CamelModel):
    db: str = Field(default="LIVE", description="Database adapter state.")
    mode: str = Field(
        default="READ_MODE",
        description="The UI is descriptive-only; no execution endpoint exists.",
    )
    guard_count: int = Field(
        default=0,
        description="Number of active risk-guard alerts at the snapshot time.",
    )


class ApiMeta(CamelModel):
    generated_at: datetime
    source: str = Field(
        default="fixture",
        description="Either 'fixture' (deterministic) or 'live' (DB-backed).",
    )


__all__ = ["ApiMeta", "CamelModel", "SystemStatus"]
