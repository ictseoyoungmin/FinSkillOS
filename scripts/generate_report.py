"""Scheduled report generator — Slice 174.

Writes a descriptive daily brief or weekly evidence report (regime + portfolio +
catalysts, plus the trade-process review for the weekly) to the exports
directory, so a cron / worker cadence can keep a dated report on disk. Read-only
against the database; the assembled markdown is wording-scanned in the builder.

Examples:
  python scripts/generate_report.py --period daily
  python scripts/generate_report.py --period weekly --stdout
  python scripts/generate_report.py --period event-week
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.db.session import session_scope

UTC = timezone.utc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a daily brief or weekly evidence report to disk."
    )
    parser.add_argument(
        "--period",
        choices=("daily", "weekly", "event-week"),
        default="daily",
        help="Which report to generate (default daily).",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="ISO date to report as-of (default today, UTC).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default $EXPORT_DIR or data/exports).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the report instead of writing a file.",
    )
    return parser


def _as_of(value: str | None) -> date:
    if value is None:
        return datetime.now(tz=UTC).date()
    return date.fromisoformat(value)


def _output_dir(out: str | None) -> Path:
    configured = out or os.getenv("EXPORT_DIR", "data/exports")
    path = Path(configured)
    if not path.is_absolute():
        path = ROOT / path
    return path


def generate(period: str, today: date) -> str:
    from api.weekly_report import build_report_markdown

    with session_scope() as session:
        return build_report_markdown(session, period=period, today=today)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    today = _as_of(args.date)
    markdown = generate(args.period, today)

    if args.stdout:
        print(markdown)
        return 0

    out_dir = _output_dir(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{args.period}_{today.isoformat()}.md"
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {args.period} report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
