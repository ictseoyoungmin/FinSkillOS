"""Collection Control API (Slice W-3).

Folder-driven control of what the worker collects. Exposes the per-folder
collection flags (Active / Price / Indicators / News) added in slice 127, the
folder membership, per-type effective ticker counts (computed with the same
``build_watchlist_refresh_policy`` the worker uses), and a global roll-up. The
Ops cockpit surface (W-4) renders and mutates these.

Mutations are limited to folder/flag/membership organization — there is no
execution or order endpoint. All copy stays descriptive-only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException

from api.dependencies import get_session_scope
from api.schemas.collection_control import (
    CollectionControlResponse,
    CollectionFlagPatch,
    CollectionFolder,
    CollectionFolderCreate,
    CollectionFolderMember,
    CollectionSymbolInput,
    CollectionTotals,
    GlobalToggleInput,
)
from api.schemas.common import SystemStatus
from finskillos.db.repositories import (
    MarketRepository,
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.db.repositories.symbol_subscription_folder_repo import (
    SymbolSubscriptionFolderSnapshot,
)
from finskillos.services.watchlist_refresh_policy import (
    build_watchlist_refresh_policy,
)

router = APIRouter(tags=["collection-control"])

UTC = timezone.utc
_BASE = "/system-ops/collection-control"


@router.get(_BASE, response_model=CollectionControlResponse)
def get_collection_control() -> CollectionControlResponse:
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        return _build_response(session)


@router.post(f"{_BASE}/folders", response_model=CollectionControlResponse)
def create_folder(payload: CollectionFolderCreate) -> CollectionControlResponse:
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        repo = SymbolSubscriptionFolderRepository(session)
        try:
            repo.upsert_folder(
                payload.name,
                description=payload.description,
                sort_order=payload.sort_order,
            )
            session.commit()
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_response(session)


@router.patch(f"{_BASE}/folders/{{folder_id}}", response_model=CollectionControlResponse)
def patch_folder_flags(
    folder_id: UUID, payload: CollectionFlagPatch
) -> CollectionControlResponse:
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        repo = SymbolSubscriptionFolderRepository(session)
        try:
            repo.set_collection_flags(
                folder_id,
                is_active=payload.is_active,
                track_market=payload.track_market,
                track_indicators=payload.track_indicators,
                track_news=payload.track_news,
            )
            session.commit()
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _build_response(session)


@router.delete(
    f"{_BASE}/folders/{{folder_id}}", response_model=CollectionControlResponse
)
def delete_folder(folder_id: UUID) -> CollectionControlResponse:
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        repo = SymbolSubscriptionFolderRepository(session)
        try:
            removed = repo.delete_folder(folder_id)
        except ValueError as exc:
            session.rollback()
            # System folder is protected.
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not removed:
            session.rollback()
            raise HTTPException(status_code=404, detail="folder_not_found")
        session.commit()
        return _build_response(session)


@router.post(
    f"{_BASE}/folders/{{folder_id}}/symbols", response_model=CollectionControlResponse
)
def add_symbol(
    folder_id: UUID, payload: CollectionSymbolInput
) -> CollectionControlResponse:
    """Subscribe the ticker (if needed) and link it to the folder in one call."""
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        folders = SymbolSubscriptionFolderRepository(session)
        if folders.get(folder_id) is None:
            raise HTTPException(status_code=404, detail="folder_not_found")
        subscriptions = SymbolSubscriptionRepository(session)
        try:
            subscriptions.subscribe(payload.ticker, name=payload.name, source="user")
            folders.add_symbol(folder_id, payload.ticker)
            session.commit()
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _build_response(session)


@router.delete(
    f"{_BASE}/folders/{{folder_id}}/symbols/{{ticker}}",
    response_model=CollectionControlResponse,
)
def remove_symbol(folder_id: UUID, ticker: str) -> CollectionControlResponse:
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        folders = SymbolSubscriptionFolderRepository(session)
        folders.remove_symbol(folder_id, ticker)
        session.commit()
        return _build_response(session)


@router.post(f"{_BASE}/global-toggle", response_model=CollectionControlResponse)
def global_toggle(payload: GlobalToggleInput) -> CollectionControlResponse:
    """Apply one collection flag to every folder in a single call."""
    with get_session_scope() as session:
        if session is None:
            return _db_unavailable_response()
        repo = SymbolSubscriptionFolderRepository(session)
        kwargs = {payload.flag: payload.value}
        for snapshot in repo.list_snapshots():
            repo.set_collection_flags(snapshot.id, **kwargs)
        session.commit()
        return _build_response(session)


# --- builders -------------------------------------------------------------


def _build_response(session) -> CollectionControlResponse:
    repo = SymbolSubscriptionFolderRepository(session)
    snapshots = _system_first(repo.list_snapshots())
    all_tickers = {m.ticker for snap in snapshots for m in snap.members}
    covered = MarketRepository(session).tickers_with_bars(all_tickers)
    folders = [_folder_schema(snap, covered) for snap in snapshots]
    totals = _totals(session, snapshots)
    return CollectionControlResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        source="live",
        folders=folders,
        totals=totals,
    )


def _system_first(
    snapshots: tuple[SymbolSubscriptionFolderSnapshot, ...],
) -> tuple[SymbolSubscriptionFolderSnapshot, ...]:
    return tuple(
        sorted(snapshots, key=lambda s: (not s.is_system, s.sort_order, s.name.lower()))
    )


def _folder_schema(
    snap: SymbolSubscriptionFolderSnapshot, covered: set[str]
) -> CollectionFolder:
    return CollectionFolder(
        id=str(snap.id),
        name=snap.name,
        description=snap.description,
        sort_order=snap.sort_order,
        is_system=snap.is_system,
        is_active=snap.is_active,
        track_market=snap.track_market,
        track_indicators=snap.track_indicators,
        track_news=snap.track_news,
        member_count=len(snap.members),
        covered_member_count=sum(1 for m in snap.members if m.ticker in covered),
        members=[
            CollectionFolderMember(ticker=m.ticker, name=m.name) for m in snap.members
        ],
    )


def _totals(
    session, snapshots: tuple[SymbolSubscriptionFolderSnapshot, ...]
) -> CollectionTotals:
    market = build_watchlist_refresh_policy(session, collection_type="market")
    indicators = build_watchlist_refresh_policy(session, collection_type="indicator")
    news = build_watchlist_refresh_policy(session, collection_type="news")
    return CollectionTotals(
        folder_count=len(snapshots),
        active_folder_count=sum(1 for s in snapshots if s.is_active),
        market_ticker_count=len(market.tickers),
        indicator_ticker_count=len(indicators.tickers),
        news_ticker_count=len(news.tickers),
        all_active=all(s.is_active for s in snapshots) if snapshots else True,
        market_all=all(s.track_market for s in snapshots) if snapshots else True,
        indicators_all=(
            all(s.track_indicators for s in snapshots) if snapshots else True
        ),
        news_all=all(s.track_news for s in snapshots) if snapshots else True,
    )


def _db_unavailable_response() -> CollectionControlResponse:
    return CollectionControlResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        system_status=SystemStatus(db="UNAVAILABLE", mode="READ_MODE", guard_count=0),
        source="fixture",
        folders=[],
        totals=CollectionTotals(),
    )
