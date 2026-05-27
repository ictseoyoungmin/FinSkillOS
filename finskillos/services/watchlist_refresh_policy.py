"""Folder-aware symbol refresh policy.

The active subscription table remains the durable refresh universe. Folders add
an optional control layer: operators can scope refreshes to one or more named
watchlist folders without changing subscription state or deleting history.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)

REFRESH_FOLDER_ENV = "FINSKILLOS_REFRESH_FOLDER_NAMES"


@dataclass(frozen=True)
class WatchlistRefreshPolicy:
    tickers: tuple[str, ...]
    base_tickers: tuple[str, ...]
    active_tickers: tuple[str, ...]
    folder_tickers: tuple[str, ...]
    folder_names: tuple[str, ...]
    scope: str

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
) -> WatchlistRefreshPolicy:
    """Return the ticker universe for refresh protocols and worker cycles."""

    base = _dedupe_tickers(base_tickers)
    requested_folders = (
        _clean_names(folder_names)
        if folder_names is not None
        else _clean_names(_csv_env(REFRESH_FOLDER_ENV))
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


def _csv_env(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(part.strip() for part in raw.replace(";", ",").split(",") if part.strip())


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
    "WatchlistRefreshPolicy",
    "build_watchlist_refresh_policy",
]
