"""Backup integrity verifier — Slice 171.

Checks a `pg_dump` plain-SQL backup *before* you rely on it: that the file is
non-trivial, ends with pg_dump's completion marker (so it wasn't truncated), and
declares every core table. This is the lightweight half of the backup-restore
drill — the full drill restores the dump into a throwaway database (see
docs/OPERATIONS_RUNBOOK.md). Read-only: it never touches a live database.

Exit codes:
  0  the dump looks complete and restorable
  3  the dump is suspect (truncated / empty / missing core tables)
  4  the dump file does not exist
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import re
from pathlib import Path

# Stable core tables every full backup must declare.
CORE_TABLES = (
    "accounts",
    "portfolio_snapshots",
    "positions",
    "trades",
    "market_bars",
    "alembic_version",
)

# pg_dump (plain format) writes this as the final line of a complete dump.
_COMPLETE_MARKER = "PostgreSQL database dump complete"
_DEFAULT_MIN_BYTES = 200


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a pg_dump SQL backup is complete and declares the core "
            "tables before relying on it for restore."
        )
    )
    parser.add_argument("path", help="Path to the .sql backup file.")
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=_DEFAULT_MIN_BYTES,
        help=f"Minimum plausible dump size (default {_DEFAULT_MIN_BYTES}).",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print a machine-readable summary."
    )
    return parser


def verify(path: Path, *, min_bytes: int = _DEFAULT_MIN_BYTES) -> dict[str, object]:
    """Return a structured integrity report without raising."""

    if not path.is_file():
        return {
            "ok": False,
            "status": "MISSING",
            "path": str(path),
            "detail": "Backup file does not exist.",
        }

    size = path.stat().st_size
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [
        table
        for table in CORE_TABLES
        if not re.search(rf"CREATE TABLE[^\n]*\b{re.escape(table)}\b", text)
    ]
    complete = _COMPLETE_MARKER in text
    problems: list[str] = []
    if size < min_bytes:
        problems.append(f"file is only {size} bytes (< {min_bytes}).")
    if not complete:
        problems.append("missing pg_dump completion marker (possibly truncated).")
    if missing:
        problems.append("missing core tables: " + ", ".join(missing))

    if problems:
        return {
            "ok": False,
            "status": "SUSPECT",
            "path": str(path),
            "size_bytes": size,
            "missing_tables": missing,
            "complete_marker": complete,
            "detail": " ".join(problems),
        }
    return {
        "ok": True,
        "status": "OK",
        "path": str(path),
        "size_bytes": size,
        "missing_tables": [],
        "complete_marker": True,
        "detail": (
            f"Backup declares all {len(CORE_TABLES)} core tables and ends with "
            "the completion marker."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify(Path(args.path), min_bytes=args.min_bytes)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Backup verify: {report['status']}")
        print(f"  path:   {report['path']}")
        if "size_bytes" in report:
            print(f"  size:   {report['size_bytes']} bytes")
        print(f"  {report['detail']}")

    if report["status"] == "MISSING":
        return 4
    return 0 if report["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
