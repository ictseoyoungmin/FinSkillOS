**FinSkillOS v2.1**

06. Regime / Risk Guard 룰북

시장 상태 판정, 지표 충돌 해석, 계좌 리스크 경고 규칙

| **문서 상태** | v2.1 기준 독립 실행형 문서                            |
|---------------|-------------------------------------------------------|
| **작성 목적** | 제품/개발 검토 및 후속 에이전트 개발 지시의 기준 문서 |
| **작성일**    | 2026-05-15                                            |

> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서를 참조하지 않아도 목적, 범위, 구조, 구현 기준을 이해할 수 있도록 작성되었습니다. v2.1은 Research Hub, Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 확장을 포함합니다.

# 1. 문서 목적

- FinSkillOS v2.1의 시장 상태 판정(Regime Engine)과 리스크 경고(Risk Guard) 기준을 정의한다.

- 룰 기반 판단을 먼저 사용하고, LLM은 해석 문구 정제나 주간 리포트 등 선택 기능으로 제한한다.

- 사용자에게 매수/매도 지시를 제공하지 않고, 현재 시장과 계좌가 어떤 운용 모드에 가까운지 설명한다.

- 룰은 재현 가능하고 테스트 가능해야 하며, 모든 alert는 근거 지표와 payload를 함께 저장해야 한다.

> **이 룰북은 투자 추천 모델이 아니라 실수 방지 시스템의 기준 문서다. 목표는 예측 정확도가 아니라, 과열/집중/드로우다운/이벤트 리스크를 사용자가 놓치지 않도록 하는 것이다.**

# 2. 입력 신호 체계

| **신호군**       | **예시**                                                    | **사용 목적**                                 |
|------------------|-------------------------------------------------------------|-----------------------------------------------|
| Market Sentiment | Fear & Greed, VIX, news heat                                | 시장 심리와 과열/공포 상태 판단               |
| Technical        | RSI, EMA, Bollinger Band, MACD, volume z-score, drawdown    | 추세, 과열, 변동성, 반전 위험 판단            |
| Macro            | 10Y yield, DXY, FOMC/CPI/PPI                                | 성장주 압박, risk-off 가능성 판단             |
| Sector           | SMH, ARKX, SRVR, PAVE, sector relative strength             | 주도 섹터와 로테이션 판단                     |
| Portfolio        | position weight, cash ratio, strategy mix, account drawdown | 계좌 리스크와 개인 룰 위반 감지               |
| Event            | SpaceX IPO window, Tesla event, NVDA earnings, FOMC, CPI    | 이벤트 전후 변동성 및 기대감 선반영 위험 판단 |
| News             | symbol/sector/macro news, impact score, sentiment           | 뉴스가 포지션과 섹터에 주는 영향도 해석       |

# 3. 시장 Regime 정의

| **Regime**           | **상태 의미**               | **대표 조건**                                                        | **기본 운용 모드**                     |
|----------------------|-----------------------------|----------------------------------------------------------------------|----------------------------------------|
| PANIC                | 공포 과매도와 강한 risk-off | Fear & Greed \< 20, VIX \> 30, 주요 지수 EMA20/60 하회, breadth 악화 | 신규 공격 금지, 관찰 및 분할 기회 탐색 |
| RECOVERY             | 공포 이후 회복 초기         | VIX 하락, QQQ/SMH 단기 반등, RSI 40~55 회복, breadth 개선            | 소액 진입 가능, confirmation 확인      |
| HEALTHY_BULL         | 건강한 상승                 | Fear & Greed 45~70, VIX 안정, QQQ/SMH EMA20 위, RSI 50~68            | 정상 운용, 강한 종목 중심              |
| AGGRESSIVE_RISK_ON   | 강한 상승과 모멘텀          | Fear & Greed 65~80, sector momentum 강함, VIX 낮음, RSI 60~75        | 공격 가능, 포지션 크기 관리            |
| RISK_ON_OVERHEAT     | 강하지만 과열된 상승        | Fear & Greed \> 80 또는 핵심 지표 RSI \> 70 다수, 뉴스/거래량 과열   | 기존 강자 유지, 신규 추격 제한         |
| DISTRIBUTION_RISK    | 상승 둔화 및 분배 위험      | 주가는 고점권이나 RSI/거래량 divergence, 좋은 뉴스 반응 둔화         | 익절/축소 경계, 리스크 낮추기          |
| DEFENSIVE_TRANSITION | 방어 전환 구간              | VIX 상승, QQQ EMA20 이탈, 섹터 모멘텀 약화, drawdown 확대            | 현금 확대, 단타 제한                   |
| RISK_OFF             | 위험 회피 상태              | VIX \> 25, 지수 하락 추세, 성장주/고베타 동반 약세                   | 신규 공격 중단, 계좌 보호 우선         |

