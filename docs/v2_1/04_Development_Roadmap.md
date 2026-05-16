# 04. FinSkillOS v2.1 개발 로드맵

Research Hub 확장과 PostgreSQL-first MVP 실행 계획

| Version | Status | Updated |
|---|---|---|
| v2.1 | Review Draft | 2026-05-15 |

> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서 없이 읽어도 전체 맥락과 구현 기준을 이해할 수 있도록 작성되었습니다.

## 문서 목적

- FinSkillOS v2.1을 실제 개발 가능한 phase와 slice 단위로 분해한다.

- 운영 탭(Command Center 등)과 분석 탭(Research Hub)을 구분하여 개발 우선순위를 정한다.

- 각 phase마다 구현 목표, 산출물, 테스트, 완료 기준을 명시한다.

- 에이전트가 코드를 작성할 때 판단 기준으로 사용할 수 있는 acceptance criteria를 제공한다.

> **핵심 원칙:** MVP라도 데이터 구조는 낮추지 않는다. PostgreSQL-first, Snapshot-first, Research-ready 구조로 시작한다.

# 목차

- 1. 로드맵 원칙
- 2. Phase Overview
- 3. Phase 0: DB Foundation
- 4. Phase 1: Goal/Portfolio OS
- 5. Phase 2: Market Signals and Charts
- 6. Phase 3: Regime/Guard/Interpreter
- 7. Phase 4: Research Hub
- 8. Phase 5: Event and News Intelligence
- 9. Phase 6: Journal/Reports
- 10. 테스트/성능/완료 기준

# 1. 로드맵 원칙

FinSkillOS v2.1의 개발 로드맵은 MVP를 빠르게 만들되, 최종 확장을 방해하는 다운그레이드를 피하는 방향으로 설계한다.

| **원칙**             | **개발 적용**                                                                     |
|----------------------|-----------------------------------------------------------------------------------|
| PostgreSQL-first     | 초기부터 accounts, positions, trades, market_bars, news 모델을 migration으로 관리 |
| Operate first        | Command Center, Portfolio Risk, Goal Tracker를 먼저 구현                          |
| Research-ready       | Index/Symbol/News 분석이 붙을 수 있도록 데이터 모델을 선반영                      |
| Interpretation-first | 차트보다 상태 해석과 행동 모드를 우선 노출                                        |
| Rule-first           | Regime/Guard는 LLM이 아니라 재현 가능한 룰 기반으로 시작                          |
| Cache-heavy          | 시장 데이터와 지표는 snapshot과 cache를 통해 빠르게 표시                          |

개발은 Streamlit-first로 시작하되, 내부 구조는 services/repositories/kernel/ui로 분리하여 이후 FastAPI/React로 확장 가능하게 둔다.

# 2. Phase Overview

| **Phase** | **목표**                 | **핵심 산출물**                                 | **우선순위** |
|-----------|--------------------------|-------------------------------------------------|--------------|
| 0         | 프로젝트/DB 기반         | Docker Postgres, SQLAlchemy, Alembic, seed data | 필수         |
| 1         | Goal/Portfolio OS        | 목표 진행률, 포지션 입력, 기본 Guard            | 필수         |
| 2         | Market Signals & Charts  | market_bars, RSI/EMA/Bollinger, 기본 차트       | 필수         |
| 3         | Regime/Guard/Interpreter | 상태 머신, 위험 경고, 자연어 해석               | 필수         |
| 4         | Research Hub             | Index Lab, Symbol Lab, Sector Rotation          | 핵심 확장    |
| 5         | Event/News Intelligence  | Event Radar, News impact, 포지션 연계           | 핵심 확장    |
| 6         | Journal/Reports          | 매매 복기, regime별 성과, 주간 리포트           | 고도화       |
| 7         | UX Polish/Deployment     | 성능 최적화, 반응형 UI, 배포                    | 마감         |

# 3. Phase 0: DB Foundation

