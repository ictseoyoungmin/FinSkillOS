"""Seed command for slice 02 — default account + initial 57M KRW snapshot.

Usage:
    python scripts/seed_sample_data.py                     # use Settings defaults
    python scripts/seed_sample_data.py --snapshot-date 2026-05-17

The script is idempotent: running it twice does not create duplicates.
It honors `FINSKILLOS_DEFAULT_ACCOUNT_NAME`, `FINSKILLOS_TARGET_VALUE`,
`FINSKILLOS_BASE_CURRENCY`, and `DATABASE_URL` from the environment via
`finskillos.config.get_settings()`.
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from finskillos.config import get_settings
from finskillos.db.seed import (
    DEFAULT_INITIAL_CASH_VALUE,
    DEFAULT_INITIAL_TOTAL_VALUE,
    seed_default_account,
    seed_system_folder,
)
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging

logger = logging.getLogger("finskillos.scripts.seed_sample_data")


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"--snapshot-date must be YYYY-MM-DD, got {value!r}"
        ) from exc


def _parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            f"expected a decimal string, got {value!r}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed the default trading account and initial portfolio snapshot."
    )
    parser.add_argument(
        "--snapshot-date",
        type=_parse_date,
        default=None,
        help="Snapshot date for the initial portfolio row (default: today).",
    )
    parser.add_argument(
        "--initial-total-value",
        type=_parse_decimal,
        default=DEFAULT_INITIAL_TOTAL_VALUE,
        help=f"Initial total account value (default: {DEFAULT_INITIAL_TOTAL_VALUE}).",
    )
    parser.add_argument(
        "--initial-cash-value",
        type=_parse_decimal,
        default=DEFAULT_INITIAL_CASH_VALUE,
        help=f"Initial cash bucket (default: {DEFAULT_INITIAL_CASH_VALUE}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info(
        "Seeding default account '%s' (target=%s %s) into %s",
        settings.default_account_name,
        settings.target_value,
        settings.base_currency,
        settings.database_url.split("@")[-1],
    )

    with session_scope() as session:
        result = seed_default_account(
            session,
            snapshot_date=args.snapshot_date,
            initial_total_value=args.initial_total_value,
            initial_cash_value=args.initial_cash_value,
        )
        folder_result = seed_system_folder(session)

    logger.info(
        "Seed complete: account=%s created=%s snapshot=%s created=%s positions=%s",
        result.account.id,
        result.created_account,
        result.initial_snapshot.id if result.initial_snapshot else None,
        result.created_snapshot,
        result.created_positions,
    )
    logger.info(
        "System folder seeded: id=%s created=%s subscribed=%s linked=%s members=%s",
        folder_result.folder_id,
        folder_result.created_folder,
        folder_result.subscribed,
        folder_result.linked,
        folder_result.members,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
