"""Shared v4.2 Evidence-to-Judgment fixture blocks."""

from __future__ import annotations

from api.schemas.common import (
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
)


def judgment(
    eyebrow: str,
    title: str,
    accent: str,
    summary: str,
    confidence: int,
) -> JudgmentHeader:
    return JudgmentHeader(
        eyebrow=eyebrow,
        title=title,
        accent=accent,
        summary=summary,
        confidence=confidence,
    )


def drivers(*rows: tuple[str, str, str]) -> list[EvidenceDriver]:
    return [EvidenceDriver(score=score, title=title, note=note) for score, title, note in rows]


def conflicts(*rows: tuple[str, str]) -> list[EvidenceConflict]:
    return [EvidenceConflict(title=title, note=note) for title, note in rows]


def watchpoints(*rows: tuple[str, str]) -> list[EvidenceWatchpoint]:
    return [EvidenceWatchpoint(title=title, note=note) for title, note in rows]


def interpretation(
    verdict: str,
    why_it_matters: str,
    what_remains_uncertain: str,
) -> IntegratedInterpretation:
    return IntegratedInterpretation(
        verdict=verdict,
        why_it_matters=why_it_matters,
        what_remains_uncertain=what_remains_uncertain,
    )