# 4. 지표별 해석 규칙

| **지표**       | **구간**               | **해석**                                           | **주의점**                                                         |
|----------------|------------------------|----------------------------------------------------|--------------------------------------------------------------------|
| Fear & Greed   | \< 25                  | 공포. 매도 압력이 과도할 수 있으나 추세 확인 필요. | 공포 자체가 즉시 매수 신호는 아니다.                               |
| Fear & Greed   | 25~45                  | 주의/중립 하단. 회복 초기 여부 확인.               | VIX 하락과 breadth 개선이 동반되어야 한다.                         |
| Fear & Greed   | 45~70                  | 건강한 중립~탐욕. 정상 운용 가능.                  | 섹터 집중이 과도하면 별도 경고.                                    |
| Fear & Greed   | 70~80                  | 탐욕. 모멘텀은 강하지만 포지션 크기 관리 필요.     | 신규 추격매수 기대값 하락 가능.                                    |
| Fear & Greed   | \> 80                  | Extreme Greed. 과열 경계.                          | 강한 장에서는 지속될 수 있으므로 즉시 매도 신호로 해석하지 않는다. |
| VIX            | \< 15                  | 안정/안도. Risk-On 유지에 우호적.                  | 너무 낮은 VIX는 complacency 위험.                                  |
| VIX            | 15~20                  | 정상 변동성.                                       | 추세와 함께 해석.                                                  |
| VIX            | 20~25                  | 경계. 성장주 변동성 확대 가능.                     | 고베타 포지션 점검.                                                |
| VIX            | \> 25                  | Risk-Off 가능성 증가.                              | 신규 단타/스윙 진입 제한 검토.                                     |
| RSI            | \< 30                  | 과매도.                                            | 하락 추세에서는 과매도가 계속될 수 있다.                           |
| RSI            | 50~70                  | 상승 추세 내 건강한 모멘텀.                        | 거래량과 EMA 확인.                                                 |
| RSI            | \> 70                  | 과열 또는 강한 추세.                               | 단독 매도 신호가 아니라 추격 진입 제한 신호.                       |
| RSI divergence | 가격 신고가 + RSI 둔화 | 모멘텀 약화/분배 위험.                             | 거래량과 뉴스 반응 둔화 동반 시 경계 상승.                         |

# 5. 보조지표 해석 규칙

| **지표**          | **긍정 해석**                                       | **위험 해석**                                                    | **사용 위치**                        |
|-------------------|-----------------------------------------------------|------------------------------------------------------------------|--------------------------------------|
| EMA 20/60/120     | 가격이 EMA20 위, EMA20\>EMA60이면 단기 상승 추세.   | EMA20 이탈 후 회복 실패 또는 EMA20\<EMA60 전환은 방어 전환 신호. | Index Lab, Symbol Lab, Market Regime |
| Bollinger Band    | 상단 밴드 근처에서도 거래량 동반 시 강한 추세 가능. | 상단 돌파 후 음봉/거래량 폭증은 climax 위험.                     | Symbol Lab                           |
| MACD              | MACD line이 signal 위로 전환되고 histogram 개선.    | 고점권에서 MACD divergence 발생 시 분배 위험.                    | Index Lab, Symbol Lab                |
| Volume z-score    | 상승 돌파 시 거래량 동반은 confirmation.            | 뉴스 과열+거래량 폭증+음봉은 차익실현 위험.                      | Symbol Lab, News Intelligence        |
| Relative Strength | QQQ/SPY 대비 우위, SMH/QQQ 우위는 주도 섹터 확인.   | 시장 상승에도 상대강도 약화는 주도권 상실 신호.                  | Index Lab, Sector Rotation           |
| Breadth           | 상승 종목 수 확대는 healthy bull 강화.              | 지수 상승에도 breadth 축소는 distribution risk.                  | Market Regime                        |