목표: PostgreSQL-first MVP 기반을 만든다. 이 단계가 불안정하면 이후 기능을 붙일 때 속도가 느려진다.

| **Slice**       | **구현 내용**                                       | **완료 조건**                                |
|-----------------|-----------------------------------------------------|----------------------------------------------|
| 0.1 Environment | docker-compose.yml, .env.example, DATABASE_URL      | postgres 컨테이너 기동 및 앱 연결 성공       |
| 0.2 ORM         | SQLAlchemy 2.x, psycopg, session manager            | repository 테스트에서 DB 세션 생성/종료 확인 |
| 0.3 Migration   | Alembic 초기화 및 core schema migration             | alembic upgrade head 성공                    |
| 0.4 Seed        | 계좌 목표 1억, 현재 5,700만원, 기본 ticker universe | seed script 재실행 가능/idempotent           |
| 0.5 Repo Layer  | Account/Portfolio/Market/Event repository           | CRUD 단위 테스트 통과                        |

- 금지: SQLite-only MVP로 우회하지 않는다.

- 금지: 마이그레이션 없이 모델만 만든다.

- 테스트: DB smoke test, migration test, seed test를 최소 구성으로 포함한다.

# 4. Phase 1: Goal/Portfolio OS

목표: FinSkillOS의 조종석을 만들기 위한 최소 계좌 운영 기능을 구현한다.

| **Slice**             | **구현 내용**                                       | **완료 조건**                        |
|-----------------------|-----------------------------------------------------|--------------------------------------|
| 1.1 Goal Tracker      | 57M -\> 100M 목표 진행률, 남은 금액, milestone mode | Command Center에 progress card 표시  |
| 1.2 Portfolio Input   | 수동 포지션 입력/수정 UI                            | positions 테이블에 저장 및 즉시 반영 |
| 1.3 Snapshot          | 일별 portfolio_snapshots 저장                       | peak_value, drawdown_pct 계산        |
| 1.4 Basic Guards      | 종목당 1천만원 제한, cash ratio, drawdown guard     | alert 생성 및 Risk Control에 표시    |
| 1.5 Command Center v1 | 상태, 목표, 포트폴리오, 경고 카드                   | 첫 화면 1.5초 이내 렌더링            |

Phase 1 완료 시점에는 아직 고급 차트가 없어도 된다. 대신 사용자는 “현재 목표 대비 어디까지 왔고, 내 계좌가 과도하게 위험한가”를 즉시 볼 수 있어야 한다.

# 5. Phase 2: Market Signals and Charts

목표: Market Regime과 Research Hub의 기초가 되는 가격/지표/차트 데이터를 구축한다.

| **Slice**            | **구현 내용**                                                | **완료 조건**                          |
|----------------------|--------------------------------------------------------------|----------------------------------------|
| 2.1 Universe         | QQQ, SPY, SMH, ARKX, SRVR, PAVE, TSLA, NVDA 등 기본 universe | ticker_master와 watchlist 생성         |
| 2.2 Market Bars      | OHLCV 수집 및 market_bars 저장                               | ticker/timeframe/date 중복 없이 upsert |
| 2.3 Indicators       | RSI, EMA20/60/120, Bollinger Band, MACD, volume z-score      | indicator_snapshots 저장               |
| 2.4 Chart Components | 캔들, 거래량, EMA, Bollinger, overlay 기본 컴포넌트          | Symbol Lab/Index Lab에서 재사용 가능   |
| 2.5 Cache Policy     | 증분 갱신, stale fallback, refresh 버튼                      | 외부 API 실패 시 마지막 스냅샷 표시    |

- MVP 기본 타임프레임: 1d, 1w, 1mo. intraday는 데이터 소스 안정화 후 추가한다.

- 차트는 plotly 기반으로 시작하고, 고성능이 필요해지면 lightweight-charts/React 전환을 고려한다.

