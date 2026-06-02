"""Folder collection-control flags + System-folder seed tests (Slice W-1)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.data_sources import DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.models import SYSTEM_FOLDER_NAME
from finskillos.db.repositories import (
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.db.seed import seed_system_folder


def test_new_folder_defaults_to_all_collection_types_on(
    db_session: Session,
) -> None:
    folders = SymbolSubscriptionFolderRepository(db_session)
    folder = folders.upsert_folder("AI Leaders")

    assert folder.is_active is True
    assert folder.track_market is True
    assert folder.track_indicators is True
    assert folder.track_news is True
    assert folder.is_system is False


def test_set_collection_flags_partial_update_leaves_unset_flags(
    db_session: Session,
) -> None:
    folders = SymbolSubscriptionFolderRepository(db_session)
    folder = folders.upsert_folder("Watchlist")

    folders.set_collection_flags(folder.id, track_news=False)

    refreshed = folders.get(folder.id)
    assert refreshed is not None
    assert refreshed.track_news is False
    # Untouched flags remain on.
    assert refreshed.is_active is True
    assert refreshed.track_market is True
    assert refreshed.track_indicators is True


def test_set_collection_flags_unknown_folder_raises(db_session: Session) -> None:
    import uuid

    folders = SymbolSubscriptionFolderRepository(db_session)
    try:
        folders.set_collection_flags(uuid.uuid4(), is_active=False)
    except ValueError as exc:
        assert str(exc) == "folder_not_found"
    else:  # pragma: no cover - guard
        raise AssertionError("expected folder_not_found")


def test_ensure_system_folder_is_idempotent_and_protected(
    db_session: Session,
) -> None:
    folders = SymbolSubscriptionFolderRepository(db_session)

    first = folders.ensure_system_folder()
    second = folders.ensure_system_folder()

    assert first.id == second.id
    assert first.name == SYSTEM_FOLDER_NAME
    assert first.is_system is True


def test_ensure_system_folder_preserves_operator_flags(
    db_session: Session,
) -> None:
    folders = SymbolSubscriptionFolderRepository(db_session)
    folder = folders.ensure_system_folder()
    folders.set_collection_flags(folder.id, track_news=False)

    # Re-running must not reset the operator's news toggle.
    folders.ensure_system_folder()

    refreshed = folders.get(folder.id)
    assert refreshed is not None
    assert refreshed.track_news is False
    assert refreshed.is_system is True


def test_seed_system_folder_registers_default_universe(
    db_session: Session,
) -> None:
    result = seed_system_folder(db_session)

    assert result.created_folder is True
    assert result.members == len(DEFAULT_US_TICKER_UNIVERSE)
    assert result.subscribed == len(DEFAULT_US_TICKER_UNIVERSE)
    assert result.linked == len(DEFAULT_US_TICKER_UNIVERSE)

    folders = SymbolSubscriptionFolderRepository(db_session)
    snapshot = next(
        snap for snap in folders.list_snapshots() if snap.name == SYSTEM_FOLDER_NAME
    )
    assert snapshot.is_system is True
    member_tickers = {member.ticker for member in snapshot.members}
    assert member_tickers == set(DEFAULT_US_TICKER_UNIVERSE)

    subscriptions = SymbolSubscriptionRepository(db_session)
    assert set(subscriptions.active_tickers()) >= set(DEFAULT_US_TICKER_UNIVERSE)


def test_seed_system_folder_is_idempotent(db_session: Session) -> None:
    seed_system_folder(db_session)
    second = seed_system_folder(db_session)

    assert second.created_folder is False
    assert second.subscribed == 0
    assert second.linked == 0
    assert second.members == len(DEFAULT_US_TICKER_UNIVERSE)

    folders = SymbolSubscriptionFolderRepository(db_session)
    system_folders = [
        snap
        for snap in folders.list_snapshots()
        if snap.name == SYSTEM_FOLDER_NAME
    ]
    assert len(system_folders) == 1
    assert len(system_folders[0].members) == len(DEFAULT_US_TICKER_UNIVERSE)


def test_list_snapshots_exposes_collection_flags(db_session: Session) -> None:
    folders = SymbolSubscriptionFolderRepository(db_session)
    folder = folders.upsert_folder("Macro")
    folders.set_collection_flags(folder.id, track_indicators=False)

    snapshot = next(
        snap for snap in folders.list_snapshots() if snap.name == "Macro"
    )
    assert snapshot.track_indicators is False
    assert snapshot.track_market is True
    assert snapshot.is_active is True
