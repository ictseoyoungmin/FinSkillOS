"""Holdings → dedicated subscription folder sync (Slice 252). Offline (sqlite)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.db.base import Base
from finskillos.db.repositories import (
    AccountRepository,
    PositionRepository,
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.services.brokerage_sync_service import (
    HOLDINGS_FOLDER_NAME,
    sync_holdings_folder,
)
from finskillos.services.portfolio_service import (
    PortfolioPositionInput,
    PortfolioService,
)


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _seed(session, holdings):
    account = AccountRepository(session).create(name="M", target_value=Decimal("1"))
    svc = PortfolioService(session)
    for ticker, value in holdings:
        svc.upsert_position(
            account_id=account.id,
            row=PortfolioPositionInput(
                ticker=ticker,
                quantity=Decimal("1"),
                market_value=Decimal(value),
                sector="Tech",
            ),
        )
    session.commit()
    return account


def _members(session) -> set[str]:
    folders = SymbolSubscriptionFolderRepository(session)
    snapshot = next(
        s for s in folders.list_snapshots() if s.name == HOLDINGS_FOLDER_NAME
    )
    return {m.ticker.upper() for m in snapshot.members}


def test_sync_holdings_folder_subscribes_and_flags() -> None:
    session = _session()
    _seed(session, [("NVDA", "100"), ("AAPL", "200")])

    result = sync_holdings_folder(session)
    assert result["status"] == "APPLIED"
    assert result["tickers"] == 2 and result["added"] == 2

    assert _members(session) == {"NVDA", "AAPL"}
    folder = SymbolSubscriptionFolderRepository(session).get_by_name(HOLDINGS_FOLDER_NAME)
    # Flags drive the worker's refresh universe (bars + indicators).
    assert folder.is_active and folder.track_market and folder.track_indicators
    active = {s.ticker for s in SymbolSubscriptionRepository(session).list_active()}
    assert {"NVDA", "AAPL"} <= active


def test_sync_holdings_folder_prunes_sold() -> None:
    session = _session()
    account = _seed(session, [("NVDA", "100"), ("AAPL", "200")])
    sync_holdings_folder(session)
    assert _members(session) == {"NVDA", "AAPL"}

    # AAPL is sold → only NVDA remains held.
    PositionRepository(session).delete_all_for_account(account.id)
    PortfolioService(session).upsert_position(
        account_id=account.id,
        row=PortfolioPositionInput(
            ticker="NVDA", quantity=Decimal("1"),
            market_value=Decimal("100"), sector="Tech",
        ),
    )
    session.commit()

    result = sync_holdings_folder(session)
    assert result["removed"] == 1
    assert _members(session) == {"NVDA"}  # AAPL pruned from the refresh universe


def test_sync_holdings_folder_skips_without_account() -> None:
    assert sync_holdings_folder(_session())["status"] == "SKIPPED"
