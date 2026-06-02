"""Folder models for organizing symbol subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base

# Default System folder (Slice W-1) — seeded with install-default sector leaders.
SYSTEM_FOLDER_NAME = "System"


class SymbolSubscriptionFolder(Base):
    __tablename__ = "symbol_subscription_folders"
    __table_args__ = (
        UniqueConstraint("name", name="uq_symbol_subscription_folders_name"),
        Index("idx_symbol_subscription_folders_sort", "sort_order", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(240))
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # Collection control (Slice W-1): per-folder toggles. A ticker's effective
    # collection is the union over its active folders' enabled types.
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=func.true(), nullable=False
    )
    track_market: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=func.true(), nullable=False
    )
    track_indicators: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=func.true(), nullable=False
    )
    track_news: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=func.true(), nullable=False
    )
    # Protected System folder: cannot be deleted; flags still toggle.
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=func.false(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SymbolSubscriptionFolderMembership(Base):
    __tablename__ = "symbol_subscription_folder_memberships"
    __table_args__ = (
        UniqueConstraint(
            "folder_id",
            "subscription_id",
            name="uq_symbol_subscription_folder_membership",
        ),
        Index(
            "idx_symbol_subscription_folder_memberships_folder",
            "folder_id",
            "sort_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    folder_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("symbol_subscription_folders.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("symbol_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
