# 09. FinSkillOS v2.1 Test / Acceptance Criteria 문서

> 문서 상태: v2.1 독립 실행형 테스트 기준 문서  
> 대상 경로: `docs/v2_1/09_Test_Acceptance_Criteria.md`  
> 핵심 원칙: **FinSkillOS는 예측기가 아니라 리스크-aware 의사결정 OS이므로, 테스트는 계산 정확도뿐 아니라 해석 일관성, 안전장치, 데이터 장애 대응까지 검증해야 한다.**

---

## 1. 목적

본 문서는 FinSkillOS v2.1 개발 완료 여부를 판단하기 위한 테스트 전략과 Acceptance Criteria를 정의한다.

FinSkillOS v2.1은 다음 요소가 결합된 시스템이다.

```text
PostgreSQL-first 데이터 모델
시장 데이터 수집
기술 지표 계산
Regime Engine
Risk Guard
Goal Tracker
Research Hub
News & Intelligence
Event Radar
Trade Journal
Interpretation-first UI
```

따라서 테스트는 단순 UI smoke test에 그쳐서는 안 된다.  
핵심은 다음 질문에 답하는 것이다.

```text
1. 데이터가 올바르게 저장되고 다시 읽히는가?
2. 지표 계산이 재현 가능한가?
3. 시장 상태 판정이 룰북과 일치하는가?
4. Risk Guard가 위험한 행동을 빠르게 감지하는가?
5. UI가 차트보다 상태와 해석을 우선 보여주는가?
6. 외부 데이터 장애 상황에서도 앱이 사용 가능한가?
7. 투자자문으로 오해될 표현을 생성하지 않는가?
```

---

## 2. 테스트 레벨

FinSkillOS v2.1은 다음 계층별 테스트를 사용한다.

| 레벨 | 대상 | 목적 |
|---|---|---|
| Unit Test | 함수/룰/계산 | 계산 정확도 및 분기 검증 |
| Repository Test | DB 모델/쿼리 | 저장/조회/제약 검증 |
| Service Test | Portfolio, Signal, Regime 등 | 비즈니스 흐름 검증 |
| Integration Test | DB + Service + Cache | 실제 데이터 흐름 검증 |
| UI Smoke Test | Streamlit pages | 주요 화면 렌더링 검증 |
| Safety Test | 문구/해석/룰 | 투자자문 오해 방지 |
| Performance Test | Hot path | 초기 렌더링/계산 속도 검증 |
| Data Failure Test | Provider 장애 | stale fallback 검증 |

---

## 3. 테스트 도구

권장 도구:

```text
pytest
pytest-cov
pytest-mock
freezegun 또는 time-machine
ruff
mypy 또는 pyright 선택
playwright 또는 streamlit testing 선택
testcontainers 또는 docker compose 기반 PostgreSQL
```

초기에는 다음 명령을 기준으로 한다.

```bash
pytest
pytest --cov=finskillos
ruff check .
python -m compileall app.py finskillos
```

UI smoke test는 프로젝트 구조에 맞춰 별도 명령을 둔다.

```bash
pytest tests/ui
```

---

## 4. 테스트 데이터 원칙

테스트는 외부 API에 의존하지 않는다.

### 4.1 Fixture 디렉터리

```text
tests/fixtures/
  market_bars/
    sample_daily_bars.csv
    sample_intraday_bars.csv
  portfolio/
    sample_portfolio_snapshot.csv
    sample_positions_over_limit.csv
    sample_sector_concentrated.csv
  news/
    sample_news_articles.json
    sample_event_linked_news.json
  events/
    sample_events.json
  regimes/
    sample_regime_inputs.json
```

---

### 4.2 Deterministic Test

테스트는 날짜와 시간에 따라 결과가 바뀌면 안 된다.

권장:

```python
from freezegun import freeze_time

@freeze_time("2026-05-15 09:00:00")
def test_goal_projection():
    ...
```

---

## 5. DB / Data Model Acceptance Criteria

### DB-AC-001: Migration 적용

```text
Given 새 PostgreSQL DB
When alembic upgrade head 실행
Then 모든 v2.1 테이블이 생성되어야 한다.
```

필수 테이블:

```text
accounts
portfolio_snapshots
positions
trades
market_bars
indicator_snapshots
market_regimes
events
alerts
interpretations
news_articles
news_impacts
chart_presets
sector_snapshots
```

---

### DB-AC-002: Unique Constraint

