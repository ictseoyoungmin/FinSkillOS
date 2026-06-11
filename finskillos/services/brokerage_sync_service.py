"""Brokerage → DB portfolio sync — v4 Phase 14 (auto, source-of-truth).

Reads holdings + cash from a read-only brokerage (Toss) and **replaces** the
recorded portfolio + snapshot baseline so the broker is the single source of
truth (stale tickers from earlier manual imports are removed). USD positions are
converted to KRW. The broker side is read-only — there is no order placement —
so this can run unattended (the user opted into automatic daily sync).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from finskillos.agent.fx import usd_krw_rate
from finskillos.agent.ingest import proposal_from_records
from finskillos.brokerage.adapter import BrokerageReadAdapter, build_brokerage_adapter
from finskillos.brokerage.toss.client import TossApiError
from finskillos.config import get_settings
from finskillos.db.repositories import (
    AccountRepository,
    PortfolioRepository,
    PositionRepository,
    TradeRepository,
)
from finskillos.services.portfolio_service import PortfolioService, parse_portfolio_csv
from finskillos.services.trade_journal_service import (
    TradeJournalInput,
    TradeJournalService,
)

__all__ = ["sync_toss_portfolio", "sync_toss_trades"]


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


def _to_krw(value, currency, rate) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if str(currency).upper() == "USD" and rate is not None:
        amount = amount * Decimal(str(rate))
    return amount


def sync_toss_trades(session, *, adapter: BrokerageReadAdapter | None = None) -> dict:
    """Import executed Toss orders (CLOSED) into the trade journal, idempotently.

    Each order is keyed by ``event_key="toss:{orderId}"`` so re-runs add only new
    fills. USD trades convert to KRW. Returns a summary; ``SKIPPED`` when Toss is
    unconfigured, ``PENDING_TOSS`` when Toss has not yet enabled CLOSED queries
    (the live ``closed-not-supported`` gate).
    """

    adapter = adapter or build_brokerage_adapter("toss")
    if not adapter.available():
        return {"status": "SKIPPED", "reason": "toss_not_configured"}
    try:
        records = adapter.fetch_trades()
    except TossApiError as exc:
        code = ""
        if isinstance(exc.payload, dict):
            code = str(exc.payload.get("error", {}).get("code", ""))
        if exc.status == 400 and code == "closed-not-supported":
            return {"status": "PENDING_TOSS", "reason": "closed-not-supported"}
        raise

    account = _resolve_or_create_account(session)
    repo = TradeRepository(session)
    existing = {
        t.event_key
        for t in repo.list_for_account(account.id)
        if t.event_key and t.event_key.startswith("toss:")
    }
    rate = (
        usd_krw_rate()
        if any(str(r.get("currency", "")).upper() == "USD" for r in records)
        else None
    )
    service = TradeJournalService(session)
    added = skipped = 0
    for record in records:
        order_id = record.get("order_id")
        event_key = f"toss:{order_id}" if order_id else None
        if event_key and event_key in existing:
            skipped += 1
            continue
        try:
            trade_date = date.fromisoformat(str(record.get("trade_date"))[:10])
        except ValueError:
            skipped += 1
            continue
        currency = record.get("currency")
        service.create_entry(
            TradeJournalInput(
                trade_date=trade_date,
                ticker=str(record.get("ticker") or ""),
                side=str(record.get("side") or "BUY"),
                quantity=_to_krw(record.get("quantity"), "KRW", None),
                price=_to_krw(record.get("price"), currency, rate),
                amount=_to_krw(record.get("amount"), currency, rate),
                fees=_to_krw(record.get("fees"), currency, rate),
                notes=f"Imported from Toss ({record.get('order_type')} "
                f"{record.get('status')}).",
                event_key=event_key,
            )
        )
        added += 1
    session.commit()
    return {"status": "APPLIED", "added": added, "skipped": skipped}
