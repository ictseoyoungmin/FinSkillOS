"""Watchlist folder refresh policy tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.services.watchlist_refresh_policy import (
    build_watchlist_refresh_policy,
)


def test_watchlist_refresh_policy_defaults_to_all_active_subscriptions(
    db_session: Session,
) -> None:
    subscriptions = SymbolSubscriptionRepository(db_session)
    subscriptions.subscribe("NVDA", name="NVIDIA")
    subscriptions.subscribe("TSLA", name="Tesla")

    policy = build_watchlist_refresh_policy(db_session, base_tickers=("SPY",))

    assert policy.scope == "all_active"
    assert policy.tickers == ("SPY", "NVDA", "TSLA")
    assert policy.folder_tickers == ()


def test_watchlist_refresh_policy_scopes_to_named_folder(
    db_session: Session,
) -> None:
    subscriptions = SymbolSubscriptionRepository(db_session)
    subscriptions.subscribe("NVDA", name="NVIDIA")
    subscriptions.subscribe("TSLA", name="Tesla")
    subscriptions.subscribe("MSFT", name="Microsoft")
    folders = SymbolSubscriptionFolderRepository(db_session)
    ai = folders.upsert_folder("AI Leaders")
    ev = folders.upsert_folder("EV")
    folders.add_symbol(ai.id, "NVDA")
    folders.add_symbol(ai.id, "MSFT")
    folders.add_symbol(ev.id, "TSLA")

    policy = build_watchlist_refresh_policy(
        db_session,
        base_tickers=("SPY", "NVDA"),
        folder_names=("AI Leaders",),
    )

    assert policy.scope == "folder"
    assert policy.folder_names == ("AI Leaders",)
    assert policy.folder_tickers == ("MSFT", "NVDA")
    assert policy.tickers == ("SPY", "NVDA", "MSFT")


def test_watchlist_refresh_policy_falls_back_when_folder_has_no_members(
    db_session: Session,
) -> None:
    subscriptions = SymbolSubscriptionRepository(db_session)
    subscriptions.subscribe("NVDA", name="NVIDIA")
    SymbolSubscriptionFolderRepository(db_session).upsert_folder("Empty")

    policy = build_watchlist_refresh_policy(
        db_session,
        base_tickers=("SPY",),
        folder_names=("Empty",),
    )

    assert policy.scope == "all_active"
    assert policy.tickers == ("SPY", "NVDA")
