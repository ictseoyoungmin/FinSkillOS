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


def _seed_two_folders(db_session: Session) -> None:
    subscriptions = SymbolSubscriptionRepository(db_session)
    for ticker in ("NVDA", "TSLA", "AAPL"):
        subscriptions.subscribe(ticker)
    folders = SymbolSubscriptionFolderRepository(db_session)
    core = folders.upsert_folder("Core")
    watch = folders.upsert_folder("Watch")
    folders.add_symbol(core.id, "NVDA")
    folders.add_symbol(core.id, "TSLA")
    folders.add_symbol(watch.id, "AAPL")


def test_collection_type_unions_base_with_flagged_folder_members(
    db_session: Session,
) -> None:
    _seed_two_folders(db_session)

    policy = build_watchlist_refresh_policy(
        db_session,
        base_tickers=("SPY",),
        collection_type="market",
    )

    assert policy.collection_type == "market"
    assert policy.scope == "collection:market"
    assert set(policy.tickers) == {"SPY", "NVDA", "TSLA", "AAPL"}


def test_collection_type_excludes_inactive_folders(db_session: Session) -> None:
    _seed_two_folders(db_session)
    folders = SymbolSubscriptionFolderRepository(db_session)
    watch = folders.get_by_name("Watch")
    assert watch is not None
    folders.set_collection_flags(watch.id, is_active=False)

    policy = build_watchlist_refresh_policy(
        db_session, collection_type="market"
    )

    # AAPL lived only in the now-inactive Watch folder.
    assert set(policy.tickers) == {"NVDA", "TSLA"}


def test_collection_type_respects_per_type_flag(db_session: Session) -> None:
    _seed_two_folders(db_session)
    folders = SymbolSubscriptionFolderRepository(db_session)
    core = folders.get_by_name("Core")
    assert core is not None
    folders.set_collection_flags(core.id, track_news=False)

    market = build_watchlist_refresh_policy(db_session, collection_type="market")
    news = build_watchlist_refresh_policy(db_session, collection_type="news")

    assert set(market.tickers) == {"NVDA", "TSLA", "AAPL"}
    # Core opted out of news, so only the Watch folder's AAPL is collected.
    assert set(news.tickers) == {"AAPL"}


def test_collection_type_empty_when_no_active_folders(db_session: Session) -> None:
    # No folders at all → only base tickers (System folder not seeded yet).
    policy = build_watchlist_refresh_policy(
        db_session, base_tickers=("SPY",), collection_type="indicator"
    )
    assert policy.tickers == ("SPY",)
    assert policy.folder_tickers == ()
