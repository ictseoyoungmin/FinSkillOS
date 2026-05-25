"""Repository for user-managed symbol subscriptions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import SymbolSubscription


class SymbolSubscriptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, ticker: str) -> SymbolSubscription | None:
        stmt = select(SymbolSubscription).where(
            SymbolSubscription.ticker == ticker.upper()
        )
        return self.session.scalars(stmt).one_or_none()

    def subscribe(
        self,
        ticker: str,
        *,
        name: str | None = None,
        source: str = "user",
    ) -> SymbolSubscription:
        normalized = ticker.upper()
        row = self.get(normalized)
        if row is None:
            row = SymbolSubscription(
                ticker=normalized,
                name=name or normalized,
                active=True,
                source=source,
            )
            self.session.add(row)
        else:
            row.active = True
            row.name = name or row.name or normalized
            row.source = source
        self.session.flush()
        return row

    def unsubscribe(self, ticker: str) -> SymbolSubscription:
        row = self.get(ticker)
        if row is None:
            row = SymbolSubscription(
                ticker=ticker.upper(),
                name=ticker.upper(),
                active=False,
                source="user",
            )
            self.session.add(row)
        else:
            row.active = False
        self.session.flush()
        return row

    def list_active(self) -> list[SymbolSubscription]:
        stmt = (
            select(SymbolSubscription)
            .where(SymbolSubscription.active.is_(True))
            .order_by(SymbolSubscription.ticker)
        )
        return list(self.session.scalars(stmt))

    def active_tickers(self) -> tuple[str, ...]:
        return tuple(row.ticker for row in self.list_active())
