"""RISK.DRAWDOWN — the Drawdown guard expressed as a declarative Skill (Phase 20.0).

First migration proving the Skill Layer can reproduce an existing guard exactly.
The bands, thresholds, and descriptive copy are lifted verbatim from
``finskillos.guards.drawdown_guard`` so the parity test
(``tests/test_skill_layer.py``) is byte-for-byte. A reviewer can change a
threshold or a line below and both behaviour and audit trail change — with no
edit to engine/service/route code (the Phase-20 success criterion).

Rule ladder (negative percentages, docs/v2_1/06 §9):

* RISK.DRAWDOWN-001  >= -5   PASS / GREEN   — normal volatility band
* RISK.DRAWDOWN-002  >= -10  WARN / YELLOW  — recent gains given back
* RISK.DRAWDOWN-003  >= -15  FAIL / ORANGE  — Risk Reduction Mode
* RISK.DRAWDOWN-004  else    FAIL / RED     — Defensive Mode
* RISK.DRAWDOWN-000  (fallback) INFO / UNKNOWN — no peak/total to compute from
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

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
from finskillos.skills.base import (
    ANY,
    Rule,
    SkillContext,
    SkillSpec,
    band_rule,
)

SKILL_ID = "RISK.DRAWDOWN"
VERSION = "drawdown-v1-2026-06-17"


def _derive_drawdown(ctx: SkillContext) -> Mapping[str, object]:
    """Resolve ``drawdown_pct`` — read it directly, else derive from peak/total.

    Mirrors ``guards.drawdown_guard._resolve_drawdown`` so the migrated skill and
    the legacy guard agree on the number (and therefore on the band that fires).
    """

    direct = ctx.num("drawdown_pct")
    if direct is not None:
        return {"drawdown_pct": direct}
    peak = ctx.num("peak_value")
    total = ctx.num("total_value")
    if peak is None or peak <= 0 or total is None:
        return {}  # leave absent → the fallback (missing-data) rung fires
    derived = ((total - peak) / peak * Decimal("100")).quantize(Decimal("0.01"))
    return {"drawdown_pct": derived}


def _base_evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "drawdown_pct": ctx.num("drawdown_pct"),
        "peak_value": ctx.get("peak_value"),
        "total_value": ctx.get("total_value"),
    }


def _msg(template: str):
    def _build(ctx: SkillContext) -> str:
        return template.format(drawdown=ctx.num("drawdown_pct"))

    return _build


DRAWDOWN_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Drawdown — peak-to-current loss band",
    reads=("drawdown_pct", "peak_value", "total_value"),
    derive=_derive_drawdown,
    ladder=(
        band_rule(
            "RISK.DRAWDOWN-001",
            feature="drawdown_pct",
            at_least="-5",
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="고점 대비 drawdown이 일반 변동 범위입니다.",
            message=_msg(
                "현재 고점 대비 {drawdown:.2f}% 수준이며 안전 구간에서 변동하고 있습니다."
            ),
            evidence=_base_evidence,
        ),
        band_rule(
            "RISK.DRAWDOWN-002",
            feature="drawdown_pct",
            at_least="-10",
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="고점 대비 -5% ~ -10% 구간으로 진입했습니다.",
            message=_msg(
                "현재 drawdown {drawdown:.2f}%로 최근 수익 일부가 반납되고 있습니다. "
                "포지션별 thesis와 stop 기준을 점검하세요."
            ),
            evidence=_base_evidence,
            watch_next=(
                "약한 포지션의 stop 기준 점검",
                "단기 추격형 노출 제약 검토",
            ),
        ),
        band_rule(
            "RISK.DRAWDOWN-003",
            feature="drawdown_pct",
            at_least="-15",
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="고점 대비 -10% 이상 손실 — Risk Reduction Mode.",
            message=_msg(
                "현재 drawdown {drawdown:.2f}%로 리스크 검토 구간에 진입했습니다. "
                "유동성 버퍼와 취약 포지션 기준을 점검하세요."
            ),
            evidence=_base_evidence,
            watch_next=(
                "유동성 버퍼 상태 점검",
                "취약 포지션 기준 점검",
                "단기 추격형 노출 제약 유지",
            ),
        ),
        band_rule(
            "RISK.DRAWDOWN-004",
            feature="drawdown_pct",
            at_least=ANY,
            status=STATUS_FAIL,
            risk_level=RISK_RED,
            title="고점 대비 -15% 이상 손실 — Defensive Mode.",
            message=_msg(
                "현재 drawdown {drawdown:.2f}%로 계좌 보호가 최우선되는 구간입니다. "
                "공격적 노출 확대를 보류하고 주간 복기 후 재평가하세요."
            ),
            evidence=_base_evidence,
            watch_next=(
                "주간 복기 전 공격적 노출 확대 보류",
                "방어 모드 전환 점검",
            ),
        ),
    ),
    fallback=Rule(
        rule_id="RISK.DRAWDOWN-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="drawdown을 계산할 수 있는 peak / total_value 정보가 없습니다.",
        message=(
            "portfolio_snapshots에 peak_value 또는 drawdown_pct가 기록되면 "
            "자동으로 계산됩니다."
        ),
        evidence=lambda ctx: {
            "peak_value": ctx.get("peak_value"),
            "total_value": ctx.get("total_value"),
        },
    ),
)
