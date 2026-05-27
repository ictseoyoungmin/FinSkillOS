"""Repository for System Ops protocol run audit records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import SystemOpsProtocolRun


class SystemOpsProtocolRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        protocol: str,
        status: str,
        message: str,
        detail: str,
        db_status: str,
        source: str,
        ran_at: datetime,
    ) -> SystemOpsProtocolRun:
        row = SystemOpsProtocolRun(
            protocol=protocol,
            status=status,
            message=message,
            detail=detail,
            db_status=db_status,
            source=source,
            ran_at=ran_at,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_recent(self, limit: int = 5) -> list[SystemOpsProtocolRun]:
        stmt = (
            select(SystemOpsProtocolRun)
            .order_by(SystemOpsProtocolRun.ran_at.desc(), SystemOpsProtocolRun.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def latest_by_protocol(self) -> dict[str, SystemOpsProtocolRun]:
        rows = list(
            self.session.scalars(
                select(SystemOpsProtocolRun).order_by(
                    SystemOpsProtocolRun.ran_at.desc(),
                    SystemOpsProtocolRun.created_at.desc(),
                )
            )
        )
        latest: dict[str, SystemOpsProtocolRun] = {}
        for row in rows:
            latest.setdefault(row.protocol, row)
        return latest
