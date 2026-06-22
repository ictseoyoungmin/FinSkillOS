"""SavedStrategyRepository — persist / list / delete saved Quant Lab specs."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models.saved_strategy import SavedStrategy


class SavedStrategyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, name: str, ticker: str, spec: dict) -> SavedStrategy:
        row = SavedStrategy(name=name, ticker=ticker.upper(), spec=spec)
        self.session.add(row)
        self.session.flush()
        return row

    def list_all(self, limit: int = 100) -> list[SavedStrategy]:
        stmt = (
            select(SavedStrategy)
            .order_by(SavedStrategy.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def get(self, spec_id: uuid.UUID) -> SavedStrategy | None:
        return self.session.get(SavedStrategy, spec_id)

    def delete(self, spec_id: uuid.UUID) -> bool:
        row = self.get(spec_id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True
