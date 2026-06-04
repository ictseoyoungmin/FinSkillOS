"""PositionRepository — CRUD over live holdings."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import Position


class PositionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        account_id: uuid.UUID,
        ticker: str,
        quantity: Decimal,
        market_value: Decimal,
        sector: str | None = None,
        theme: str | None = None,
        strategy_type: str = "swing",
        average_cost: Decimal | None = None,
        pnl_pct: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        thesis: str | None = None,
    ) -> Position:
        position = Position(
            account_id=account_id,
            ticker=ticker,
            sector=sector,
            theme=theme,
            strategy_type=strategy_type,
            quantity=quantity,
            average_cost=average_cost,
            market_value=market_value,
            pnl_pct=pnl_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            thesis=thesis,
        )
        self.session.add(position)
        self.session.flush()
        return position

    def get(self, position_id: uuid.UUID) -> Position | None:
        return self.session.get(Position, position_id)

    def get_by_account_and_ticker(
        self, account_id: uuid.UUID, ticker: str
    ) -> Position | None:
        stmt = select(Position).where(
            Position.account_id == account_id, Position.ticker == ticker
        )
        return self.session.scalars(stmt).one_or_none()

    def list_for_account(self, account_id: uuid.UUID) -> list[Position]:
        stmt = (
            select(Position)
            .where(Position.account_id == account_id)
            .order_by(Position.ticker)
        )
        return list(self.session.scalars(stmt))

    def update_market_value(
        self, position_id: uuid.UUID, market_value: Decimal, pnl_pct: Decimal | None = None
    ) -> Position:
        position = self.session.get(Position, position_id)
        if position is None:
            raise LookupError(f"Position {position_id} not found")
        position.market_value = market_value
        if pnl_pct is not None:
            position.pnl_pct = pnl_pct
        self.session.flush()
        return position

    def update(
        self,
        position_id: uuid.UUID,
        *,
        ticker: str,
        quantity: Decimal,
        market_value: Decimal,
        sector: str | None = None,
        theme: str | None = None,
        strategy_type: str = "swing",
        average_cost: Decimal | None = None,
        thesis: str | None = None,
    ) -> Position:
        """Full-field update of an editable holding (Slice 158)."""
        position = self.session.get(Position, position_id)
        if position is None:
            raise LookupError(f"Position {position_id} not found")
        position.ticker = ticker
        position.quantity = quantity
        position.market_value = market_value
        position.sector = sector
        position.theme = theme
        position.strategy_type = strategy_type
        position.average_cost = average_cost
        position.thesis = thesis
        self.session.flush()
        return position

    def delete(self, position_id: uuid.UUID) -> None:
        position = self.session.get(Position, position_id)
        if position is not None:
            self.session.delete(position)
            self.session.flush()

    def delete_all_for_account(self, account_id: uuid.UUID) -> int:
        """Delete every holding for an account (the "Clear sample" action)."""
        positions = self.list_for_account(account_id)
        for position in positions:
            self.session.delete(position)
        if positions:
            self.session.flush()
        return len(positions)
