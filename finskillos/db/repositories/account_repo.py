"""AccountRepository — thin CRUD wrapper around the Account model."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import Account


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        target_value: Decimal,
        base_currency: str = "KRW",
    ) -> Account:
        account = Account(
            name=name, target_value=target_value, base_currency=base_currency
        )
        self.session.add(account)
        self.session.flush()
        return account

    def get(self, account_id: uuid.UUID) -> Account | None:
        return self.session.get(Account, account_id)

    def get_by_name(self, name: str) -> Account | None:
        stmt = select(Account).where(Account.name == name)
        return self.session.scalars(stmt).one_or_none()

    def list_all(self) -> list[Account]:
        return list(self.session.scalars(select(Account).order_by(Account.created_at)))

    def update_target(self, account_id: uuid.UUID, target_value: Decimal) -> Account:
        account = self.session.get(Account, account_id)
        if account is None:
            raise LookupError(f"Account {account_id} not found")
        account.target_value = target_value
        self.session.flush()
        return account

    def delete(self, account_id: uuid.UUID) -> None:
        account = self.session.get(Account, account_id)
        if account is not None:
            self.session.delete(account)
            self.session.flush()