# 6. Regime 판정 스코어링

- 각 지표는 0~100 점수로 정규화한다. 높은 점수가 항상 긍정은 아니며, risk_on_score와 overheat_score를 별도로 계산한다.

- Regime은 단순 평균이 아니라 risk_on_score, overheat_score, risk_off_score, distribution_score의 조합으로 결정한다.

- 일시적 튐을 줄이기 위해 hysteresis를 둔다. 예: Regime 변경은 2개 이상 핵심 조건이 동시에 충족되거나 2회 연속 스냅샷에서 확인될 때 반영한다.

- confidence를 함께 산출한다. 데이터 누락, 지표 충돌, API stale 상태에서는 confidence를 낮춘다.

| **스코어**         | **구성 요소**                                                            | **의미**                           |
|--------------------|--------------------------------------------------------------------------|------------------------------------|
| risk_on_score      | QQQ/SMH trend, sector momentum, low VIX, breadth, Fear & Greed 중간~상단 | 공격적 운용이 가능한 시장 힘       |
| overheat_score     | Fear & Greed extreme, RSI 과열, volume climax, news heat                 | 추격 진입과 포지션 과대 위험       |
| risk_off_score     | VIX 상승, EMA 이탈, sector momentum 약화, 금리/DXY 압박                  | 방어 전환 및 신규 공격 제한 필요성 |
| distribution_score | 가격 고점권, RSI divergence, 좋은 뉴스 반응 둔화, breadth 축소           | 상승 후반부 차익실현/분배 위험     |

# 7. 지표 충돌 해석 규칙

| **충돌 상황**                             | **잘못된 단순 해석**      | **FinSkillOS 해석**                                                                   |
|-------------------------------------------|---------------------------|---------------------------------------------------------------------------------------|
| RSI \> 70, VIX 낮음, sector momentum 강함 | 과매수이므로 즉시 매도    | 강한 추세가 지속 중일 수 있다. 기존 강자 유지 가능, 신규 추격만 제한.                 |
| Fear & Greed \> 80, breadth 강함          | 무조건 위험               | 과열은 맞지만 시장 내부 참여가 넓으면 즉시 붕괴 신호는 아니다. 포지션 크기 관리 중심. |
| VIX 상승, QQQ 상승                        | 문제 없음                 | 지수 상승 중 변동성 동반 상승은 불안정한 상승일 수 있다. 이벤트/옵션 만기 확인.       |
| 좋은 뉴스, 주가 약세                      | 뉴스가 아직 반영되지 않음 | 기대감 선반영 또는 분배 위험 가능성. 거래량과 캔들 반응 확인.                         |
| Fear & Greed 낮음, RSI 과매도             | 바닥 매수                 | 공포+과매도는 기회 후보일 뿐이다. VIX 둔화, EMA 회복, breadth 개선 확인 필요.         |

# 8. Risk Guard 규칙

