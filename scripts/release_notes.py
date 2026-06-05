"""Release-notes generator — Slice 173.

Turns the project's ``NN — Title`` commit convention into a markdown slice list
for a git range, so CHANGELOG entries stay in sync with what actually shipped.
Read-only: it only reads ``git log``.

``--from`` / ``--to`` take git refs (commit / tag / branch), not slice numbers.

Examples:
  python scripts/release_notes.py --from v0.4 --to HEAD
  python scripts/release_notes.py --from 21035e1 --version "v0.5 — Phase 5"
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Slice commit subjects look like "169 — Operator CLI / Bootstrap (Phase 5)".
_SLICE_RE = re.compile(r"^(\d+)\s+—\s+(.+)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate release notes from NN — Title slice commits."
    )
    parser.add_argument(
        "--from",
        dest="from_ref",
        default=None,
        help="Start ref (exclusive). Omit for the whole history.",
    )
    parser.add_argument(
        "--to", dest="to_ref", default="HEAD", help="End ref (default HEAD)."
    )
    parser.add_argument(
        "--version", default="Unreleased", help="Heading for the notes."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print a machine-readable summary."
    )
    return parser


def parse_slice_commits(subjects: list[str]) -> list[tuple[int, str]]:
    """Extract ``(number, title)`` from slice commit subjects, newest-first input
    preserved as ascending-by-number output (deduped on number, first wins)."""

    seen: dict[int, str] = {}
    for subject in subjects:
        match = _SLICE_RE.match(subject.strip())
        if match is None:
            continue
        number = int(match.group(1))
        seen.setdefault(number, match.group(2).strip())
    return sorted(seen.items())


def collect_subjects(from_ref: str | None, to_ref: str) -> list[str]:
    rev_range = f"{from_ref}..{to_ref}" if from_ref else to_ref
    result = subprocess.run(
        ["git", "log", "--format=%s", rev_range],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def render_markdown(entries: list[tuple[int, str]], version: str) -> str:
    lines = [f"## {version}", ""]
    if not entries:
        lines.append("_No slice commits in this range._")
    else:
        for number, title in entries:
            lines.append(f"- **{number}** — {title}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    subjects = collect_subjects(args.from_ref, args.to_ref)
    entries = parse_slice_commits(subjects)
    if args.json:
        print(
            json.dumps(
                {
                    "version": args.version,
                    "count": len(entries),
                    "slices": [{"number": n, "title": t} for n, t in entries],
                },
                indent=2,
            )
        )
    else:
        print(render_markdown(entries, args.version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
