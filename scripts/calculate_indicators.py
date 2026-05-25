"""Compute indicator snapshots from stored market bars.

Manual-first, cron-compatible command for Slice 18. Indicators are
descriptive read models only; no trade recommendation is produced.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.data_sources import DEFAULT_TIMEFRAME, DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.signal_service import SignalService

logger = logging.getLogger("finskillos.scripts.calculate_indicators")


def _tickers(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return DEFAULT_US_TICKER_UNIVERSE
    result: list[str] = []
    for value in values:
        result.extend(part.strip().upper() for part in value.split(",") if part.strip())
    return tuple(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute descriptive indicator snapshots from stored bars."
    )
    parser.add_argument(
        "--tickers",
        nargs="*",
        default=None,
        help="Ticker list, either space-separated or comma-separated.",
    )
    parser.add_argument(
        "--timeframe",
        default=DEFAULT_TIMEFRAME,
        help=f"Indicator timeframe (default: {DEFAULT_TIMEFRAME}).",
    )
    parser.add_argument(
        "--persist-history",
        action="store_true",
        help="Persist every historical snapshot instead of only the latest one.",
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

    target_tickers = _tickers(args.tickers)
    logger.info(
        "Computing indicators timeframe=%s tickers=%s persist_history=%s",
        args.timeframe,
        ",".join(target_tickers),
        args.persist_history,
    )

    with session_scope() as session:
        service = SignalService(session)
        results = service.compute_for_universe(
            target_tickers,
            timeframe=args.timeframe,
            persist_history=args.persist_history,
        )

    succeeded = [item for item in results if item.ok]
    failed = [item for item in results if not item.ok]
    summary = {
        "timeframe": args.timeframe,
        "tickers": len(results),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "snapshotsWritten": sum(item.snapshots_written for item in results),
        "failures": [
            {"ticker": item.ticker, "error": item.error} for item in failed
        ],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        logger.info("Indicator compute summary: %s", summary)
    return 0 if len(succeeded) > 0 or len(results) == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
