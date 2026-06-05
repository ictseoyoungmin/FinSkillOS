"""Local data-dir policy report — Slice 172.

Prints where FinSkillOS keeps local state, so an operator can see (and relocate)
it: the host data directories, the backups directory, and the `.env` config. The
Postgres data itself lives in the Docker named volume ``postgres_data`` (shown by
``docker volume ls``, not by this filesystem report). Read-only.
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Defaults mirror .env.example; env vars override (docker compose / shell).
_DIR_KEYS = (
    ("DATA_DIR", "data"),
    ("CACHE_DIR", "data/cache"),
    ("EXPORT_DIR", "data/exports"),
    ("BACKUP_DIR", "backups"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report the local data-dir / backup locations and config."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print a machine-readable summary."
    )
    return parser


def _dir_facts(path: Path) -> dict[str, object]:
    exists = path.exists()
    file_count = 0
    total_bytes = 0
    if exists and path.is_dir():
        for child in path.rglob("*"):
            if child.is_file():
                file_count += 1
                total_bytes += child.stat().st_size
    return {
        "path": str(path),
        "exists": exists,
        "file_count": file_count,
        "total_bytes": total_bytes,
    }


def build_report(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    dirs: dict[str, object] = {}
    for key, default in _DIR_KEYS:
        configured = os.getenv(key, default)
        path = Path(configured)
        if not path.is_absolute():
            path = base / path
        dirs[key] = {"configured": configured, **_dir_facts(path)}

    env_file = base / ".env"
    return {
        "repo_root": str(base),
        "env_file": {"path": str(env_file), "exists": env_file.exists()},
        "postgres_volume": "postgres_data (Docker named volume — see `docker volume ls`)",
        "directories": dirs,
        "policy": (
            "Postgres state lives in the postgres_data volume — `docker compose "
            "down` keeps it; never use `down -v` unless you intend to erase it. "
            "Back up before risky changes (./fsoctl.sh backup)."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Repo root: {report['repo_root']}")
        env = report["env_file"]
        print(f".env:      {env['path']} ({'present' if env['exists'] else 'absent'})")
        print(f"Postgres:  {report['postgres_volume']}")
        print("Directories:")
        for key, facts in report["directories"].items():
            print(
                f"  {key:<11} {facts['path']} "
                f"({'exists' if facts['exists'] else 'absent'}, "
                f"{facts['file_count']} files, {facts['total_bytes']} bytes)"
            )
        print(f"\nPolicy: {report['policy']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
