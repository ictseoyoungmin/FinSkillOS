**FinSkillOS v2.1**

05. UI/UX 설계서

해석 접근성을 중심으로 한 개인 투자 운영체제 화면 설계

| **문서 상태** | v2.1 기준 독립 실행형 문서                            |
|---------------|-------------------------------------------------------|
| **작성 목적** | 제품/개발 검토 및 후속 에이전트 개발 지시의 기준 문서 |
| **작성일**    | 2026-05-15                                            |

> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서를 참조하지 않아도 목적, 범위, 구조, 구현 기준을 이해할 수 있도록 작성되었습니다. v2.1은 Research Hub, Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 확장을 포함합니다.

# 1. 문서 목적

- FinSkillOS v2.1의 화면 구조, 정보구조, 사용자 흐름, 컴포넌트 체계, 시각 언어를 정의한다.

- 대시보드가 단순 차트 모음으로 변질되지 않도록 “상태 → 해석 → 리스크 → 행동 → 복기” 흐름을 UX의 중심 원칙으로 고정한다.

- 개발자가 Streamlit/React 등 구현 방식과 무관하게 동일한 제품 경험을 구현할 수 있도록 화면별 책임과 구성 요소를 명시한다.

- 투자 추천 또는 자동 매매 신호가 아닌, 사용자의 리스크 인식과 판단 접근성을 높이는 의사결정 보조 UX를 설계한다.

> **핵심 원칙: 그래프를 읽게 하지 말고 상태를 읽게 하라. 차트는 근거이고, 해석이 본문이며, 행동 모드가 결론이다.**

# 2. UX 철학과 제품 정체성

| **구분**    | **일반 금융 대시보드** | **FinSkillOS v2.1**                   |
|-------------|------------------------|---------------------------------------|
| 핵심 단위   | 종목, 차트, 뉴스       | 시장 상태, 계좌 리스크, 목표 진행률   |
| 사용자 질문 | 어떤 종목이 오를까?    | 지금 공격/방어/유지 중 무엇이 맞는가? |
| 차트 역할   | 메인 콘텐츠            | 해석의 근거 자료                      |
| 뉴스 역할   | 피드 나열              | 내 보유 종목/섹터 영향도 해석         |
| 경고 방식   | 숫자와 색상            | 왜 위험한지와 다음 체크포인트 설명    |
| 최종 출력   | 정보 조회              | 오늘의 운용 모드와 리스크 제한        |

# 3. 전체 정보구조 IA

| **상위 영역** | **탭**          | **역할**                               | **핵심 질문**                               |
|---------------|-----------------|----------------------------------------|---------------------------------------------|
| Operate       | Command Center  | 오늘의 종합 상태와 행동 모드           | 지금 공격/방어/유지 중 무엇인가?            |
| Operate       | Market Regime   | 시장 상태 및 지표 충돌 해석            | 시장은 Risk-On인가 Risk-Off인가?            |
| Operate       | Portfolio Risk  | 내 계좌의 집중도, 드로우다운, 현금비중 | 내 포지션은 과도하게 위험한가?              |
| Operate       | Event Radar     | 촉매 이벤트와 포지션 영향도            | 어떤 일정이 내 계좌를 흔들 수 있는가?       |
| Operate       | Goal Tracker    | 5,700만원에서 1억원까지의 목표 관리    | 목표에 가까워질수록 리스크를 줄이고 있는가? |
| Reflect       | Trade Journal   | 매매 이유, 감정, 결과 복기             | 나는 어떤 상황에서 돈을 벌고 잃는가?        |
| Analyze       | Research Hub    | 지수, 종목, 뉴스, 섹터 심화 분석       | 판단 근거를 깊게 확인하려면?                |
| System        | Settings / Data | 데이터 소스, 룰, 티커, 목표 설정       | 시스템 기준은 올바르게 설정되어 있는가?     |

# 4. 글로벌 UX 구조

- 좌측 내비게이션: Command Center, Market Regime, Portfolio Risk, Event Radar, Goal Tracker, Trade Journal, Research Hub, Settings/Data.

