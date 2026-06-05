"""On-demand explanation CLI — Slice 178.

Narrates descriptive evidence points (or reflection prompts) through the
explanation boundary (``finskillos.llm_explanation``). The default narrator is the
deterministic offline echo; the output is guard-scanned so it can only restate
evidence — never judgment or trade direction.

Examples:
  python scripts/explain.py --title "Regime" --point "Breadth narrow" --point "VIX elevated"
  python scripts/explain.py --kind reflection_prompt --title "Weekly" --point "What repeated?"
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.llm_explanation import (
    ExplanationBoundaryError,
    ExplanationRequest,
    narrate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Narrate descriptive evidence through the explanation boundary."
    )
    parser.add_argument(
        "--kind",
        choices=("evidence_narration", "reflection_prompt"),
        default="evidence_narration",
        help="What to narrate (default evidence_narration).",
    )
    parser.add_argument("--title", default="Evidence", help="Heading for the narration.")
    parser.add_argument(
        "--point",
        action="append",
        default=[],
        dest="points",
        help="A descriptive evidence point / prompt (repeatable).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request = ExplanationRequest(
        kind=args.kind, title=args.title, points=tuple(args.points)
    )
    try:
        print(narrate(request))
    except ExplanationBoundaryError as exc:
        print(f"explanation boundary: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
