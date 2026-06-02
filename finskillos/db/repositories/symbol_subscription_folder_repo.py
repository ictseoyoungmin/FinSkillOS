"""Repository for foldered symbol subscription organization."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finskillos.db.models import (
    SYSTEM_FOLDER_NAME,
    SymbolSubscription,
    SymbolSubscriptionFolder,
    SymbolSubscriptionFolderMembership,
)


@dataclass(frozen=True)
class SymbolSubscriptionFolderMember:
    ticker: str
    name: str | None
    subscription_id: uuid.UUID


@dataclass(frozen=True)
class SymbolSubscriptionFolderSnapshot:
    id: uuid.UUID
    name: str
    description: str | None
    sort_order: int
    members: tuple[SymbolSubscriptionFolderMember, ...]
    # Collection-control flags (Slice W-1).
    is_active: bool = True
    track_market: bool = True
    track_indicators: bool = True
    track_news: bool = True
    is_system: bool = False


class SymbolSubscriptionFolderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, folder_id: uuid.UUID) -> SymbolSubscriptionFolder | None:
        stmt = select(SymbolSubscriptionFolder).where(
            SymbolSubscriptionFolder.id == folder_id
        )
        return self.session.scalars(stmt).one_or_none()

    def get_by_name(self, name: str) -> SymbolSubscriptionFolder | None:
        normalized = _normalize_folder_name(name)
        stmt = select(SymbolSubscriptionFolder).where(
            SymbolSubscriptionFolder.name == normalized
        )
        return self.session.scalars(stmt).one_or_none()

    def upsert_folder(
        self,
        name: str,
        *,
        description: str | None = None,
        sort_order: int = 0,
    ) -> SymbolSubscriptionFolder:
        normalized = _normalize_folder_name(name)
        row = self.get_by_name(normalized)
        if row is None:
            row = SymbolSubscriptionFolder(
                name=normalized,
                description=_clean_optional(description),
                sort_order=sort_order,
            )
            self.session.add(row)
        else:
            row.description = _clean_optional(description)
            row.sort_order = sort_order
        self.session.flush()
        return row

    def add_symbol(
        self,
        folder_id: uuid.UUID,
        ticker: str,
        *,
        sort_order: int = 0,
    ) -> SymbolSubscriptionFolderMembership:
        folder = self.get(folder_id)
        if folder is None:
            raise ValueError("folder_not_found")

        subscription = _active_subscription(self.session, ticker)
        if subscription is None:
            raise ValueError("subscription_not_found")

        existing = self._get_membership(folder_id, subscription.id)
        if existing is not None:
            existing.sort_order = sort_order
            self.session.flush()
            return existing

        row = SymbolSubscriptionFolderMembership(
            folder_id=folder_id,
            subscription_id=subscription.id,
            sort_order=sort_order,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def remove_symbol(self, folder_id: uuid.UUID, ticker: str) -> bool:
        subscription = _subscription(self.session, ticker)
        if subscription is None:
            return False
        row = self._get_membership(folder_id, subscription.id)
        if row is None:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    def set_collection_flags(
        self,
        folder_id: uuid.UUID,
        *,
        is_active: bool | None = None,
        track_market: bool | None = None,
        track_indicators: bool | None = None,
        track_news: bool | None = None,
    ) -> SymbolSubscriptionFolder:
        """Partial-update a folder's collection flags. `None` leaves a flag as-is."""
        folder = self.get(folder_id)
        if folder is None:
            raise ValueError("folder_not_found")
        if is_active is not None:
            folder.is_active = is_active
        if track_market is not None:
            folder.track_market = track_market
        if track_indicators is not None:
            folder.track_indicators = track_indicators
        if track_news is not None:
            folder.track_news = track_news
        self.session.flush()
        return folder

    def ensure_system_folder(
        self, *, description: str | None = None
    ) -> SymbolSubscriptionFolder:
        """Get or create the protected System folder (idempotent)."""
        row = self.get_by_name(SYSTEM_FOLDER_NAME)
        if row is None:
            row = SymbolSubscriptionFolder(
                name=SYSTEM_FOLDER_NAME,
                description=_clean_optional(description),
                sort_order=0,
                is_system=True,
            )
            self.session.add(row)
        else:
            # Re-assert protection without disturbing operator-set flags.
            row.is_system = True
            if description is not None and not row.description:
                row.description = _clean_optional(description)
        self.session.flush()
        return row

    def list_snapshots(self) -> tuple[SymbolSubscriptionFolderSnapshot, ...]:
        folders = list(
            self.session.scalars(
                select(SymbolSubscriptionFolder).order_by(
                    SymbolSubscriptionFolder.sort_order,
                    SymbolSubscriptionFolder.name,
                )
            )
        )
        if not folders:
            return ()

        memberships = list(
            self.session.execute(
                select(
                    SymbolSubscriptionFolderMembership.folder_id,
                    SymbolSubscription.ticker,
                    SymbolSubscription.name,
                    SymbolSubscription.id,
                )
                .join(
                    SymbolSubscription,
                    SymbolSubscription.id
                    == SymbolSubscriptionFolderMembership.subscription_id,
                )
                .where(SymbolSubscription.active.is_(True))
                .order_by(
                    SymbolSubscriptionFolderMembership.sort_order,
                    SymbolSubscription.ticker,
                )
            )
        )
        members_by_folder: dict[
            uuid.UUID, list[SymbolSubscriptionFolderMember]
        ] = {}
        for folder_id, ticker, name, subscription_id in memberships:
            members_by_folder.setdefault(folder_id, []).append(
                SymbolSubscriptionFolderMember(
                    ticker=ticker,
                    name=name,
                    subscription_id=subscription_id,
                )
            )

        return tuple(
            SymbolSubscriptionFolderSnapshot(
                id=folder.id,
                name=folder.name,
                description=folder.description,
                sort_order=folder.sort_order,
                members=tuple(members_by_folder.get(folder.id, ())),
                is_active=folder.is_active,
                track_market=folder.track_market,
                track_indicators=folder.track_indicators,
                track_news=folder.track_news,
                is_system=folder.is_system,
            )
            for folder in folders
        )

    def delete_folder(self, folder_id: uuid.UUID) -> bool:
        """Delete a folder (and its memberships via cascade). Refuses System."""
        folder = self.get(folder_id)
        if folder is None:
            return False
        if folder.is_system:
            raise ValueError("system_folder_protected")
        self.session.delete(folder)
        self.session.flush()
        return True

    def has_member(self, folder_id: uuid.UUID, ticker: str) -> bool:
        subscription = _subscription(self.session, ticker)
        if subscription is None:
            return False
        return self._get_membership(folder_id, subscription.id) is not None

    def member_count(self, folder_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(
            SymbolSubscriptionFolderMembership
        ).where(SymbolSubscriptionFolderMembership.folder_id == folder_id)
        return int(self.session.scalar(stmt) or 0)

    def _get_membership(
        self, folder_id: uuid.UUID, subscription_id: uuid.UUID
    ) -> SymbolSubscriptionFolderMembership | None:
        stmt = select(SymbolSubscriptionFolderMembership).where(
            SymbolSubscriptionFolderMembership.folder_id == folder_id,
            SymbolSubscriptionFolderMembership.subscription_id == subscription_id,
        )
        return self.session.scalars(stmt).one_or_none()


def _active_subscription(session: Session, ticker: str) -> SymbolSubscription | None:
    row = _subscription(session, ticker)
    if row is None or not row.active:
        return None
    return row


def _subscription(session: Session, ticker: str) -> SymbolSubscription | None:
    stmt = select(SymbolSubscription).where(SymbolSubscription.ticker == ticker.upper())
    return session.scalars(stmt).one_or_none()


def _normalize_folder_name(name: str) -> str:
    normalized = " ".join(name.strip().split())
    if not normalized:
        raise ValueError("folder_name_required")
    if len(normalized) > 80:
        raise ValueError("folder_name_too_long")
    return normalized


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None
