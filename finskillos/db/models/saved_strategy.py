"""SavedStrategy model — persisted agent-authored / custom quant specs (Slice 333).

A saved Quant Lab strategy: the validated free-form spec JSON (name / ticker /
entry / exit condition trees) so a designed hypothesis can be re-run later. JSON
column uses the cross-dialect variant (JSONB on Postgres, JSON on SQLite).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Index, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base

JSONPayload = JSON().with_variant(JSONB(), "postgresql")


class SavedStrategy(Base):
    __tablename__ = "saved_strategies"
    __table_args__ = (
        Index("idx_saved_strategies_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    spec: Mapped[dict] = mapped_column(JSONPayload, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
