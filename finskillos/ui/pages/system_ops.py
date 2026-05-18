"""System Ops page — sample-account seed + risk / regime re-run actions.

Read-only safe-mode actions only — nothing here triggers external
fetches or live brokerage calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from finskillos.db.seed import seed_default_account
from finskillos.services.regime_service import RegimeService
from finskillos.services.risk_guard_service import RiskGuardService

UTC = timezone.utc


def format_regime_recalc_message(
    *,
    regime: str,
    confidence,  # Decimal | float | int
    decision_mode: str,
    risk_level: str,
) -> str:
    """Build the success line shown after a Regime 재계산 run.

    Kept as a pure helper so the message format can be unit-tested
    without launching Streamlit (07-cleanup Task 4).
    """

    return (
        f"Regime 재계산 완료 · {regime} (confidence {float(confidence):.0f}%) · "
        f"운영 모드 {decision_mode} · 위험 레벨 {risk_level}"
    )


def render(session: Session) -> None:
    import streamlit as st

    from finskillos.db.repositories import AccountRepository

    st.markdown("## System Ops")
    st.caption(
        "Slice 07에서는 샘플 계좌 생성, 가드 재실행 등 안전한 운영 액션만 지원합니다."
    )

    accounts = AccountRepository(session).list_all()
    st.markdown("### Accounts")
    if accounts:
        st.table(
            [
                {
                    "Name": a.name,
                    "Currency": a.base_currency,
                    "Target": f"{a.target_value:,.0f}",
                    "Created": a.created_at.isoformat(timespec="seconds"),
                }
                for a in accounts
            ]
        )
    else:
        st.warning("아직 등록된 계좌가 없습니다.")

    st.markdown("### Actions")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("샘플 계좌 / 초기 스냅샷 생성", type="primary"):
            result = seed_default_account(session)
            session.commit()
            if result.created_account:
                st.success(f"계좌 생성 완료: {result.account.name}")
            else:
                st.info(f"기존 계좌 재사용: {result.account.name}")
            if result.created_snapshot:
                st.success("초기 포트폴리오 스냅샷 생성 완료.")
            else:
                st.info("기존 스냅샷이 이미 존재합니다.")
    with col_b:
        target_account = accounts[0] if accounts else None
        disabled = target_account is None
        if st.button("Risk Guard 재실행 (활성 alert 갱신)", disabled=disabled):
            service = RiskGuardService(session)
            report = service.evaluate(
                target_account.id,
                generated_at=datetime.now(tz=UTC),
                persist_alerts=True,
            )
            session.commit()
            st.success(
                f"가드 {len(report.results)}개 실행 완료 · 종합 상태 "
                f"{report.overall_status}"
            )
    with col_c:
        if st.button("Regime 재계산"):
            regime_service = RegimeService(session)
            try:
                output = regime_service.evaluate_today_regime(
                    snapshot_time=datetime.now(tz=UTC),
                    persist=True,
                )
                session.commit()
            except Exception as exc:  # noqa: BLE001 — surface as UI warning, do not crash
                st.warning(
                    "Regime 재계산 중 문제가 발생했습니다. "
                    "indicator / VIX 데이터 수집 상태를 확인하세요. "
                    f"오류: {exc}"
                )
            else:
                st.success(
                    format_regime_recalc_message(
                        regime=output.regime,
                        confidence=output.confidence,
                        decision_mode=output.decision_mode,
                        risk_level=output.risk_level,
                    )
                )
                if output.regime == "UNKNOWN":
                    st.info(
                        "필수 indicator 데이터가 부족해 UNKNOWN으로 분류되었습니다. "
                        "SPY / QQQ / SMH indicator_snapshots와 VIX market_bars가 "
                        "들어오면 다음 실행에서 자동 분류됩니다."
                    )