- 중요: 차트 컴포넌트는 Research Hub뿐 아니라 Market Regime의 drilldown에서도 재사용한다.

# 6. Phase 3: Regime/Guard/Interpreter

목표: 여러 지표를 사용자가 이해 가능한 시장 상태와 행동 모드로 번역한다.

| **Slice**             | **구현 내용**                                                | **완료 조건**                                   |
|-----------------------|--------------------------------------------------------------|-------------------------------------------------|
| 3.1 Regime Rules      | PANIC, RECOVERY, HEALTHY_BULL, RISK_ON_OVERHEAT 등 상태 정의 | 테스트 입력별 regime 결정                       |
| 3.2 Risk Guards       | drawdown, concentration, overheat, goal protection           | alerts 테이블에 결과 저장                       |
| 3.3 Interpreter       | 템플릿 기반 자연어 요약                                      | What happened / What it means / Watch next 출력 |
| 3.4 Conflict Resolver | RSI 과열 + VIX 안정 같은 충돌 해석                           | 모순 지표에 대한 설명 생성                      |
| 3.5 Market Regime UI  | Fear & Greed, VIX, RSI, sector momentum, 해석 패널           | 그래프보다 해석이 상단에 표시                   |

이 단계까지 완료되면 FinSkillOS는 “숫자 대시보드”가 아니라 “상태 해석 OS”로 동작하기 시작한다.

# 7. Phase 4: Research Hub

목표: 기존 6개 운영 탭과 별도로 심화 분석 공간을 제공한다. Research Hub는 분석 탭이지만, 모든 화면에 해석 패널을 붙여야 한다.

| **Submodule**           | **구현 내용**                                                   | **완료 조건**                         |
|-------------------------|-----------------------------------------------------------------|---------------------------------------|
| Index Lab               | 지수/ETF 개별 차트, overlay, normalized performance, 상대강도   | QQQ/SMH/ARKX/PAVE 등 비교 가능        |
| Symbol Lab              | 종목 검색, 캔들, 거래량, EMA, Bollinger, RSI, 내 포지션 맥락    | TSLA 등 보유 종목 상세 분석 가능      |
| Sector Rotation         | 섹터별 1W/1M/3M 수익률, RSI, momentum score                     | 현재 주도 섹터와 약화 섹터 표시       |
| Research Interpretation | 차트 해석 카드: What happened / What it means / Watch next      | 차트 화면마다 해석 카드 제공          |
| Drilldown Links         | Portfolio Risk -\> Symbol Lab, Market Regime -\> Index Lab 연결 | 운영 화면에서 분석 화면으로 이동 가능 |

- Research Hub는 Command Center를 복잡하게 만들지 않기 위한 분석 격리 공간이다.

- Command Center는 요약 조종석이고, Research Hub는 근거를 확인하는 분석실이다.

- 모든 그래프는 “해석 가능한 그래프”여야 하며 단순 차트 나열을 금지한다.

# 8. Phase 5: Event and News Intelligence

목표: 이벤트와 뉴스가 내 포지션에 미치는 영향을 연결한다.

| **Slice**             | **구현 내용**                                           | **완료 조건**                  |
|-----------------------|---------------------------------------------------------|--------------------------------|
| 5.1 Event Radar       | FOMC, CPI, NVIDIA 실적, Tesla 이벤트, SpaceX IPO window | events 테이블과 UI 캘린더 연동 |
| 5.2 Event Impact Map  | event -\> sectors -\> related holdings 연결             | 보유 종목 영향도 표시          |
| 5.3 News Feed         | 뉴스 기사 수집/수동 입력, ticker/theme 태깅             | News & Intelligence 목록 표시  |
| 5.4 News Impact       | 내 포지션 영향도 high/medium/low 산출                   | news_impacts 저장 및 표시      |
| 5.5 Event-linked News | 이벤트와 관련 뉴스 연결                                 | Event Radar에서 관련 뉴스 접근 |