| **Guard**             | **조건**                                                                 | **Severity** | **권장 모드/문구**                                                     |
|-----------------------|--------------------------------------------------------------------------|--------------|------------------------------------------------------------------------|
| Single Position Limit | 단일 종목 평가금액 \>= 10,000,000 KRW 또는 포트폴리오 비중 \>= 설정 한도 | YELLOW/RED   | 종목당 제한에 접근/초과했습니다. 신규 추가보다 비중 관리가 우선입니다. |
| Sector Concentration  | 단일 섹터 \> 60% 또는 AI CAPEX 관련 묶음 \> 70%                          | YELLOW/RED   | 종목은 분산되어도 같은 테마 리스크에 묶일 수 있습니다.                 |
| Drawdown Guard        | 고점 대비 -8%, -10%, -15% 단계                                           | YELLOW/RED   | 신규 단기 진입 제한, 손실 복구 매매 금지, 현금비중 확대 검토.          |
| Cash Ratio Guard      | 현금비중 \< 10% 또는 목표 단계별 최소치 미달                             | YELLOW       | 급락/이벤트 대응 여력이 낮습니다. 최소 현금비중을 회복하세요.          |
| Overtrading Guard     | 일일 거래 횟수/회전율이 설정 기준 초과, 손실 후 거래 증가                | YELLOW/RED   | 복구 매매 가능성이 있습니다. 오늘의 신규 진입을 제한하세요.            |
| Event Risk Guard      | 중요 이벤트 1~5거래일 전, 관련 포지션 비중 과대                          | YELLOW       | 이벤트 기대감 선반영과 발표 후 차익실현 리스크를 구분하세요.           |
| News Heat Guard       | 보유 종목 관련 뉴스 급증, sentiment 과열, 거래량 폭증                    | YELLOW       | 뉴스가 좋아도 주가 반응이 둔화되면 분배 위험입니다.                    |
| Goal Protection Guard | 자산 8,500만 이상 또는 목표 85% 이상                                     | YELLOW/RED   | 목표 근접 구간에서는 수익 극대화보다 손실 회피가 우선입니다.           |

# 9. Drawdown Guard 세부 기준

| **고점 대비 하락** | **상태**       | **시스템 메시지**                   | **운용 제한**                                              |
|--------------------|----------------|-------------------------------------|------------------------------------------------------------|
| 0% ~ -5%           | Normal         | 일반 변동 범위입니다.               | 제한 없음. 단, 과열장에서는 신규 추격 제한 유지.           |
| -5% ~ -8%          | Watch          | 최근 수익 일부가 반납되고 있습니다. | 포지션별 thesis와 stop 기준 점검.                          |
| -8% ~ -10%         | Yellow Alert   | 계좌가 고점 대비 -8%를 넘었습니다.  | 신규 단기 진입 제한, 섹터 집중도 확인.                     |
| -10% ~ -15%        | Risk Reduction | 리스크 축소 모드입니다.             | 현금비중 확대, 손실 복구 매매 금지, 약한 포지션 정리 검토. |
| -15% 이하          | Defensive Mode | 계좌 보호가 최우선입니다.           | 공격 운용 중단, 주간 복기 전 신규 진입 제한.               |

# 10. 목표 보호 모드

| **평가금액 구간** | **Goal Phase**     | **운용 철학**                | **기본 제한**                                     |
|-------------------|--------------------|------------------------------|---------------------------------------------------|
| 57M ~ 70M         | Growth             | 복리 엔진을 키우는 구간      | 기본 리스크 룰 준수, 종목당 1천만원 제한          |
| 70M ~ 85M         | Balanced           | 성장과 방어 균형             | 현금비중 최소 10~15%, 이벤트 전 과대 포지션 경계  |
| 85M ~ 95M         | Protection         | 목표 근접. 큰 손실 방지 우선 | 신규 고위험 추격 제한, drawdown guard 민감도 상향 |
| 95M ~ 100M        | Completion Guard   | 조기 종료 준비               | 수익 보호, 현금화 계획, 과열장 신규 공격 제한     |
| 100M 이상         | Challenge Complete | 목표 달성. 보호 모드 전환    | 신규 공격 중단, 다음 목표 설정 전 냉각 기간       |

# 11. Event Risk 규칙

- 중요 이벤트는 importance 1~5로 등급화한다. 5는 SpaceX IPO window, NVIDIA earnings, FOMC/CPI 등 계좌 전체에 영향을 줄 수 있는 이벤트다.

