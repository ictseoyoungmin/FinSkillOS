"""System Ops page — sample-account seed + risk re-check actions.

Read-only safe-mode actions only — nothing here triggers external
fetches or live brokerage calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from finskillos.db.seed import seed_default_account
from finskillos.services.risk_guard_service import RiskGuardService

UTC = timezone.utc


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
    col_a, col_b = st.columns(2)
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
