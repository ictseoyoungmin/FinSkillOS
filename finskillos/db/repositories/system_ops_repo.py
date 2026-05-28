"""Repositories for System Ops and worker audit records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import SystemOpsProtocolRun, WorkerCycleRun


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


class WorkerCycleRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        status: str,
        started_at: datetime,
        finished_at: datetime,
        timeframe: str,
        market_status: str,
        news_status: str,
        indicator_status: str,
        market_scope: str,
        news_scope: str,
        indicator_scope: str,
        summary: dict,
    ) -> WorkerCycleRun:
        row = WorkerCycleRun(
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            timeframe=timeframe,
            market_status=market_status,
            news_status=news_status,
            indicator_status=indicator_status,
            market_scope=market_scope,
            news_scope=news_scope,
            indicator_scope=indicator_scope,
            summary=summary,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_recent(self, limit: int = 5) -> list[WorkerCycleRun]:
        stmt = (
            select(WorkerCycleRun)
            .order_by(WorkerCycleRun.started_at.desc(), WorkerCycleRun.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def latest(self) -> WorkerCycleRun | None:
        stmt = (
            select(WorkerCycleRun)
            .order_by(WorkerCycleRun.started_at.desc(), WorkerCycleRun.created_at.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()
