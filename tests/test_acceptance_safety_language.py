"""Slice 13 — Project-level safety-language acceptance gates.

The .devmd/13 acceptance list calls out the specific direct-advice
phrases that must be blocked by ``assert_no_forbidden_wording`` and
the descriptive idioms that must remain allowed. Parametrising the
list here keeps the contract visible to future contributors so a
regression in the regex (Slice-06 / Slice-10 / Slice-13 cleanups)
fails this suite directly rather than leaking through a downstream
view-model scan.
"""

from __future__ import annotations

import pytest

from finskillos.guards.base import GuardResult, assert_no_forbidden_wording

# .devmd/13 §Safety language — English direct-advice / certainty phrases.
_FORBIDDEN_EN: tuple[str, ...] = (
    "buy now",
    "sell now",
    "guaranteed",
    "must buy",
    "will rise",
)

# .devmd/13 §Safety language — Korean direct-advice / certainty phrases.
_FORBIDDEN_KO: tuple[str, ...] = (
    "지금 매수",
    "무조건 상승",
    "보장",
    "반드시 사",
    "오늘 팔아",
)

# Descriptive market idioms / interpretation text the scanner does
# receive. Hand-written Streamlit caption disclaimers like
# "매수 / 매도 지시가 아닌 ..." are NOT included — that text lives in
# the page module, not in view-model strings, so the scanner never
# sees it. The literal substring 매수 / 매도 inside such captions is
# intentionally caught by the regex and any disclaimer that needs
# them must avoid passing through the scanner.
_ALLOWED_DESCRIPTIVE: tuple[str, ...] = (
    "Monitor sell-the-news risk after the print.",
    "Sell-the-news pattern is possible despite a strong headline.",
    "RSI is elevated; monitor overheat risk.",
    "Trend state is bullish; tape support is constructive.",
)


def _wrap(message: str) -> GuardResult:
    return GuardResult(
        guard_name="ACCEPTANCE_SAFETY_LANGUAGE",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=message,
    )


@pytest.mark.parametrize("phrase", _FORBIDDEN_EN + _FORBIDDEN_KO)
def test_acceptance_forbidden_phrases_are_blocked(phrase: str) -> None:
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(_wrap(phrase))


@pytest.mark.parametrize("phrase", _ALLOWED_DESCRIPTIVE)
def test_acceptance_descriptive_phrases_remain_allowed(phrase: str) -> None:
    # Must not raise — the safety scan is descriptive-tolerant.
    assert_no_forbidden_wording(_wrap(phrase))


def test_acceptance_safety_blocks_buy_now_inside_longer_text() -> None:
    """Direct-advice phrases buried inside narrative still fail."""

    text = (
        "Earnings beat consensus by 3% — buy now to capture the move "
        "before the open."
    )
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(_wrap(text))


def test_acceptance_safety_blocks_korean_advice_inside_paragraph() -> None:
    text = "지수가 약하지만 이 종목은 무조건 상승할 것이라고 단언합니다."
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(_wrap(text))


def test_acceptance_safety_blocks_will_rise_prediction() -> None:
    """Deterministic-prediction wording must remain blocked."""

    text = "Forecast: the index will rise by 3% by month-end."
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(_wrap(text))