- 상단 상태 바: 시장 개장 상태, 마지막 동기화 시각, 현재 Regime, 리스크 레벨, 목표 진행률을 표시한다.

- 우측 해석 패널: 각 탭에서 “What happened / What it means / What to watch next”를 기본 구조로 제공한다.

- 하단 상태 흐름: State → Interpretation → Risk → Action → Reflection → Results를 시각적으로 고정한다.

- 모든 화면은 Summary First, Details on Demand 원칙을 따른다. 사용자는 먼저 결론을 보고, 필요할 때 차트/뉴스/원천 데이터를 연다.

# 5. 화면별 상세 설계

| **화면**                   | **목적**                  | **주요 구성요소**                                                                                               | **사용자 흐름**                                                                                 | **성능/구현 메모**                                                                  |
|----------------------------|---------------------------|-----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Command Center             | 오늘의 운영 조종석        | 현재 시장 상태, 목표 진행률, 포트폴리오 가치, 행동 모드, 핵심 경고, AI 해석 요약, Suggested Action.             | 앱을 켜자마자 오늘 신규 진입 가능 여부, 기존 포지션 유지 여부, 현금비중 경고를 확인한다.        | 앱 초기 렌더는 state snapshot만 읽어 1.5초 이내에 표시한다.                         |
| Market Regime              | 시장 상태 해석            | Fear & Greed, VIX, QQQ/SMH/TSLA RSI, 섹터 모멘텀, Regime History, Conflict Interpretation.                      | RSI 과열이지만 VIX가 낮은 상황처럼 지표가 충돌할 때 단순 위험/안전이 아닌 상태 설명을 제공한다. | 차트는 최근 3~6개월 기본, 전체 기간은 사용자가 요청할 때만 로딩한다.                |
| Portfolio Risk             | 내 계좌 리스크 제어       | 보유 종목, 섹터 노출, 종목당 제한, 현금비중, 고점 대비 drawdown, 전략 믹스, Risk Controls.                      | 분산처럼 보이지만 AI CAPEX 테마에 과도하게 묶였는지 감지한다.                                   | 현재 포지션 snapshot 기반으로 guard를 즉시 계산한다.                                |
| Event Radar                | 촉매와 이벤트 리스크 관리 | SpaceX IPO, Tesla 이벤트, NVIDIA 실적, FOMC, CPI, 우주 발사 일정, 이벤트-포지션 영향도.                         | 이벤트 전에는 기대감 과열, 이벤트 후에는 차익실현 가능성을 구분해 표시한다.                     | 이벤트 데이터는 하루 1회 갱신하고 사용자가 수동 이벤트를 추가할 수 있어야 한다.     |
| Goal Tracker               | 1억 목표 달성 관리        | 현재 57,000,000원, 목표 100,000,000원, 진행률, 남은 금액, 시나리오, Growth/Balanced/Protection/Completion 단계. | 목표가 가까워질수록 공격성을 자동으로 낮추도록 시각화한다.                                      | 복잡한 Monte Carlo는 요청 시 실행하고 기본 화면은 rule-based projection을 사용한다. |
| Trade Journal / Reflection | 매매 복기 및 학습         | 매수 thesis, catalyst, market regime, emotion state, result, mistake tags, regime별 성과.                       | 손실 복구 매매, 추격매수, stop loss 미설정 같은 반복 실수를 데이터로 드러낸다.                  | 원본 일지는 append-only, 통계는 materialized summary를 사용한다.                    |
| Research Hub               | 심화 분석 작업 공간       | Index Lab, Symbol Lab, News & Intelligence, Sector Rotation.                                                    | Command Center의 결론이 왜 나왔는지 차트와 뉴스로 확인한다.                                     | 탭별 lazy loading을 적용하고 차트 데이터는 필요 시점에만 로딩한다.                  |

# 6. Research Hub 상세 설계