```text
market_bars는 ticker + timestamp + timeframe + source 기준 중복 저장을 막아야 한다.
portfolio_snapshots는 account_id + snapshot_date 기준 중복 저장을 막아야 한다.
```

---

### DB-AC-003: JSONB 저장/조회

다음 필드는 JSONB 또는 배열 형태로 정상 저장/조회되어야 한다.

```text
events.affected_themes
events.related_tickers
alerts.payload
market_regimes.positive_factors
market_regimes.risk_factors
interpretations.suggested_actions
news_impacts.watch_next
```

---

### DB-AC-004: Index 존재

필수 인덱스:

```text
idx_market_bars_ticker_ts
idx_indicator_ticker_ts
idx_trades_account_date
idx_snapshots_account_date
idx_alerts_date_severity
idx_events_date
idx_news_ticker_date
```

---

## 6. Portfolio / Goal Tracker Acceptance Criteria

### PORT-AC-001: 포트폴리오 CSV Import

```text
Given sample_portfolio_snapshot.csv
When import_snapshot 실행
Then positions와 portfolio_snapshots가 정상 생성되어야 한다.
```

---

### PORT-AC-002: 계좌 요약 계산

입력:

```text
total_value = 57,000,000
target_value = 100,000,000
```

기대:

```text
progress_pct = 57.0
remaining = 43,000,000
```

---

### PORT-AC-003: 종목당 1천만원 제한

입력:

```text
TSLA market_value = 11,000,000
max_single_position_value = 10,000,000
```

기대:

```text
severity = YELLOW or RED
guard_name = MAX_SINGLE_POSITION_VALUE
```

---

### GOAL-AC-001: 목표 구간 판정

| 현재 평가금액 | 기대 goal mode |
|---:|---|
| 57,000,000 | GROWTH |
| 75,000,000 | BALANCED |
| 88,000,000 | PROTECTION |
| 97,000,000 | COMPLETION_GUARD |
| 100,000,000 이상 | CHALLENGE_COMPLETE |

---

### GOAL-AC-002: 1억 도달 시 조기 종료 상태

```text
Given total_value >= 100,000,000
Then goal_status = CHALLENGE_COMPLETE
And decision_mode must not encourage additional aggressive entries.
```

---

## 7. Market Data / Signal Acceptance Criteria

### DATA-AC-001: MarketBar Import

```text
Given sample_daily_bars.csv
When import_market_bars 실행
Then market_bars에 OHLCV가 저장되어야 한다.
```

---

### DATA-AC-002: Incremental Update

```text
Given TSLA market_bars가 2026-05-10까지 저장되어 있음
When 2026-05-11~2026-05-15 데이터 import
Then 기존 row는 중복 생성되지 않고 새 row만 추가되어야 한다.
```

---

### SIG-AC-001: RSI 계산

```text
Given 고정된 close series
When calculate_rsi_14 실행
Then expected RSI 값과 허용 오차 내 일치해야 한다.
```

허용 오차:

```text
abs(actual - expected) < 0.01
```

---

### SIG-AC-002: EMA 계산

```text
EMA 20 / 60 / 120이 pandas ewm 기준과 일치해야 한다.
```

---

### SIG-AC-003: Bollinger Band 계산

```text
bb_mid = SMA20
bb_upper = SMA20 + 2 * std20
bb_lower = SMA20 - 2 * std20
```

---

### SIG-AC-004: Indicator Snapshot 저장

```text
Given indicator 계산 완료
Then indicator_snapshots에 ticker, ts, timeframe별 결과가 저장되어야 한다.
```

---

## 8. Regime Engine Acceptance Criteria

### REG-AC-001: Risk-On Overheat 판정

입력 예:

```json
{
  "fear_greed": 84,
  "vix": 13.5,
  "qqq_rsi": 72,
  "smh_rsi": 78,
  "sector_momentum": "strong"
}
```

기대:

```text
regime = RISK_ON_OVERHEAT
risk_level = YELLOW or ORANGE
decision_mode = HOLD_WINNERS_LIMIT_NEW_ENTRIES
```

---

### REG-AC-002: Risk-Off 판정

입력 예:

```json
{
  "fear_greed": 22,
  "vix": 28,
  "qqq_rsi": 38,
  "smh_rsi": 35,
  "sector_momentum": "weak"
}
```

기대:

```text
regime = RISK_OFF
decision_mode = DEFENSIVE_MODE
```

---

### REG-AC-003: Recovery 판정

입력 예:

