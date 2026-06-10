"""Toss API config — v4 Phase 13. Read from env; blank → disabled."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://openapi.tossinvest.com"


@dataclass(frozen=True)
class TossConfig:
    client_id: str | None
    client_secret: str | None
    account_seq: str | None
    base_url: str

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


def load_toss_config() -> TossConfig:
    return TossConfig(
        client_id=os.getenv("FINSKILLOS_TOSS_CLIENT_ID") or None,
        client_secret=os.getenv("FINSKILLOS_TOSS_CLIENT_SECRET") or None,
        account_seq=os.getenv("FINSKILLOS_TOSS_ACCOUNT_SEQ") or None,
        base_url=(
            os.getenv("FINSKILLOS_TOSS_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/"),
    )