| **하위 탭**         | **주요 기능**                                                                                                         | **해석 패널 기준**                                                                      | **연결되는 상위 판단**                         |
|---------------------|-----------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|------------------------------------------------|
| Index Lab           | SPY/QQQ/SMH/ARKX/SRVR/PAVE/VIX/DXY/TNX 개별 및 overlay 차트, normalized performance, EMA/Bollinger/RSI/MACD.          | 지수와 섹터 ETF가 같은 방향으로 움직이는지, 상대강도가 어디에 있는지 설명한다.          | Market Regime, Sector Rotation, Command Center |
| Symbol Lab          | 종목 검색, 캔들, 거래량, 시간/일/주/월봉, EMA, Bollinger, VWAP, RSI, MACD, 내 평균단가/비중/손절/이벤트 연결.         | 차트 상태를 내 포지션의 위험과 연결한다. 예: 반등은 유지되지만 이벤트 선반영 위험 증가. | Portfolio Risk, Event Radar, Trade Journal     |
| News & Intelligence | 시장/섹터/종목/이벤트 연동 뉴스, 보유종목 필터, 중요도, 영향 방향, AI 요약.                                           | 뉴스가 내 포지션에 긍정/중립/부정인지, 기대감 과열인지, 실제 리스크인지 구분한다.       | Event Radar, Portfolio Risk, Market Regime     |
| Sector Rotation     | 반도체, 우주, 데이터센터, 인프라, 전력, AI 소프트웨어, 방산, 현금/채권성 자산의 1W/1M/3M 성과, RSI, 거래량, 상대강도. | 주도 섹터와 이탈 섹터를 구분하고, 내 포트폴리오가 뒤늦게 과열 섹터에 몰렸는지 설명한다. | Market Regime, Portfolio Risk                  |

# 7. 차트 UX 원칙

- 모든 차트에는 해석 카드가 붙어야 한다: What happened, What it means, What to watch next.

- 개별 지표 차트와 overlay 차트를 구분한다. overlay는 normalized performance 기준을 기본으로 사용한다.

- 시간 단위는 intraday, daily, weekly, monthly를 지원하되 기본은 daily/3개월로 시작한다.

- 종목 차트에는 평균단가, 현재 수익률, 포지션 비중, 손절 기준, 관련 이벤트를 함께 표시한다.

- Bollinger Band, EMA, RSI, MACD 등 보조지표는 기본 숨김 또는 체크박스 토글로 제공한다.

- 차트는 판단 근거이지 결론이 아니다. 결론은 항상 상태/리스크/행동 모드로 압축한다.

# 8. 뉴스 UX 원칙

| **요소**    | **설계 기준**                                                                                            |
|-------------|----------------------------------------------------------------------------------------------------------|
| 뉴스 카드   | 제목, 출처, 시간, 관련 종목, 관련 섹터, 중요도, 방향성, 내 포지션 영향도, 요약, 주의점으로 구성한다.     |
| 필터        | 보유 종목만, 관심 종목만, 반도체, 우주, 데이터센터, 인프라, TSLA/Musk ecosystem, 오늘/3일/1주.           |
| 이벤트 연동 | Event Radar의 일정과 뉴스가 연결되어야 한다. 예: SpaceX IPO 뉴스가 TSLA/ARKX/RKLB 관련 리스크로 연결.    |
| 해석 문구   | 뉴스가 좋은지 나쁜지만 말하지 말고 기대감 선반영, 차익실현, 실적 확인, 규제 리스크 중 무엇인지 설명한다. |
| 중복 제거   | 동일 주제 뉴스는 클러스터링하여 정보 과부하를 줄인다.                                                    |

# 9. 상태/색상/경고 규칙

| **상태** | **색상**    | **사용 위치**                         | **문구 톤**                                |
|----------|-------------|---------------------------------------|--------------------------------------------|
| INFO     | Blue/Teal   | 일반 상태, 동기화, 중립 정보          | 정보 제공. 행동 강제 없음.                 |
| OK       | Green       | 목표 정상, 추세 건강, 현금비중 양호   | 긍정적이나 과신을 유도하지 않는다.         |
| CAUTION  | Amber       | 과열, 집중도 경계, 이벤트 전후 변동성 | 신규 진입 제한, 포지션 관리 강조.          |
| RISK     | Red         | 드로우다운, 제한 초과, Risk-Off 전환  | 즉시 확인해야 할 리스크. 과장 없이 구체적. |
| COMPLETE | Purple/Gold | 1억원 목표 달성 및 조기 종료          | 축하와 함께 보호 모드 전환을 안내.         |

