"""Folder models for organizing symbol subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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
