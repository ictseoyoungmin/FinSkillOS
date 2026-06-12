"""Brokerage → DB portfolio sync — v4 Phase 14 (auto, source-of-truth).

Reads holdings + cash from a read-only brokerage (Toss) and **replaces** the
recorded portfolio + snapshot baseline so the broker is the single source of
truth (stale tickers from earlier manual imports are removed). USD positions are
converted to KRW. The broker side is read-only — there is no order placement —
so this can run unattended (the user opted into automatic daily sync).
"""

from __future__ import annotations

import hashlib
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


def _dec(value) -> Decimal | None:
    """Parse a decimal without any FX conversion (native units)."""

    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def sync_toss_trades(
    session,
    *,
    adapter: BrokerageReadAdapter | None = None,
    replace: bool = False,
) -> dict:
    """Import executed Toss orders (CLOSED) into the trade journal, idempotently.

    Each order is keyed by ``event_key="toss:{orderId}"`` so re-runs add only new
    fills. ``price`` is stored in the trade's **native** currency (USD for US
    tickers, KRW for KR) alongside a ``currency`` marker so realized P&L can be
    summed exactly per currency; ``amount`` stays KRW for the journal's cashflow
    views. Returns a summary; ``SKIPPED`` when Toss is unconfigured,
    ``PENDING_TOSS`` when Toss has not yet enabled CLOSED queries (the live
    ``closed-not-supported`` gate).

    ``replace=True`` deletes the existing Toss-imported trades first (in the same
    transaction, so a failure rolls back with no loss) and re-imports them — used
    once to backfill native price + currency onto the legacy KRW-converted rows.
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
    toss_trades = [
        t
        for t in repo.list_for_account(account.id)
        if t.event_key and t.event_key.startswith("toss:")
    ]
    removed = 0
    if replace:
        for trade in toss_trades:
            session.delete(trade)
        removed = len(toss_trades)
        session.flush()
        existing: set = set()
    else:
        existing = {t.event_key for t in toss_trades}
    rate = (
        usd_krw_rate()
        if any(str(r.get("currency", "")).upper() == "USD" for r in records)
        else None
    )
    service = TradeJournalService(session)
    added = skipped = 0
    for record in records:
        order_id = record.get("order_id")
        # Toss orderIds are long opaque tokens (~80 chars); hash to fit the
        # event_key column (varchar 80) while staying stable + unique for dedup.
        event_key = (
            f"toss:{hashlib.sha1(str(order_id).encode()).hexdigest()}"
            if order_id
            else None
        )
        if event_key and event_key in existing:
            skipped += 1
            continue
        try:
            trade_date = date.fromisoformat(str(record.get("trade_date"))[:10])
        except ValueError:
            skipped += 1
            continue
        currency = str(record.get("currency") or "").upper() or None
        service.create_entry(
            TradeJournalInput(
                trade_date=trade_date,
                ticker=str(record.get("ticker") or ""),
                side=str(record.get("side") or "BUY"),
                quantity=_dec(record.get("quantity")),
                # native price (no FX) + currency marker → exact per-currency P&L;
                # amount/fees stay KRW for the journal's cashflow views.
                price=_dec(record.get("price")),
                amount=_to_krw(record.get("amount"), currency, rate),
                currency=currency,
                fees=_to_krw(record.get("fees"), currency, rate),
                notes=f"Imported from Toss ({record.get('order_type')} "
                f"{record.get('status')}).",
                event_key=event_key,
            )
        )
        added += 1
    session.commit()
    return {"status": "APPLIED", "added": added, "skipped": skipped, "removed": removed}
