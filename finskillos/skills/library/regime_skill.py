"""RISK.REGIME_RISK — the regime-risk guard as a declarative skill (20.2b).

Byte-for-byte conversion of ``guards.regime_guard`` — a categorical map from the
regime risk level to (status, risk_level), then status-driven copy. The FAIL rung
carries a *data-derived* risk level (RED or ORANGE), so it uses a callable
``risk_level`` (the runner resolves callables). Copy lifted verbatim.

* RISK.REGIME_RISK-001  status PASS  PASS / GREEN          — favourable regime
* RISK.REGIME_RISK-002  status WARN  WARN / YELLOW          — caution regime
* RISK.REGIME_RISK-003  status FAIL  FAIL / (RED|ORANGE)    — defensive regime
* RISK.REGIME_RISK-004  status INFO  INFO / UNKNOWN         — uninterpretable level
* RISK.REGIME_RISK-000  (fallback) regime/level missing     INFO / UNKNOWN
"""

from __future__ import annotations

from collections.abc import Mapping

from finskillos.guards.base import (
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.skills.base import Rule, SkillContext, SkillSpec

SKILL_ID = "RISK.REGIME_RISK"
VERSION = "regime-risk-v1-2026-06-17"

# Mirrors guards.regime_guard._REGIME_LEVEL_MAP.
_REGIME_LEVEL_MAP = {
    RISK_RED: (STATUS_FAIL, RISK_RED),
    RISK_ORANGE: (STATUS_FAIL, RISK_ORANGE),
    RISK_YELLOW: (STATUS_WARN, RISK_YELLOW),
    RISK_GREEN: (STATUS_PASS, RISK_GREEN),
    RISK_UNKNOWN: (STATUS_INFO, RISK_UNKNOWN),
}


def _derive(ctx: SkillContext) -> Mapping[str, object]:
    regime = ctx.get("regime")
    risk_level = ctx.get("regime_risk_level")
    if regime is None or risk_level is None:
        return {}
    status, level = _REGIME_LEVEL_MAP.get(risk_level, (STATUS_INFO, RISK_UNKNOWN))
    return {"_regime_status": status, "_regime_level": level}


def _evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "regime": ctx.get("regime"),
        "regime_risk_level": ctx.get("regime_risk_level"),
        "decision_mode": ctx.get("decision_mode"),
    }


def _is(status: str):
    return lambda ctx: ctx.get("_regime_status") == status


REGIME_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Regime risk — operating posture by market regime",
    reads=("regime", "regime_risk_level", "decision_mode"),
    derive=_derive,
    ladder=(
        Rule(
            rule_id="RISK.REGIME_RISK-001",
            when=_is(STATUS_PASS),
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="시장 regime이 우호적인 구간입니다.",
            message=lambda ctx: (
                f"현재 regime {ctx.get('regime')} / 운영 모드 "
                f"{ctx.get('decision_mode')}에서 기본 검토 모드가 가능한 환경입니다."
            ),
            evidence=_evidence,
        ),
        Rule(
            rule_id="RISK.REGIME_RISK-002",
            when=_is(STATUS_WARN),
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="시장 regime이 주의 구간으로 진입했습니다.",
            message=lambda ctx: (
                f"현재 regime {ctx.get('regime')}는 운영 모드 "
                f"{ctx.get('decision_mode')}로 공격적 노출 확대에는 제약 검토가 "
                "필요합니다."
            ),
            evidence=_evidence,
            watch_next=(
                "주도 섹터 RSI / VIX 추이 점검",
                "추격형 노출 제약 유지",
            ),
        ),
        Rule(
            rule_id="RISK.REGIME_RISK-003",
            when=_is(STATUS_FAIL),
            status=STATUS_FAIL,
            risk_level=lambda ctx: ctx.get("_regime_level"),
            title="시장 regime이 방어 구간입니다.",
            message=lambda ctx: (
                f"현재 regime {ctx.get('regime')}는 운영 모드 "
                f"{ctx.get('decision_mode')}로 계좌 보호가 우선되는 환경입니다."
            ),
            evidence=_evidence,
            watch_next=(
                "현금 비중 / drawdown guard 상태 점검",
                "공격적 노출 확대 제약 유지",
            ),
        ),
        Rule(
            rule_id="RISK.REGIME_RISK-004",
            when=_is(STATUS_INFO),
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="시장 regime 정보를 해석할 수 없습니다.",
            message=lambda ctx: (
                f"regime_risk_level={ctx.get('regime_risk_level')!r}이 알려진 "
                "값이 아닙니다."
            ),
            evidence=_evidence,
        ),
    ),
    fallback=Rule(
        rule_id="RISK.REGIME_RISK-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="시장 regime 정보가 아직 수집되지 않았습니다.",
        message=(
            "RegimeService.evaluate_today_regime이 실행되어 market_regimes에 "
            "결과가 누적되면 자동으로 점검합니다."
        ),
        evidence=lambda ctx: {
            "regime": None,
            "regime_risk_level": None,
            "decision_mode": ctx.get("decision_mode"),
        },
    ),
)
