"""Drawdown Guard — peak-to-current loss check.

Reads ``drawdown_pct`` straight off the latest portfolio snapshot when
available, otherwise derives it from ``peak_value`` / ``total_value``.
Output stays descriptive — the guard reports the drawdown band but
never says "sell" or "exit", because the user policy is to use the
signal as an operating-mode trigger rather than a transaction order.

Thresholds (negative percentages, per docs/v2_1/06 §9):

* 0% to -5%   : PASS / GREEN — normal volatility band
* -5% to -8%  : WARN / YELLOW — recent gains being given back
* -8% to -10% : WARN / YELLOW — Yellow Alert
* -10% to -15%: FAIL / ORANGE — Risk Reduction Mode
* below -15%  : FAIL / RED    — Defensive Mode
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    GUARD_DRAWDOWN,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
    GuardInput,
    GuardResult,
)


def _resolve_drawdown(inputs: GuardInput) -> Decimal | None:
    if inputs.drawdown_pct is not None:
        return Decimal(inputs.drawdown_pct)
    if inputs.peak_value is None or inputs.peak_value <= 0:
        return None
    if inputs.total_value is None:
        return None
    return (
        ((Decimal(inputs.total_value) - Decimal(inputs.peak_value))
         / Decimal(inputs.peak_value))
        * Decimal("100")
    ).quantize(Decimal("0.01"))


def evaluate(inputs: GuardInput) -> GuardResult:
    drawdown = _resolve_drawdown(inputs)

    if drawdown is None:
        return GuardResult(
            guard_name=GUARD_DRAWDOWN,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="drawdown을 계산할 수 있는 peak / total_value 정보가 없습니다.",
            message=(
                "portfolio_snapshots에 peak_value 또는 drawdown_pct가 기록되면 "
                "자동으로 계산됩니다."
            ),
            evidence={
                "peak_value": inputs.peak_value,
                "total_value": inputs.total_value,
            },
        )

    base_evidence = {
        "drawdown_pct": drawdown,
        "peak_value": inputs.peak_value,
        "total_value": inputs.total_value,
    }

    if drawdown >= Decimal("-5"):
        return GuardResult(
            guard_name=GUARD_DRAWDOWN,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="고점 대비 drawdown이 일반 변동 범위입니다.",
            message=(
                f"현재 고점 대비 {drawdown:.2f}% 수준이며 안전 구간에서 변동하고 있습니다."
            ),
            evidence=base_evidence,
        )
    if drawdown >= Decimal("-10"):
        return GuardResult(
            guard_name=GUARD_DRAWDOWN,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="고점 대비 -5% ~ -10% 구간으로 진입했습니다.",
            message=(
                f"현재 drawdown {drawdown:.2f}%로 최근 수익 일부가 반납되고 있습니다. "
                "포지션별 thesis와 stop 기준을 점검하세요."
            ),
            evidence=base_evidence,
            watch_next=(
                "약한 포지션의 stop 기준 점검",
                "단기 추격형 노출 제약 검토",
            ),
        )
    if drawdown >= Decimal("-15"):
        return GuardResult(
            guard_name=GUARD_DRAWDOWN,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="고점 대비 -10% 이상 손실 — Risk Reduction Mode.",
            message=(
                f"현재 drawdown {drawdown:.2f}%로 리스크 검토 구간에 진입했습니다. "
                "유동성 버퍼와 취약 포지션 기준을 점검하세요."
            ),
            evidence=base_evidence,
            watch_next=(
                "유동성 버퍼 상태 점검",
                "취약 포지션 기준 점검",
                "단기 추격형 노출 제약 유지",
            ),
        )

    return GuardResult(
        guard_name=GUARD_DRAWDOWN,
        status=STATUS_FAIL,
        risk_level=RISK_RED,
        title="고점 대비 -15% 이상 손실 — Defensive Mode.",
        message=(
            f"현재 drawdown {drawdown:.2f}%로 계좌 보호가 최우선되는 구간입니다. "
            "공격적 노출 확대를 보류하고 주간 복기 후 재평가하세요."
        ),
        evidence=base_evidence,
        watch_next=(
            "주간 복기 전 공격적 노출 확대 보류",
            "방어 모드 전환 점검",
        ),
    )
