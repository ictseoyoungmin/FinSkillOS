"""On-demand explanation boundary tests — Slice 178.

The contract: a narrator may only restate descriptive evidence / pose reflection
prompts — never judgment or trade direction. The boundary is enforced on output.
"""

from __future__ import annotations

import pytest

from finskillos.llm_explanation import (
    DISCLAIMER,
    EchoExplainer,
    ExplanationBoundaryError,
    ExplanationRequest,
    NullExplainer,
    build_explainer,
    narrate,
)


def _request(kind: str = "evidence_narration") -> ExplanationRequest:
    return ExplanationRequest(
        kind=kind, title="Regime", points=("Breadth narrow", "VIX elevated")
    )


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("echo", EchoExplainer),
        ("none", NullExplainer),
        ("off", NullExplainer),
        ("unknown", EchoExplainer),  # unknown → safe echo default
    ],
)
def test_build_explainer_resolves(name: str, expected: type) -> None:
    assert isinstance(build_explainer(name), expected)


def test_build_explainer_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINSKILLOS_LLM_EXPLAINER", "none")
    assert isinstance(build_explainer(), NullExplainer)
    monkeypatch.delenv("FINSKILLOS_LLM_EXPLAINER", raising=False)
    assert isinstance(build_explainer(), EchoExplainer)


def test_echo_narration_is_descriptive_and_disclaimed() -> None:
    text = narrate(_request(), explainer=EchoExplainer())
    assert "Evidence summary — Regime" in text
    assert "Breadth narrow" in text
    assert DISCLAIMER in text


def test_reflection_prompt_kind_lists_prompts() -> None:
    request = ExplanationRequest(
        kind="reflection_prompt",
        title="Weekly",
        points=("What repeated?", "What was the strongest evidence?"),
    )
    text = narrate(request, explainer=EchoExplainer())
    assert "Reflection prompts — Weekly" in text
    assert "- What repeated?" in text


def test_null_explainer_returns_empty() -> None:
    assert narrate(_request(), explainer=NullExplainer()) == ""


def test_boundary_blocks_judgment_or_direction() -> None:
    class _Hostile:
        def explain(self, request: ExplanationRequest) -> str:
            return "지금 사라"  # "buy now" — must never pass the boundary

    with pytest.raises(ExplanationBoundaryError):
        narrate(_request(), explainer=_Hostile())


def test_boundary_blocks_english_direction() -> None:
    class _Hostile:
        def explain(self, request: ExplanationRequest) -> str:
            return "You must buy now for guaranteed gains."

    with pytest.raises(ExplanationBoundaryError):
        narrate(_request(), explainer=_Hostile())


def test_request_has_no_trade_direction_field() -> None:
    # The input shape carries descriptive evidence only — no order / side field.
    fields = ExplanationRequest.__dataclass_fields__
    assert set(fields) == {"kind", "title", "points"}