```json
{
  "fear_greed": 35,
  "vix": 19,
  "qqq_rsi": 48,
  "qqq_trend": "recovering",
  "sector_momentum": "improving"
}
```

기대:

```text
regime = RECOVERY
decision_mode = SMALL_ENTRIES_ALLOWED
```

---

### REG-AC-004: 해석 충돌 처리

입력:

```text
RSI high
VIX low
sector momentum strong
Fear & Greed greed
```

기대 해석:

```text
과열 신호는 존재하지만 추세 붕괴 신호는 아니며,
신규 추격 진입 제한과 기존 강세 포지션 관리가 우선이라는 설명이 생성되어야 한다.
```

---

## 9. Risk Guard Acceptance Criteria

### GUARD-AC-001: Drawdown Guard

입력:

```text
peak_value = 62,000,000
current_value = 56,500,000
drawdown_pct = -8.87%
```

기대:

```text
severity = YELLOW
guard_name = DRAWDOWN_GUARD
message includes "고점 대비"
```

---

### GUARD-AC-002: Sector Concentration Guard

입력:

```text
Technology + AI Infra exposure = 68%
limit = 60%
```

기대:

```text
severity = YELLOW or RED
guard_name = SECTOR_CONCENTRATION
```

---

### GUARD-AC-003: Cash Ratio Guard

입력:

```text
cash_ratio = 5%
min_cash_ratio = 10%
```

기대:

```text
severity = YELLOW
guard_name = MIN_CASH_RATIO
```

---

### GUARD-AC-004: Event Risk Guard

입력:

```text
portfolio has TSLA/RKLB/ASTS exposure
upcoming event = SpaceX IPO Window
market regime = RISK_ON_OVERHEAT
```

기대:

```text
event_risk_score >= threshold
alert generated
message mentions event-driven volatility or 기대감 선반영
```

---

### GUARD-AC-005: Overtrading Guard

입력:

```text
same-day trades count > configured limit
recent loss trades exist
```

기대:

```text
warning against revenge trading / 복구 매매
```

직접적 투자 지시가 아니라 위험 경고 문구여야 한다.

---

## 10. Interpretation / Safety Acceptance Criteria

### SAFE-AC-001: 금지 표현

생성 문구에는 다음 표현이 없어야 한다.

```text
무조건 매수
반드시 매도
수익 보장
확실한 상승
원금 보장
지금 사라
지금 팔아라
```

---

### SAFE-AC-002: 허용 표현

다음과 같은 표현은 허용된다.

```text
신규 추격 진입은 신중해야 합니다.
기존 포지션 관리를 우선하세요.
현금 비중을 확인하세요.
이벤트 전후 변동성 확대 가능성을 점검하세요.
```

---

### SAFE-AC-003: 비투자자문 고지

Reports 또는 Settings / Data에는 다음 원칙이 명시되어야 한다.

```text
FinSkillOS는 투자 자문 도구가 아니며, 매수/매도 지시를 제공하지 않습니다.
본 시스템은 사용자의 시장 상태 해석, 리스크 점검, 매매 복기를 지원합니다.
```

---

## 11. UI / UX Acceptance Criteria

### UI-AC-001: Command Center First Paint

Command Center는 다음 요소를 첫 화면에서 표시해야 한다.

```text
- Market State Banner
- Goal Progress
- Portfolio Value
- Today Decision Mode
- Key Risk Alerts
- AI / Rule-based Interpretation Summary
```

---

### UI-AC-002: 차트보다 해석 우선

Market Regime, Index Lab, Symbol Lab에는 다음 세 문장이 포함되는 구조여야 한다.

```text
What happened?
What does it mean?
What should I watch next?
```

또는 이에 준하는 한글 해석 블록.

---

### UI-AC-003: Research Hub 하위 탭

Research Hub는 다음 하위 탭을 가져야 한다.

```text
Index Lab
Symbol Lab
News & Intelligence
Sector Rotation
```

---

### UI-AC-004: Symbol Lab 포지션 맥락

Symbol Lab에서 보유 종목을 선택하면 다음 정보가 표시되어야 한다.

```text
- 평균단가
- 현재 수익률
- 포트폴리오 비중
- 관련 이벤트
- thesis
- stop_loss / take_profit
```

---

### UI-AC-005: News & Intelligence 포지션 영향도

뉴스 카드는 단순 제목 나열이 아니라 다음을 포함해야 한다.

```text
- 관련 종목
- 관련 theme
- 내 포트폴리오 노출도
- 영향 수준
- AI/rule summary
- watch next
```

