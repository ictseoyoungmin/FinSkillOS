"""On-demand explanation boundary — Slice 178.

An optional, pluggable narrator that turns **already-computed** descriptive
evidence (or reflection prompts) into prose. The hard contract: a narrator may
only restate evidence / pose reflection questions — never produce judgment, a
verdict, or trade direction. That boundary is enforced two ways:

1. **Input shape** — `ExplanationRequest` carries descriptive evidence points and
   a constrained ``kind``; there is no price-direction / order field to fill.
2. **Output guard** — every narrator's output is run through the Slice-06
   forbidden-wording guard before it is returned; a violation raises
   `ExplanationBoundaryError` so unsafe text never escapes, even from a future
   real-LLM adapter.

The default narrator is a deterministic offline ``EchoExplainer`` (no model, no
network). A real LLM adapter registers behind ``build_explainer`` but is **off by
default** (``FINSKILLOS_LLM_EXPLAINER`` defaults to ``echo``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

from finskillos.guards.base import GuardResult, assert_no_forbidden_wording

__all__ = [
    "ExplanationRequest",
    "Explainer",
    "EchoExplainer",
    "NullExplainer",
    "ExplanationBoundaryError",
    "build_explainer",
    "narrate",
    "DISCLAIMER",
]

ExplanationKind = Literal["evidence_narration", "reflection_prompt"]

DISCLAIMER = "Descriptive narration only — not judgment or a trade directive."


class ExplanationBoundaryError(ValueError):
    """Raised when narrator output breaches the descriptive-only boundary."""


@dataclass(frozen=True)
class ExplanationRequest:
    """Descriptive evidence to narrate. No trade-direction field by design."""

    kind: ExplanationKind
    title: str
    points: tuple[str, ...] = field(default_factory=tuple)


@runtime_checkable
class Explainer(Protocol):
    def explain(self, request: ExplanationRequest) -> str: ...


class NullExplainer:
    """Produces no narration (explicit opt-out)."""

    def explain(self, request: ExplanationRequest) -> str:
        return ""


class EchoExplainer:
    """Deterministic offline narrator — restates the evidence, no model call."""

    def explain(self, request: ExplanationRequest) -> str:
        points = [p.strip() for p in request.points if p.strip()]
        if request.kind == "reflection_prompt":
            lead = f"Reflection prompts — {request.title}:"
            body = "\n".join(f"- {p}" for p in points) or "- (no prompts provided)"
            return f"{lead}\n{body}"
        lead = f"Evidence summary — {request.title}:"
        if not points:
            body = "No evidence points were provided to narrate."
        else:
            body = "The current evidence notes: " + "; ".join(points) + "."
        return f"{lead}\n{body}"


def build_explainer(name: str | None = None) -> Explainer:
    """Resolve the configured narrator (env ``FINSKILLOS_LLM_EXPLAINER``)."""

    resolved = (name or os.getenv("FINSKILLOS_LLM_EXPLAINER", "echo")).strip().lower()
    if resolved in ("", "none", "null", "off"):
        return NullExplainer()
    # "echo" and any unknown value use the safe deterministic narrator. A real
    # LLM adapter registers here later, but never bypasses ``narrate``'s guard.
    return EchoExplainer()


def narrate(
    request: ExplanationRequest, *, explainer: Explainer | None = None
) -> str:
    """Narrate ``request`` through the configured explainer, enforcing the
    descriptive-only boundary on the output (Slice 178)."""

    explainer = explainer or build_explainer()
    text = explainer.explain(request)
    if not text:
        return ""
    _assert_descriptive(text)
    return f"{text}\n\n_{DISCLAIMER}_"


def _assert_descriptive(text: str) -> None:
    try:
        assert_no_forbidden_wording(
            GuardResult(
                guard_name="LLM_EXPLANATION_BOUNDARY",
                status="INFO",
                risk_level="GREEN",
                title="",
                message=text,
            )
        )
    except AssertionError as exc:
        raise ExplanationBoundaryError(
            "Narrator output breached the descriptive-only boundary "
            "(judgment / trade-direction wording is not allowed)."
        ) from exc
