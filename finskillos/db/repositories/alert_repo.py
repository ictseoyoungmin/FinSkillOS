"""AlertRepository — append/query Risk Firewall alerts.

Alerts are append-only; the only mutation supported is the resolve flag.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
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
        stmt = select(Alert).where(Alert.resolved.is_(False))
        if account_id is not None:
            stmt = stmt.where(Alert.account_id == account_id)
        stmt = stmt.order_by(Alert.severity, Alert.alert_date.desc())
        return list(self.session.scalars(stmt))

    def resolve(self, alert_id: uuid.UUID) -> Alert:
        alert = self.session.get(Alert, alert_id)
        if alert is None:
            raise LookupError(f"Alert {alert_id} not found")
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        self.session.flush()
        return alert
