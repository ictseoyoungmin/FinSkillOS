"""Collection Control API schemas (Slice W-3).

Camel-case Pydantic shapes for the folder-driven collection control surface:
per-folder collection flags, members, per-type effective ticker counts, and a
global roll-up. The cockpit's Ops tab toggles these flags to decide what the
worker collects (see ``finskillos/services/watchlist_refresh_policy.py``).
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from api.schemas.common import CamelModel, SystemStatus

CollectionFlag = Literal[
    "is_active",
    "track_market",
    "track_indicators",
    "track_news",
]


class CollectionFolderMember(CamelModel):
    ticker: str
    name: str | None = None


class CollectionFolder(CamelModel):
    id: str
    name: str
    description: str | None = None
    sort_order: int = 0
    is_system: bool = False
    is_active: bool = True
    track_market: bool = True
    track_indicators: bool = True
    track_news: bool = True
    member_count: int = 0
    # Members with at least one stored market bar (coverage hint, Slice W-5).
    covered_member_count: int = 0
    members: list[CollectionFolderMember] = Field(default_factory=list)


class CollectionTotals(CamelModel):
    folder_count: int = 0
    active_folder_count: int = 0
    market_ticker_count: int = 0
    indicator_ticker_count: int = 0
    news_ticker_count: int = 0
    # Per-type "every folder has this on" roll-up (drives the global toggles).
    all_active: bool = True
    market_all: bool = True
    indicators_all: bool = True
    news_all: bool = True


class CollectionControlResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    source: Literal["fixture", "live"] = "fixture"
    folders: list[CollectionFolder] = Field(default_factory=list)
    totals: CollectionTotals = Field(default_factory=CollectionTotals)
    safety_caption: str = (
        "Collection control is descriptive-only. Toggles decide which symbols the "
        "worker observes; no orders or trade actions are ever placed."
    )


class CollectionFlagPatch(CamelModel):
    is_active: bool | None = None
    track_market: bool | None = None
    track_indicators: bool | None = None
    track_news: bool | None = None


class CollectionFolderCreate(CamelModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=240)
    sort_order: int = 0


class CollectionSymbolInput(CamelModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=120)


class GlobalToggleInput(CamelModel):
    flag: CollectionFlag
    value: bool