---

## 12. Event Radar Acceptance Criteria

### EVENT-AC-001: 이벤트 등록

```text
Given 이벤트 수동 입력
When 저장
Then events 테이블에 related_tickers와 affected_themes가 저장되어야 한다.
```

---

### EVENT-AC-002: 이벤트-포지션 연결

```text
Given TSLA 보유
And event.related_tickers includes TSLA
Then Event Radar는 이 이벤트를 "position relevant"로 표시해야 한다.
```

---

### EVENT-AC-003: 이벤트 위험 점수

```text
event_risk_score는 importance, exposure, days_to_event, market_overheat를 반영해야 한다.
```

---

## 13. Trade Journal Acceptance Criteria

### JOURNAL-AC-001: 매매 일지 입력

필수 필드:

```text
ticker
trade_date
side
strategy_type
amount
reason
catalyst
emotion_state
market_regime
```

---

### JOURNAL-AC-002: Mistake Tags

다음 태그를 지원해야 한다.

```text
chasing
no_stop
oversized
revenge_trade
weak_thesis
event_overexpectation
late_entry
early_exit
```

---

### JOURNAL-AC-003: Regime별 성과 집계

```text
Risk-On
Neutral
Risk-Off
Overheat
```

각 regime별 승률, 평균 R, 총손익을 집계할 수 있어야 한다.

---

## 14. Data Failure Acceptance Criteria

### FAIL-AC-001: Market Data Provider Failure

```text
Given market data provider raises error
When app refresh
Then app must not crash
And previous cache is shown with stale warning
```

---

### FAIL-AC-002: News Provider Failure

```text
Given news provider failure
Then News & Intelligence shows "news temporarily unavailable"
And Command Center still renders
```

---

### FAIL-AC-003: Empty Portfolio

```text
Given no positions
Then Command Center renders setup guide
And no division-by-zero error occurs
```

---

### FAIL-AC-004: Missing Indicator

```text
Given RSI is unavailable for a new ticker
Then UI shows insufficient history state
And Regime Engine does not crash
```

---

## 15. Performance Acceptance Criteria

| 기능 | 목표 |
|---|---:|
| Command Center initial render | < 1.5s |
| Portfolio risk refresh | < 500ms |
| Regime calculation | < 300ms |
| Signal update for 20 tickers | < 3s |
| Full market data refresh | < 15s |
| News impact scoring for 100 articles | < 3s |
| Weekly report generation | < 10s |
| UI tab change without refresh | < 500ms |

테스트 환경에 따라 수치는 완화 가능하지만, 성능 회귀를 감지할 수 있어야 한다.

---

## 16. 테스트 파일 구조

```text
tests/
  unit/
    test_technical_indicators.py
    test_goal_tracker.py
    test_regime_engine.py
    test_risk_guards.py
    test_interpretation_safety.py

  integration/
    test_db_migrations.py
    test_portfolio_import_flow.py
    test_market_data_flow.py
    test_news_event_flow.py

  ui/
    test_command_center_smoke.py
    test_research_hub_smoke.py

  fixtures/
    ...
```

---

## 17. CI Acceptance

GitHub Actions 또는 로컬 CI에서 최소 다음을 실행한다.

```bash
python -m compileall app.py finskillos
ruff check .
pytest
```

선택:

```bash
pytest --cov=finskillos --cov-report=term-missing
mypy finskillos
```

---

## 18. Release Gate

MVP 릴리즈 전 다음 조건을 만족해야 한다.

```text
[ ] DB migration passes from empty DB.
[ ] Sample portfolio can be imported.
[ ] Command Center renders without external API.
[ ] Market Regime can be calculated from fixtures.
[ ] Risk Guards produce expected alerts.
[ ] Research Hub has Index Lab and Symbol Lab skeletons.
[ ] News & Intelligence can render sample news impacts.
[ ] Event Radar can link events to holdings.
[ ] Trade Journal can save and summarize entries.
[ ] No direct buy/sell recommendation language appears.
[ ] All tests pass.
```

---

## 19. 요약

FinSkillOS v2.1의 테스트는 다음을 보장해야 한다.

```text
계산은 재현 가능해야 한다.
룰은 문서와 일치해야 한다.
UI는 해석 우선이어야 한다.
데이터 장애에도 앱은 살아야 한다.
Risk Guard는 빠르게 동작해야 한다.
문구는 투자자문으로 오해되지 않아야 한다.
```
