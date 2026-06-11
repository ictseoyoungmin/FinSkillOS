"""Brokerage → DB portfolio sync — v4 Phase 14 (auto, source-of-truth).

Reads holdings + cash from a read-only brokerage (Toss) and **replaces** the
recorded portfolio + snapshot baseline so the broker is the single source of
truth (stale tickers from earlier manual imports are removed). USD positions are
converted to KRW. The broker side is read-only — there is no order placement —
so this can run unattended (the user opted into automatic daily sync).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from finskillos.agent.fx import usd_krw_rate
from finskillos.agent.ingest import proposal_from_records
from finskillos.brokerage.adapter import BrokerageReadAdapter, build_brokerage_adapter
from finskillos.config import get_settings
from finskillos.db.repositories import (
    AccountRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.services.portfolio_service import PortfolioService, parse_portfolio_csv

__all__ = ["sync_toss_portfolio"]


def _resolve_or_create_account(session):
    accounts = AccountRepository(session)
    settings = get_settings()
    account = accounts.get_by_name(settings.default_account_name)
    if account is None:
        rows = accounts.list_all()
        account = rows[0] if rows else None
    if account is None:
        account = accounts.create(
            name=settings.default_account_name,
            target_value=settings.target_value,
            base_currency=settings.base_currency,
        )
    return account


def sync_toss_portfolio(
    session, *, adapter: BrokerageReadAdapter | None = None
) -> dict:
    """Replace the portfolio + baseline from the Toss source of truth.

    Returns a summary dict; ``status="SKIPPED"`` (no mutation) when Toss is not
    configured. Caller commits via the session scope.
    """

    adapter = adapter or build_brokerage_adapter("toss")
    if not adapter.available():
        return {"status": "SKIPPED", "reason": "toss_not_configured"}

    records = adapter.fetch_positions()
    rate = (
        usd_krw_rate()
        if any(str(r.get("currency", "")).upper() == "USD" for r in records)
        else None
    )
    proposal = proposal_from_records(records, usd_krw_rate=rate)
    rows = parse_portfolio_csv(proposal.normalized_csv) if proposal.rows else []

    account = _resolve_or_create_account(session)

    # Cash: prefer the live broker figure; keep the existing baseline cash on miss.
    cash = None
    fetch_cash = getattr(adapter, "fetch_cash", None)
    if callable(fetch_cash):
        cash = fetch_cash(rate)
    if cash is None:
        latest = PortfolioRepository(session).latest(account.id)
        cash = latest.cash_value if latest is not None else Decimal("0")

    # Replace — the broker is authoritative, so drop tickers it no longer reports.
    PositionRepository(session).delete_all_for_account(account.id)
    service = PortfolioService(session)
    for row in rows:
        service.upsert_position(account_id=account.id, row=row)

    positions_total = sum((row.market_value for row in rows), Decimal("0"))
    total = positions_total + (cash or Decimal("0"))
    PortfolioRepository(session).update_latest_baseline(
        account.id,
        snapshot_date=datetime.now(tz=timezone.utc).date(),
        total_value=total,
        cash_value=cash,
    )
    session.commit()
    return {
        "status": "APPLIED",
        "positions": len(rows),
        "cash": str(cash),
        "total": str(total),
        "warnings": proposal.warnings,
    }
