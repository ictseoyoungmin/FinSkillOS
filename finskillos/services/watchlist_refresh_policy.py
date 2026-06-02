"""Folder-aware symbol refresh policy.

The active subscription table remains the durable refresh universe. Folders add
an optional control layer: operators can scope refreshes to one or more named
watchlist folders without changing subscription state or deleting history.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.runtime_settings import read_runtime_csv

REFRESH_FOLDER_ENV = "FINSKILLOS_REFRESH_FOLDER_NAMES"

CollectionType = Literal["market", "indicator", "news"]

# Maps a collection type to the per-folder flag that enables it (Slice W-2).
_COLLECTION_FLAG: dict[str, str] = {
    "market": "track_market",
    "indicator": "track_indicators",
    "news": "track_news",
}


@dataclass(frozen=True)
class WatchlistRefreshPolicy:
    tickers: tuple[str, ...]
    base_tickers: tuple[str, ...]
    active_tickers: tuple[str, ...]
    folder_tickers: tuple[str, ...]
    folder_names: tuple[str, ...]
    scope: str
    collection_type: str | None = None

    @property
    def is_folder_scoped(self) -> bool:
        return self.scope == "folder"

    @property
    def detail(self) -> str:
        folders = "|".join(self.folder_names) if self.folder_names else "-"
        return (
            f"scope={self.scope},folders={folders},base={len(self.base_tickers)},"
            f"active={len(self.active_tickers)},folderTickers={len(self.folder_tickers)},"
            f"tickers={len(self.tickers)}"
        )


def build_watchlist_refresh_policy(
    session: Session,
    *,
    base_tickers: Iterable[str] = (),
    folder_names: Iterable[str] | None = None,
    collection_type: CollectionType | None = None,
    runtime_overrides: Mapping[str, str] | None = None,
) -> WatchlistRefreshPolicy:
    """Return the ticker universe for refresh protocols and worker cycles.

    When ``collection_type`` is given (Slice W-2), the universe is driven by the
    per-folder collection flags: members of every ``is_active`` folder whose
    matching type flag is on, unioned with ``base_tickers``. Inactive folders and
    folders with the type flag off contribute nothing, so an operator can scope
    each collection type independently from the GUI. When ``collection_type`` is
    ``None`` the legacy subscription/named-folder behavior is preserved (used by
    the read-only API routes)."""

    base = _dedupe_tickers(base_tickers)

    if collection_type is not None:
        try:
            flagged = _flagged_folder_tickers(session, collection_type)
            active = _dedupe_tickers(
                SymbolSubscriptionRepository(session).active_tickers()
            )
        except Exception:
            session.rollback()
            flagged = ()
            active = ()
        tickers = _dedupe_tickers((*base, *flagged))
        return WatchlistRefreshPolicy(
            tickers=tickers,
            base_tickers=base,
            active_tickers=active,
            folder_tickers=flagged,
            folder_names=(),
            scope=f"collection:{collection_type}",
            collection_type=collection_type,
        )

    requested_folders = (
        _clean_names(folder_names)
        if folder_names is not None
        else _clean_names(
            read_runtime_csv(
                REFRESH_FOLDER_ENV,
                runtime_overrides=runtime_overrides,
            )
        )
    )
    try:
        active = _dedupe_tickers(SymbolSubscriptionRepository(session).active_tickers())
        folder_tickers = _folder_member_tickers(session, requested_folders)
    except Exception:
        session.rollback()
        active = ()
        folder_tickers = ()

    scoped = bool(requested_folders and folder_tickers)
    subscription_tickers = folder_tickers if scoped else active
    tickers = _dedupe_tickers((*base, *subscription_tickers))
    return WatchlistRefreshPolicy(
        tickers=tickers,
        base_tickers=base,
        active_tickers=active,
        folder_tickers=folder_tickers,
        folder_names=requested_folders,
        scope="folder" if scoped else "all_active",
    )


def _flagged_folder_tickers(
    session: Session, collection_type: str
) -> tuple[str, ...]:
    """Members of active folders whose matching collection flag is on."""
    flag = _COLLECTION_FLAG[collection_type]
    snapshots = SymbolSubscriptionFolderRepository(session).list_snapshots()
    tickers: list[str] = []
    for folder in snapshots:
        if not folder.is_active or not getattr(folder, flag):
            continue
        tickers.extend(member.ticker for member in folder.members)
    return _dedupe_tickers(tickers)


def _folder_member_tickers(
    session: Session, folder_names: tuple[str, ...]
) -> tuple[str, ...]:
    if not folder_names:
        return ()
    requested = {name.lower() for name in folder_names}
    snapshots = SymbolSubscriptionFolderRepository(session).list_snapshots()
    tickers: list[str] = []
    for folder in snapshots:
        if folder.name.lower() not in requested:
            continue
        tickers.extend(member.ticker for member in folder.members)
    return _dedupe_tickers(tickers)


def _clean_names(values: Iterable[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = " ".join(value.strip().split())
        key = name.lower()
        if not name or key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
    return tuple(cleaned)


def _dedupe_tickers(values: Iterable[str]) -> tuple[str, ...]:
    tickers: list[str] = []
    seen: set[str] = set()
    for value in values:
        ticker = value.strip().upper() if value else ""
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        tickers.append(ticker)
    return tuple(tickers)


__all__ = [
    "REFRESH_FOLDER_ENV",
    "CollectionType",
    "WatchlistRefreshPolicy",
    "build_watchlist_refresh_policy",
]