# 10. 핵심 컴포넌트 설계

| **컴포넌트**         | **용도**                      | **필수 속성**                                                   |
|----------------------|-------------------------------|-----------------------------------------------------------------|
| Market State Banner  | 현재 시장 상태를 한 줄로 압축 | regime, risk_level, decision_mode, updated_at                   |
| Metric Card          | 핵심 숫자 표시                | label, value, delta, state, tooltip                             |
| Interpreter Panel    | 상태 해석                     | summary, positive_factors, risk_factors, next_watch             |
| Alert Card           | 리스크 경고                   | severity, guard_name, message, payload, action_link             |
| Chart Panel          | 차트와 해석 묶음              | ticker/list, timeframe, overlays, interpretation                |
| Event Impact Card    | 이벤트와 내 포지션 연결       | event, affected_themes, related_holdings, pre/post risk         |
| Goal Progress Module | 목표 진행률과 보호 모드       | current, target, remaining, phase, completion_state             |
| Journal Entry Row    | 매매 기록                     | ticker, thesis, catalyst, regime, emotion, result, mistake_tags |

# 11. 화면 상태 설계: Empty, Loading, Error

| **상태**     | **사용자 메시지 원칙**                                         | **예시**                                                                                           |
|--------------|----------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Empty        | 사용자가 다음에 무엇을 입력해야 하는지 명확히 안내한다.        | 아직 포지션이 없습니다. 먼저 보유 종목을 입력하면 목표 진행률과 리스크 경고를 계산합니다.          |
| Loading      | 무엇을 갱신 중인지와 최근 캐시 사용 여부를 표시한다.           | 시장 데이터를 갱신 중입니다. 최근 캐시 데이터로 Command Center를 먼저 표시합니다.                  |
| Partial Data | 누락 데이터가 판단에 어떤 영향을 주는지 설명한다.              | Fear & Greed 데이터가 누락되어 Regime confidence가 낮아졌습니다. RSI/VIX 중심으로 임시 판정합니다. |
| Error        | 기술 오류보다 사용자가 취할 수 있는 다음 행동을 우선 제시한다. | 뉴스 API 호출에 실패했습니다. 마지막 저장 뉴스와 이벤트 캘린더 기준으로 표시합니다.                |
| Stale Data   | 데이터 오래됨을 명확히 표시하고 수동 갱신 버튼을 제공한다.     | 시장 데이터가 18시간 전 기준입니다. Refresh를 눌러 최신 데이터를 가져오세요.                       |

# 12. 구현 우선순위

1.  Command Center: state snapshot 기반 1차 화면 구현.

2.  Portfolio Risk: positions와 risk guards를 연결하여 계좌 리스크를 즉시 표시.

3.  Market Regime: RSI/VIX/Fear & Greed 기반의 초기 regime 해석 구현.

4.  Research Hub v1: Index Lab과 Symbol Lab의 기본 차트 및 해석 패널 구현.

5.  News & Intelligence: 뉴스 수집보다 먼저 뉴스-포지션 영향도 데이터 모델과 UI를 구현.

6.  Trade Journal: 거래 기록과 regime별 성과 요약 구현.

7.  UI polish: 색상, 상태 카드, microcopy, empty/error state 정리.

# 13. Acceptance Criteria

- 사용자는 Command Center만 보고 오늘의 운용 모드를 이해할 수 있어야 한다.

- Market Regime 화면은 최소 5개 지표의 충돌 상황을 자연어로 설명해야 한다.

- Symbol Lab은 차트와 내 포지션 맥락을 같은 화면에서 제공해야 한다.

- News & Intelligence는 뉴스의 원문 나열이 아니라 내 포지션 영향도를 먼저 보여야 한다.

- 모든 주요 차트 화면은 What happened / What it means / What to watch next를 포함해야 한다.

- 경고 메시지는 숫자만 표시하지 않고 왜 위험한지와 다음 체크포인트를 설명해야 한다.
