"""Migration safety preflight — Slice 170.

Compares the database's current Alembic revision against the migration head in
the code, so an operator knows *before* an upgrade / restore whether the schema
is up to date, has pending migrations, or — the dangerous case — is at a
revision the code does not know about (the code is older than the DB).

Exit codes:
  0  up to date, or pending upgrade (informational)
  3  database is at an unknown / newer revision than the code (downgrade risk)
  4  could not reach the database
With ``--require-current`` a pending upgrade also exits non-zero (2), so the
check can gate an automated step.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from finskillos.config import get_settings

_ALEMBIC_INI = ROOT / "alembic.ini"
_SCRIPT_LOCATION = ROOT / "finskillos" / "db" / "migrations"

STATUS_UP_TO_DATE = "UP_TO_DATE"
STATUS_PENDING = "PENDING_UPGRADE"
STATUS_UNINITIALISED = "UNINITIALISED"
STATUS_UNKNOWN_REVISION = "UNKNOWN_REVISION"
STATUS_UNREACHABLE = "DB_UNREACHABLE"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check the database Alembic revision against the migration head "
            "before an upgrade or restore."
        )
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override the DATABASE_URL used for the check.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary.",
    )
    parser.add_argument(
        "--require-current",
        action="store_true",
        help="Exit non-zero when a pending upgrade exists (not only on danger).",
    )
    return parser


def _script_directory() -> ScriptDirectory:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_SCRIPT_LOCATION))
    return ScriptDirectory.from_config(cfg)


def _current_revision(database_url: str) -> str | None:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    finally:
        engine.dispose()


def evaluate(database_url: str) -> dict[str, object]:
    """Return the schema status without raising (DB errors become a status)."""

    script = _script_directory()
    heads = list(script.get_heads())
    head = heads[0] if len(heads) == 1 else ", ".join(heads)
    known = {revision.revision for revision in script.walk_revisions()}

    try:
        current = _current_revision(database_url)
    except SQLAlchemyError as exc:
        return {
            "status": STATUS_UNREACHABLE,
            "current": None,
            "head": head,
            "detail": f"Could not read the database revision: {type(exc).__name__}.",
        }

    if current is None:
        return {
            "status": STATUS_UNINITIALISED,
            "current": None,
            "head": head,
            "detail": "Database has no Alembic revision yet — run migrations.",
        }
    if current in heads:
        return {
            "status": STATUS_UP_TO_DATE,
            "current": current,
            "head": head,
            "detail": "Schema is at the migration head.",
        }
    if current in known:
        pending = _pending_count(script, current)
        return {
            "status": STATUS_PENDING,
            "current": current,
            "head": head,
            "pending": pending,
            "detail": (
                f"{pending} migration(s) pending — run an upgrade before relying "
                "on the schema."
            ),
        }
    return {
        "status": STATUS_UNKNOWN_REVISION,
        "current": current,
        "head": head,
        "detail": (
            f"Database revision {current} is not in the code history — the code "
            "may be older than the database (downgrade risk). Do not upgrade "
            "blindly; align the code version first."
        ),
    }


def _pending_count(script: ScriptDirectory, current: str) -> int:
    count = 0
    for revision in script.walk_revisions():
        if revision.revision == current:
            break
        count += 1
    return count


_EXIT_CODES = {
    STATUS_UP_TO_DATE: 0,
    STATUS_PENDING: 0,
    STATUS_UNINITIALISED: 0,
    STATUS_UNKNOWN_REVISION: 3,
    STATUS_UNREACHABLE: 4,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database_url = args.database_url or get_settings().database_url
    result = evaluate(database_url)
    exit_code = _EXIT_CODES.get(result["status"], 1)
    if args.require_current and result["status"] == STATUS_PENDING:
        exit_code = 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Migration safety: {result['status']}")
        print(f"  database revision: {result.get('current') or '(none)'}")
        print(f"  code head:         {result['head']}")
        print(f"  {result['detail']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
