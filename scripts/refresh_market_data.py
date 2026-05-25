"""Refresh stored market bars.

Manual-first, cron-compatible command for Slice 18. The command writes
market bars only; it does not compute indicators, classify regimes, or
emit trading instructions.

Examples:
    python3 scripts/refresh_market_data.py --adapter mock
    python3 scripts/refresh_market_data.py --tickers SPY QQQ SMH VIX
    python3 scripts/refresh_market_data.py --adapter csv --csv-path data/bars.csv
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

from finskillos.config import get_settings
from finskillos.data_sources import (
    DEFAULT_TIMEFRAME,
    DEFAULT_US_TICKER_UNIVERSE,
    CsvMarketDataAdapter,
    MockMarketDataAdapter,
)
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.market_data_service import MarketDataService

logger = logging.getLogger("finskillos.scripts.refresh_market_data")
UTC = timezone.utc


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _tickers(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return DEFAULT_US_TICKER_UNIVERSE
    result: list[str] = []
    for value in values:
        result.extend(part.strip().upper() for part in value.split(",") if part.strip())
    return tuple(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh stored market bars for the configured universe."
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
        help=f"Market-bar timeframe (default: {DEFAULT_TIMEFRAME}).",
    )
    parser.add_argument(
        "--adapter",
        choices=("mock", "csv"),
        default="mock",
        help="Market adapter to use. `mock` is deterministic and offline-safe.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=None,
        help="CSV path required when --adapter csv is selected.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Optional ISO timestamp/date upper bound for fetched bars.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    setup_logging(settings.log_level)

    if args.adapter == "csv":
        if args.csv_path is None:
            raise SystemExit("--csv-path is required when --adapter csv is selected")
        adapter = CsvMarketDataAdapter(args.csv_path)
    else:
        adapter = MockMarketDataAdapter()

    target_tickers = _tickers(args.tickers)
    logger.info(
        "Refreshing market bars adapter=%s timeframe=%s tickers=%s",
        args.adapter,
        args.timeframe,
        ",".join(target_tickers),
    )

    with session_scope() as session:
        service = MarketDataService(session, adapter=adapter, universe=target_tickers)
        report = service.refresh_bars(
            target_tickers,
            timeframe=args.timeframe,
            end=_parse_datetime(args.end),
        )

    summary = {
        "timeframe": report.timeframe,
        "tickers": len(report.results),
        "succeeded": len(report.succeeded),
        "failed": len(report.failed),
        "barsWritten": report.total_bars_written,
        "failures": [
            {"ticker": item.ticker, "error": item.error} for item in report.failed
        ],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        logger.info("Market refresh summary: %s", summary)
    return 0 if len(report.succeeded) > 0 or len(report.results) == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
