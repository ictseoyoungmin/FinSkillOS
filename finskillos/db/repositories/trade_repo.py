"""TradeRepository — append/query trade journal entries."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import Trade


class TradeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        account_id: uuid.UUID,
        ticker: str,
        trade_date: date,
        side: str,
        quantity: Decimal,
        price: Decimal,
        amount: Decimal,
        strategy_type: str = "swing",
        fees: Decimal | None = None,
        reason: str | None = None,
        catalyst: str | None = None,
        emotion_state: str | None = None,
        market_regime: str | None = None,
        mistake_tag: str | None = None,
    ) -> Trade:
        trade = Trade(
            account_id=account_id,
            ticker=ticker,
            trade_date=trade_date,
            side=side,
            quantity=quantity,
            price=price,
            amount=amount,
            strategy_type=strategy_type,
            fees=fees,
            reason=reason,
            catalyst=catalyst,
            emotion_state=emotion_state,
            market_regime=market_regime,
            mistake_tag=mistake_tag,
        )
        self.session.add(trade)
        self.session.flush()
        return trade

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
