"""Phase 20.x — the Skill Catalog is generated from the registries and kept fresh.

The committed ``docs/v4/SKILL_CATALOG.md`` must match what the live registries
render, so the browsable spec never drifts from the code.
"""

from __future__ import annotations

import pathlib

from finskillos.skills.catalog import build_default_catalog

_CATALOG_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "docs" / "v4" / "SKILL_CATALOG.md"
)


def test_catalog_lists_declarative_skills_and_rules():
    catalog = build_default_catalog()
    # A declarative RISK skill + its ladder rule ids.
    assert "### RISK.DRAWDOWN" in catalog
    assert "RISK.DRAWDOWN-003" in catalog
    assert "RISK.CASH_RATIO-001" in catalog
    # The REGIME seam is listed too.
    assert "### REGIME.CLASSIFY" in catalog
    assert "Seam skill" in catalog
    # Domains present.
    assert "## RISK" in catalog
    assert "## REGIME" in catalog


def test_committed_catalog_is_fresh():
    expected = build_default_catalog()
    actual = _CATALOG_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/v4/SKILL_CATALOG.md is stale — regenerate with "
        "`python -m finskillos.skills.catalog`."
    )
