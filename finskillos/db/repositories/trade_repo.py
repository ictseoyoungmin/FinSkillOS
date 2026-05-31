"""TradeRepository — Slice-02 CRUD extended with Slice-12 reflection filters.

The Slice-02 ``create`` signature is preserved so existing tests
(``tests/unit/test_repositories.py``) keep passing. Slice 12 adds the
reflection fields (thesis / result_pnl / mistake_tags / notes /
sector / theme / event_key) plus filtered list helpers that the
``ReflectionService`` consumes.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import Trade

_UNSET: object = object()


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_ticker(ticker: str | None) -> str | None:
    cleaned = _empty_to_none(ticker)
    return cleaned.upper() if cleaned else None


def _coerce_mistake_tags(value: Sequence[str] | list[str] | None) -> list[str] | None:
    if value is None:
        return None
    cleaned = [tag.strip() for tag in value if isinstance(tag, str) and tag.strip()]
    return cleaned if cleaned else None


class TradeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        account_id: uuid.UUID,
        ticker: str,
        trade_date: date,
        side: str,
        quantity: Decimal = Decimal("0"),
        price: Decimal = Decimal("0"),
        amount: Decimal = Decimal("0"),
        strategy_type: str = "swing",
        fees: Decimal | None = None,
        reason: str | None = None,
        thesis: str | None = None,
        catalyst: str | None = None,
        emotion_state: str | None = None,
        market_regime: str | None = None,
        mistake_tag: str | None = None,
        mistake_tags: Sequence[str] | None = None,
        result_pnl: Decimal | None = None,
        result_pnl_pct: Decimal | None = None,
        r_multiple: Decimal | None = None,
        notes: str | None = None,
        sector: str | None = None,
        theme: str | None = None,
        event_key: str | None = None,
    ) -> Trade:
        trade = Trade(
            account_id=account_id,
            ticker=_normalize_ticker(ticker) or "",
            trade_date=trade_date,
            side=side,
            quantity=quantity,
            price=price,
            amount=amount,
            strategy_type=strategy_type,
            fees=fees,
            reason=reason,
            thesis=thesis,
            catalyst=catalyst,
            emotion_state=emotion_state,
            market_regime=market_regime,
            mistake_tag=mistake_tag,
            mistake_tags=_coerce_mistake_tags(mistake_tags),
            result_pnl=result_pnl,
            result_pnl_pct=result_pnl_pct,
            r_multiple=r_multiple,
            notes=notes,
            sector=_empty_to_none(sector),
            theme=_empty_to_none(theme),
            event_key=_empty_to_none(event_key),
        )
        self.session.add(trade)
        self.session.flush()
        return trade

    def update(
        self,
        trade_id: uuid.UUID,
        *,
        ticker: str | None = None,
        trade_date: date | None = None,
        side: str | None = None,
        quantity: Decimal | None = None,
        price: Decimal | None = None,
        amount: Decimal | None = None,
        strategy_type: str | None = None,
        fees: Decimal | None | object = _UNSET,
        reason: str | None | object = _UNSET,
        thesis: str | None | object = _UNSET,
        catalyst: str | None | object = _UNSET,
        emotion_state: str | None | object = _UNSET,
        market_regime: str | None | object = _UNSET,
        mistake_tag: str | None | object = _UNSET,
        mistake_tags: Sequence[str] | None | object = _UNSET,
        result_pnl: Decimal | None | object = _UNSET,
        result_pnl_pct: Decimal | None | object = _UNSET,
        r_multiple: Decimal | None | object = _UNSET,
        notes: str | None | object = _UNSET,
        sector: str | None | object = _UNSET,
        theme: str | None | object = _UNSET,
        event_key: str | None | object = _UNSET,
    ) -> Trade:
        """Partial / explicit update.

        Non-null required columns keep "pass ``None`` to skip"; nullable
        reflection fields use ``_UNSET`` so ``None`` explicitly clears
        them. This mirrors the Slice-11 event-update sentinel pattern.
        """

        trade = self.session.get(Trade, trade_id)
        if trade is None:
            raise LookupError(f"Trade {trade_id} not found")
        if ticker is not None:
            normalized = _normalize_ticker(ticker)
            if normalized is not None:
                trade.ticker = normalized
        if trade_date is not None:
            trade.trade_date = trade_date
        if side is not None:
            trade.side = side
        if quantity is not None:
            trade.quantity = quantity
        if price is not None:
            trade.price = price
        if amount is not None:
            trade.amount = amount
        if strategy_type is not None:
            trade.strategy_type = strategy_type
        if fees is not _UNSET:
            trade.fees = fees  # type: ignore[assignment]
        if reason is not _UNSET:
            trade.reason = reason  # type: ignore[assignment]
        if thesis is not _UNSET:
            trade.thesis = thesis  # type: ignore[assignment]
        if catalyst is not _UNSET:
            trade.catalyst = catalyst  # type: ignore[assignment]
        if emotion_state is not _UNSET:
            trade.emotion_state = emotion_state  # type: ignore[assignment]
        if market_regime is not _UNSET:
            trade.market_regime = market_regime  # type: ignore[assignment]
        if mistake_tag is not _UNSET:
            trade.mistake_tag = mistake_tag  # type: ignore[assignment]
        if mistake_tags is not _UNSET:
            trade.mistake_tags = _coerce_mistake_tags(
                mistake_tags  # type: ignore[arg-type]
            )
        if result_pnl is not _UNSET:
            trade.result_pnl = result_pnl  # type: ignore[assignment]
        if result_pnl_pct is not _UNSET:
            trade.result_pnl_pct = result_pnl_pct  # type: ignore[assignment]
        if r_multiple is not _UNSET:
            trade.r_multiple = r_multiple  # type: ignore[assignment]
        if notes is not _UNSET:
            trade.notes = notes  # type: ignore[assignment]
        if sector is not _UNSET:
            trade.sector = _empty_to_none(sector)  # type: ignore[arg-type]
        if theme is not _UNSET:
            trade.theme = _empty_to_none(theme)  # type: ignore[arg-type]
        if event_key is not _UNSET:
            trade.event_key = _empty_to_none(event_key)  # type: ignore[arg-type]
        self.session.flush()
        return trade

    def delete(self, trade_id: uuid.UUID) -> None:
        """Remove one trade row. Raises ``LookupError`` if absent."""

        trade = self.session.get(Trade, trade_id)
        if trade is None:
            raise LookupError(f"Trade {trade_id} not found")
        self.session.delete(trade)
        self.session.flush()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get(self, trade_id: uuid.UUID) -> Trade | None:
        return self.session.get(Trade, trade_id)

    def list_for_account(
        self,
        account_id: uuid.UUID,
        *,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Trade]:
        stmt = select(Trade).where(Trade.account_id == account_id)
        if start is not None:
            stmt = stmt.where(Trade.trade_date >= start)
        if end is not None:
            stmt = stmt.where(Trade.trade_date <= end)
        stmt = stmt.order_by(Trade.trade_date, Trade.created_at)
        return list(self.session.scalars(stmt))

    def list_recent(
        self,
        account_id: uuid.UUID,
        *,
        limit: int = 20,
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .where(Trade.account_id == account_id)
            .order_by(Trade.trade_date.desc(), Trade.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_by_ticker(
        self,
        account_id: uuid.UUID,
        ticker: str,
    ) -> list[Trade]:
        upper = _normalize_ticker(ticker)
        if upper is None:
            return []
        stmt = (
            select(Trade)
            .where(
                Trade.account_id == account_id,
                Trade.ticker == upper,
            )
            .order_by(Trade.trade_date)
        )
        return list(self.session.scalars(stmt))

    def list_by_date_range(
        self,
        account_id: uuid.UUID,
        *,
        start: date,
        end: date,
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .where(
                Trade.account_id == account_id,
                Trade.trade_date >= start,
                Trade.trade_date <= end,
            )
            .order_by(Trade.trade_date)
        )
        return list(self.session.scalars(stmt))

    def list_by_regime(
        self,
        account_id: uuid.UUID,
        regime: str,
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .where(
                Trade.account_id == account_id,
                Trade.market_regime == regime,
            )
            .order_by(Trade.trade_date)
        )
        return list(self.session.scalars(stmt))

    def list_by_strategy_type(
        self,
        account_id: uuid.UUID,
        strategy_type: str,
    ) -> list[Trade]:
        stmt = (
            select(Trade)
            .where(
                Trade.account_id == account_id,
                Trade.strategy_type == strategy_type,
            )
            .order_by(Trade.trade_date)
        )
        return list(self.session.scalars(stmt))

    def list_by_mistake_tag(
        self,
        account_id: uuid.UUID,
        tag: str,
    ) -> list[Trade]:
        """Match either the legacy ``mistake_tag`` column or any value
        in the new ``mistake_tags`` JSON list. JSON membership tests
        run in Python because the SQLite test DB does not implement
        JSON containment operators.
        """

        if not tag:
            return []
        rows = self.list_for_account(account_id)
        matched: list[Trade] = []
        for row in rows:
            if row.mistake_tag == tag:
                matched.append(row)
                continue
            tags = row.mistake_tags or []
            if isinstance(tags, list) and tag in tags:
                matched.append(row)
        return matched
