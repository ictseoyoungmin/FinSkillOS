"""Run the descriptive market-regime scan.

Manual-first, cron-compatible command for Slice 18. The scan reads
stored indicator/market snapshots and persists a read-only regime
interpretation by default.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.regime_service import RegimeService

logger = logging.getLogger("finskillos.scripts.run_regime_scan")
UTC = timezone.utc


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute the descriptive market-regime snapshot."
    )
    parser.add_argument(
        "--snapshot-time",
        default=None,
        help="Optional ISO timestamp for the persisted regime row.",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Compute the regime without writing a row to market_regimes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging()

    snapshot_time = _parse_datetime(args.snapshot_time)
    with session_scope() as session:
        service = RegimeService(session)
        output = service.evaluate_today_regime(
            snapshot_time=snapshot_time,
            persist=not args.no_persist,
        )

    summary = {
        "regime": output.regime,
        "riskLevel": output.risk_level,
        "decisionMode": output.decision_mode,
        "confidence": str(output.confidence),
        "persisted": not args.no_persist,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        logger.info("Regime scan summary: %s", summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
