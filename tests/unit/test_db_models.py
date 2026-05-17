"""Slice 02 — DB model tests.

Validates the SQLAlchemy mappings against an in-memory SQLite DB:
* table creation via `Base.metadata.create_all`
* portfolio_snapshots uniqueness on (account_id, snapshot_date)
* positions uniqueness on (account_id, ticker)
* alerts.payload round-trips structured JSON
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from finskillos.db.models import Account, Alert, PortfolioSnapshot, Position, Trade


def _make_account(session: Session, name: str = "Main Trading Account") -> Account:
    account = Account(
        name=name,
        base_currency="KRW",
        target_value=Decimal("100000000"),
    )
    session.add(account)
    session.flush()
    return account


def test_account_persists_with_uuid_pk(db_session: Session) -> None:
    account = _make_account(db_session)

    assert isinstance(account.id, uuid.UUID)
    assert account.base_currency == "KRW"
    assert account.target_value == Decimal("100000000")


def test_portfolio_snapshot_uniqueness(db_session: Session) -> None:
    account = _make_account(db_session)
    snap = PortfolioSnapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 17),
        total_value=Decimal("57000000"),
        cash_value=Decimal("7000000"),
    )
    db_session.add(snap)
    db_session.flush()

    dup = PortfolioSnapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 17),
        total_value=Decimal("57500000"),
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_positions_unique_per_account_ticker(db_session: Session) -> None:
    account = _make_account(db_session)
    db_session.add(
        Position(
            account_id=account.id,
            ticker="TSLA",
            quantity=Decimal("10"),
            market_value=Decimal("3000000"),
        )
    )
    db_session.flush()

    db_session.add(
        Position(
            account_id=account.id,
            ticker="TSLA",
            quantity=Decimal("5"),
            market_value=Decimal("1500000"),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_alert_round_trips_json_payload(db_session: Session) -> None:
    account = _make_account(db_session)
    payload = {
        "guard": "MAX_SINGLE_POSITION_VALUE",
        "ticker": "TSLA",
        "observed": "11000000",
        "limit": "10000000",
        "affected_positions": ["TSLA"],
    }
    alert = Alert(
        account_id=account.id,
        alert_date=date(2026, 5, 17),
        guard_name="MAX_SINGLE_POSITION_VALUE",
        severity="YELLOW",
        title="단일 종목 한도 초과",
        message="TSLA 평가금액이 1천만원 한도를 초과했습니다.",
        payload=payload,
    )
    db_session.add(alert)
    db_session.flush()

    db_session.expire_all()
    reloaded = db_session.get(Alert, alert.id)
    assert reloaded is not None
    assert reloaded.resolved is False
    assert reloaded.payload == payload
    assert reloaded.payload["affected_positions"] == ["TSLA"]


def test_trade_required_fields_persist(db_session: Session) -> None:
    account = _make_account(db_session)
    trade = Trade(
        account_id=account.id,
        ticker="NVDA",
        trade_date=date(2026, 5, 12),
        side="BUY",
        quantity=Decimal("3"),
        price=Decimal("950.55"),
        amount=Decimal("2851.65"),
        reason="AI capex thesis",
        market_regime="RISK_ON",
    )
    db_session.add(trade)
    db_session.flush()

    db_session.expire_all()
    reloaded = db_session.get(Trade, trade.id)
    assert reloaded is not None
    assert reloaded.side == "BUY"
    assert reloaded.market_regime == "RISK_ON"
    assert reloaded.strategy_type == "swing"  # server default
