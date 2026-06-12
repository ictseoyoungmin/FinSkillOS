"""AlertRepository — append/query Risk Firewall alerts.

Alerts are append-only; the only mutation supported is the resolve flag.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from finskillos.db.models import Alert


class AlertRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        alert_date: date,
        guard_name: str,
        severity: str,
        title: str,
        account_id: uuid.UUID | None = None,
        message: str | None = None,
        payload: dict | None = None,
    ) -> Alert:
        alert = Alert(
            account_id=account_id,
            alert_date=alert_date,
            guard_name=guard_name,
            severity=severity,
            title=title,
            message=message,
            payload=payload,
        )
        self.session.add(alert)
        self.session.flush()
        return alert

    def get(self, alert_id: uuid.UUID) -> Alert | None:
        return self.session.get(Alert, alert_id)

    def list_active(
        self,
        account_id: uuid.UUID | None = None,
    ) -> list[Alert]:
        severity_rank = case(
            (Alert.severity == "RED", 0),
            (Alert.severity == "ORANGE", 1),
            (Alert.severity == "YELLOW", 2),
            (Alert.severity == "INFO", 3),
            else_=9,
        )
        stmt = select(Alert).where(Alert.resolved.is_(False))
        if account_id is not None:
            stmt = stmt.where(Alert.account_id == account_id)
        stmt = stmt.order_by(
            severity_rank, Alert.alert_date.desc(), Alert.created_at.desc()
        )
        return list(self.session.scalars(stmt))

    def resolve(self, alert_id: uuid.UUID) -> Alert:
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            raise LookupError(f"Alert {alert_id} not found")
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        self.session.flush()
        return alert

    def resolve_stale(
        self,
        *,
        account_id: uuid.UUID | None,
        current_date: date,
        active_guards: set[str],
    ) -> int:
        """Resolve every unresolved alert that the latest full guard re-scan no
        longer backs — anything dated before ``current_date`` (superseded) or a
        same-day guard that is not currently firing (condition cleared). Keeps the
        active list a snapshot of the present state instead of an append-only log.
        Returns the number resolved."""

        stmt = select(Alert).where(Alert.resolved.is_(False))
        if account_id is not None:
            stmt = stmt.where(Alert.account_id == account_id)
        now = datetime.now(timezone.utc)
        resolved = 0
        for alert in self.session.scalars(stmt):
            if alert.alert_date == current_date and alert.guard_name in active_guards:
                continue
            alert.resolved = True
            alert.resolved_at = now
            resolved += 1
        if resolved:
            self.session.flush()
        return resolved
