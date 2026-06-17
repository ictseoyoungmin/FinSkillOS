"""Skill Catalog — a browsable spec auto-derived from the live registries.

Realises the legacy EXT-CREATIVE-002 "Analysis Policy as Markdown": every skill +
its rule ladder rendered from the registry, so the governing rule pack is
inspectable without reading code. ``docs/v4/SKILL_CATALOG.md`` is generated from
this and kept fresh by a test.
"""

from __future__ import annotations

from finskillos.skills.base import Rule, SkillSpec
from finskillos.skills.event_registry import build_event_registry
from finskillos.skills.regime_registry import build_regime_registry
from finskillos.skills.risk_registry import build_risk_registry

_HEADER = (
    "# Skill Catalog (auto-generated)\n\n"
    "Generated from the live skill registries by "
    "`finskillos.skills.catalog.build_catalog` (Phase 20.x). Do not edit by hand —"
    " run `python -m finskillos.skills.catalog` to regenerate. A test keeps this "
    "file in sync with the registries.\n"
)


def _static(value: object) -> str:
    return value if isinstance(value, str) else "(dynamic)"


def _rule_row(rule: Rule) -> str:
    title = rule.title if isinstance(rule.title, str) else "(dynamic)"
    return (
        f"| `{rule.rule_id}` | {_static(rule.status)} | "
        f"{_static(rule.risk_level)} | {title} |"
    )


def _regime_classification_rows() -> list[str]:
    """The REGIME.CLASSIFY priority table, rendered as catalog rows (20.3b)."""

    from finskillos.regime.regime_engine import (
        CLASSIFICATION_RULES,
        RULE_INSUFFICIENT_INPUTS,
        RULE_UNCLASSIFIED,
    )

    rows = [
        "Classification seam — the priority ladder below is a shared table the",
        "engine and skill both walk (first match wins); prose / confidence stay in",
        "the engine.",
        "",
        "| Rule | Regime state |",
        "|---|---|",
        f"| `{RULE_INSUFFICIENT_INPUTS}` | UNKNOWN (too few inputs) |",
    ]
    rows += [
        f"| `{rule_id}` | {state} |"
        for rule_id, _predicate, state in CLASSIFICATION_RULES
    ]
    rows.append(f"| `{RULE_UNCLASSIFIED}` | UNKNOWN (no rule matched) |")
    return rows


def _skill_section(skill: object) -> list[str]:
    skill_id = skill.skill_id  # type: ignore[attr-defined]
    version = skill.version  # type: ignore[attr-defined]
    lines = [f"### {skill_id} — `{version}`", ""]
    if isinstance(skill, SkillSpec):
        lines.append(skill.title)
        lines.append("")
        reads = ", ".join(skill.reads) if skill.reads else "—"
        lines.append(f"- **reads:** {reads}")
        lines.append("")
        lines.append("| Rule | Status | Risk | Title |")
        lines.append("|---|---|---|---|")
        for rule in (*skill.ladder, skill.fallback):
            lines.append(_rule_row(rule))
    elif skill_id == "REGIME.CLASSIFY":
        lines.extend(_regime_classification_rows())
    else:
        lines.append(
            "Seam skill — wraps an engine function; its rules convert to "
            "declarative rungs behind the seam."
        )
    lines.append("")
    return lines


def build_catalog(registries: dict[str, object]) -> str:
    """Render a markdown catalog from ``{domain: SkillRegistry}``."""

    parts = [_HEADER]
    for domain, registry in registries.items():
        parts.append(f"## {domain}\n")
        for skill in registry.all():  # type: ignore[attr-defined]
            parts.extend(_skill_section(skill))
    return "\n".join(parts).rstrip() + "\n"


def build_default_catalog() -> str:
    """The catalog for the live RISK + REGIME registries."""

    return build_catalog(
        {
            "RISK": build_risk_registry(),
            "REGIME": build_regime_registry(),
            "EVENT": build_event_registry(),
        }
    )


if __name__ == "__main__":  # pragma: no cover - manual regeneration entrypoint
    import pathlib

    target = pathlib.Path("docs/v4/SKILL_CATALOG.md")
    target.write_text(build_default_catalog(), encoding="utf-8")
    print(f"wrote {target}")