뉴스 기능은 예측 도구가 아니다. 목표는 “내 포지션과 관련된 뉴스가 무엇이고, 어떤 위험/기회를 의미하는지”를 빠르게 이해하게 하는 것이다.

# 9. Phase 6: Journal/Reports

목표: 사용자의 실제 매매 행동을 복기 가능한 데이터로 만든다.

| **Slice**                 | **구현 내용**                                               | **완료 조건**                       |
|---------------------------|-------------------------------------------------------------|-------------------------------------|
| 6.1 Trade Journal         | thesis, catalyst, emotion, market_regime, mistake_tags 입력 | 거래별 복기 저장                    |
| 6.2 Performance by Regime | Regime별 승률/평균 R/손익                                   | Risk-On/Risk-Off 성과 비교          |
| 6.3 Mistake Analytics     | chasing, no stop, oversized 등 태그 분석                    | 반복 실수 상위 목록 표시            |
| 6.4 Weekly Report         | 계좌 변화, 주요 매매, 경고, 다음 주 watch point             | HTML/DOCX 또는 Markdown 리포트 생성 |
| 6.5 Goal Review           | 목표 달성 확률, 보호 모드 필요 여부                         | Goal Tracker와 연결                 |

# 10. 테스트/성능/완료 기준

| **영역**       | **테스트 기준**                                                                                        |
|----------------|--------------------------------------------------------------------------------------------------------|
| DB/Migration   | alembic upgrade/downgrade smoke, repository CRUD, seed idempotency                                     |
| Portfolio/Goal | 목표 진행률, drawdown, position limit guard 계산 테스트                                                |
| Market Signals | RSI/EMA/Bollinger 계산 정확성, timeframe별 upsert 테스트                                               |
| Regime         | 정해진 fixture 입력에 대해 regime과 decision_mode가 일관되게 산출                                      |
| Research Hub   | Index overlay, Symbol candlestick, chart interpretation card 렌더링 테스트                             |
| News/Event     | ticker/theme tagging, event impact map, news impact 저장 테스트                                        |
| UI Smoke       | 모든 탭이 sample data로 Streamlit 예외 없이 렌더링                                                     |
| Performance    | Command Center initial render \< 1.5s, Portfolio risk refresh \< 500ms, 20 tickers signal update \< 3s |

## Agent 작업 지시 원칙

- 각 phase는 독립 PR 또는 독립 branch로 진행한다.

- 기능 구현 전 스키마/모델/테스트 placeholder를 먼저 만든다.

- 임시 mock data를 쓰더라도 실제 DB 모델을 우회하지 않는다.

- LLM 기능은 항상 fallback 가능한 템플릿 해석을 먼저 구현한다.

- 차트 기능은 반드시 해석 카드와 함께 구현한다.

- 보안상 개인 계좌 정보, API key, DB dump는 저장소에 포함하지 않는다.

## 최종 MVP Definition of Done

1.  PostgreSQL이 Docker Compose로 실행되고 schema migration이 완료된다.

2.  현재 자산 57,000,000 KRW와 목표 100,000,000 KRW가 Goal Tracker에 표시된다.

3.  포지션을 수동 입력하고 종목당 1천만원 제한 및 섹터 노출 경고를 받을 수 있다.

4.  QQQ/SMH/TSLA 등 기본 universe의 OHLCV와 RSI/EMA/Bollinger 지표가 저장된다.

5.  Market Regime이 룰 기반으로 산출되고 자연어 해석으로 표시된다.

6.  Research Hub에서 Index Lab, Symbol Lab, News & Intelligence의 기본 화면이 동작한다.

7.  Event Radar가 주요 이벤트와 내 보유 종목의 영향도를 연결한다.

8.  Trade Journal에 매매 thesis와 결과를 기록하고 regime별 성과를 볼 수 있다.

9.  전체 앱이 sample data 기준으로 1.5초 내 Command Center를 표시한다.