- 이벤트 위험 점수는 event_importance × related_portfolio_exposure × days_to_event_weight × market_overheat_weight로 계산한다.

- 이벤트 전에는 기대감 선반영 위험, 이벤트 후에는 sell-the-news 위험을 별도 문구로 설명한다.

- 관련 보유 종목이 없더라도 Market Regime에 영향을 줄 수 있는 이벤트는 표시한다.

# 12. Alert Schema

| **필드**       | **설명**                      | **예시**                                                             |
|----------------|-------------------------------|----------------------------------------------------------------------|
| severity       | INFO / YELLOW / RED           | YELLOW                                                               |
| guard_name     | 경고를 만든 guard 이름        | SECTOR_CONCENTRATION                                                 |
| title          | 짧은 제목                     | AI CAPEX 노출 과다                                                   |
| message        | 사용자에게 보여줄 자연어 설명 | 반도체, 데이터센터, 전력 인프라가 같은 risk-on 테마에 묶여 있습니다. |
| evidence       | 근거 지표                     | {"ai_capex_exposure": 0.72, "limit": 0.70}                           |
| suggested_mode | 행동 모드                     | LIMIT_NEW_ENTRIES                                                    |
| created_at     | 생성 시각                     | 2026-05-15T23:00:00+09:00                                            |
| resolved       | 사용자 확인/해결 여부         | false                                                                |

# 13. Rule Engine Pseudocode

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>1) Load latest market, sector, portfolio, event, news snapshots.<br />
2) Normalize raw indicators into risk_on, overheat, risk_off, distribution scores.<br />
3) Determine candidate regime using rule priority and hysteresis.<br />
4) Run Risk Guards against current portfolio snapshot.<br />
5) Apply Goal Protection modifier based on current account value.<br />
6) Resolve signal conflicts and generate interpretation tokens.<br />
7) Persist market_regime, alerts, interpretation cache, and state snapshot.<br />
8) UI reads state snapshot first, then lazy-loads supporting charts and logs.</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

# 14. 테스트 기준

| **테스트**            | **입력 조건**                                   | **기대 결과**                                              |
|-----------------------|-------------------------------------------------|------------------------------------------------------------|
| Overheat Regime       | Fear & Greed 85, QQQ RSI 72, SMH RSI 78, VIX 13 | RISK_ON_OVERHEAT, 신규 추격 제한 메시지                    |
| Risk-Off Transition   | VIX 27, QQQ EMA20 이탈, sector momentum 약화    | DEFENSIVE_TRANSITION 또는 RISK_OFF                         |
| Single Position Alert | TSLA market_value 11,000,000 KRW                | MAX_SINGLE_POSITION 경고 생성                              |
| Drawdown Yellow       | peak 62M, current 56.5M                         | drawdown -8% 이상 Yellow Alert                             |
| Goal Protection       | current 90M, target 100M                        | Protection phase 및 신규 고위험 제한                       |
| Conflict Resolution   | RSI 75, VIX 낮음, breadth 양호                  | 즉시 매도 신호가 아니라 기존 강자 유지/신규 추격 제한 해석 |
| Event Risk            | NVIDIA earnings 2일 전, NVDA/SMH exposure 25%   | 이벤트 전 기대감/발표 후 차익실현 위험 경고                |

# 15. 운영 및 보정 원칙

- 룰 threshold는 초기값으로 시작하고, 실제 매매/복기 데이터가 쌓이면 보정한다.

- 경고가 너무 많아지면 중요도와 actionability 기준으로 줄인다. 경고 피로는 시스템 신뢰도를 떨어뜨린다.

- LLM은 룰 결과를 바꾸지 않는다. LLM은 설명을 더 읽기 쉽게 만드는 보조 계층으로 제한한다.

- 모든 룰 변경은 버전과 변경 사유를 기록한다. 나중에 과거 판단 재현성을 위해 rule_version을 저장한다.

- 시스템은 “매수/매도하라”가 아니라 “현재 이 행동은 어떤 리스크를 동반한다”라고 설명한다.
