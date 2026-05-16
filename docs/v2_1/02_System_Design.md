# FinSkillOS v2.1 시스템 설계서

> FinSkillOS v2.1 OS-style 아키텍처, 데이터 흐름, 모듈 경계 및 최적화 설계

| **문서 유형** | System Design                                               |
|---------------|-------------------------------------------------------------|
| **버전**      | v2.1                                                        |
| **작성 목적** | 개인 투자 운영체제형 FinSkillOS v2.1 개발 기준 문서         |
| **핵심 변경** | Research Hub, Index/Symbol/News 분석 영역, 해석 접근성 강화 |
| **작성일**    | 2026-05-15                                                  |

**핵심 문장: 차트는 근거이고, 상태 해석이 본문이며, 행동 모드가 결론이다.**

> **문서 사용 원칙**
>
> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서를 참조하지 않아도 제품 목적, 구조, 개발 범위를 이해할 수 있도록 작성되었습니다. v2.1은 v2.0을 대체하며 Research Hub, Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 확장을 포함합니다.

# 1. 설계 개요

본 문서는 FinSkillOS v2.1의 시스템 아키텍처를 정의한다. v2.1은 기존 OS-style 설계에 Research Hub 분석 영역을 추가하여 지수 그래프, 종목별 캔들/보조지표, 뉴스 인텔리전스, 섹터 로테이션을 공식 모듈로 포함한다.

> **설계 목표**
>
> FinSkillOS는 Streamlit 기반 MVP로 시작할 수 있지만, 데이터 모델과 서비스 경계는 PostgreSQL-first, OS-style, 확장 가능한 구조로 설계한다. MVP라는 이유로 데이터 구조를 다운그레이드하지 않는다.

# 2. 전체 아키텍처

```text
┌──────────────────────────────────────────────┐
│ UX Shell Layer │
│ Command Center / Operate Tabs / Research Hub │
├──────────────────────────────────────────────┤
│ Application Layer │
│ Goal / Portfolio / Event / Journal / Research │
├──────────────────────────────────────────────┤
│ Decision Layer │
│ Regime Engine / Risk Guards / Interpreter │
├──────────────────────────────────────────────┤
│ Signal & Analytics Layer │
│ RSI / EMA / Bollinger / Sector Rotation │
├──────────────────────────────────────────────┤
│ Kernel Layer │
│ Event Bus / Scheduler / State Manager / Rules │
├──────────────────────────────────────────────┤
│ Data Service Layer │
│ Market / Portfolio / News / Event Data │
├──────────────────────────────────────────────┤
│ Storage Layer │
│ PostgreSQL Core / Parquet Cache / JSONL Logs │
└──────────────────────────────────────────────┘
```

# 3. 레이어별 책임

| **레이어**         | **책임**                                                                                  |
|--------------------|-------------------------------------------------------------------------------------------|
| UX Shell           | 사용자 화면 구성, 탭 네비게이션, 상태/해석/위험/행동 모드 표시                            |
| Application        | Command Center, Portfolio, Event Radar, Goal Tracker, Trade Journal, Research Hub 앱 로직 |
| Decision           | Regime 판정, 리스크 가드, 지표 충돌 해석, 행동 모드 산출                                  |
| Signal & Analytics | RSI, EMA, Bollinger, MACD, 거래량, 상대강도, 섹터 모멘텀 계산                             |
| Kernel             | Event Bus, dependency graph, scheduler, state snapshot, rule orchestration                |
| Data Service       | 시장 가격, 포트폴리오, 이벤트, 뉴스, 매크로/심리 지표 수집 및 정규화                      |
| Storage            | PostgreSQL source of truth, Parquet price cache, JSONL audit log                          |

# 4. v2.1 모듈 구조

```text
finskillos/
config.py
db/
models/ repositories/ migrations/
kernel/
event_bus.py scheduler.py state_manager.py rule_engine.py
services/
portfolio_service.py market_data_service.py signal_service.py
regime_service.py interpretation_service.py risk_guard_service.py
goal_service.py event_service.py news_service.py research_service.py
signals/
technical.py sector.py macro.py portfolio.py
research/
index_lab.py symbol_lab.py news_intelligence.py sector_rotation.py
guards/
drawdown_guard.py concentration_guard.py overheat_guard.py event_risk_guard.py goal_guard.py
ui/
pages/ components/
optimization/
cache_manager.py incremental_compute.py dependency_graph.py profiler.py
observability/
metrics.py timing.py healthcheck.py
```

# 5. Storage Layer 설계

PostgreSQL은 시스템의 source of truth로 사용한다. 가격 시계열과 분석 캐시는 Parquet/DuckDB로 보조하고, 감사성 이벤트 로그는 JSONL로 append-only 저장한다.

| **저장소**      | **역할**                                                                         |
|-----------------|----------------------------------------------------------------------------------|
| PostgreSQL Core | accounts, positions, trades, snapshots, regimes, events, alerts, interpretations |
| Parquet Cache   | market_prices, indicator history, chart cache, backtest input                    |
| JSONL Logs      | scheduler log, guard log, interpreter log, data refresh log                      |
| Future Redis    | 실시간 알림/작업 큐가 필요할 때만 도입                                           |

# 6. Data Service Layer

- MarketDataService: 티커별 OHLCV, 지수/ETF, VIX, 금리, DXY 등 수집.

- PortfolioService: 수동 입력/CSV 업로드/향후 증권사 API를 통해 포지션과 계좌 스냅샷 수집.

- EventCalendarService: FOMC, CPI, NVIDIA 실적, Tesla 이벤트, SpaceX IPO window 등 이벤트 관리.

- NewsService: 종목/섹터/이벤트 뉴스 수집, 중복 제거, 관련 종목/섹터 매핑.

- CacheService: stale-while-revalidate, per-ticker incremental update, API 실패 시 마지막 정상 데이터 fallback.

# 7. Signal & Analytics Layer

| **신호 그룹**     | **계산 항목**                                                  |
|-------------------|----------------------------------------------------------------|
| Technical Signals | RSI, EMA 20/60/120, Bollinger Band, MACD, VWAP, 거래량 z-score |
| Macro Signals     | VIX regime, 금리 압력, 달러 압력, risk-on/risk-off 지표        |
| Sector Signals    | 반도체/우주/데이터센터/인프라/전력/AI SW 섹터 상대강도         |
| Portfolio Signals | drawdown, 현금 비중, 종목 집중도, 섹터 노출도, 전략 mix        |
| News Signals      | 뉴스 톤, 영향도, 보유 종목 관련성, 이벤트 연동성               |

# 8. Research Hub 설계

Research Hub는 v2.1에서 추가된 심화 분석 영역이다. 운영 화면의 복잡도를 늘리지 않기 위해 Index Lab, Symbol Lab, News & Intelligence, Sector Rotation으로 분리한다.

## 8.1 Index Lab

- 입력: SPY, QQQ, SMH, ARKX, SRVR, PAVE, VIX, DXY, TNX 등 지수/ETF 가격.

- 차트: 개별 차트, normalized overlay, relative strength, drawdown chart.

- 보조지표: EMA, Bollinger Band, RSI, MACD, Volume.

- 출력: 지수별 상태, 섹터별 주도력, risk-on/risk-off 해석.

## 8.2 Symbol Lab

- 입력: 개별 종목 OHLCV, 내 포지션, 관련 이벤트, 관련 뉴스.

- 차트: 시간봉/일봉/주봉/월봉, 캔들, 거래량, EMA, Bollinger, VWAP, RSI, MACD.

- 내 포지션 맥락: 평균단가, 수익률, 포트폴리오 비중, 종목당 1천만원 제한, thesis, stop loss/take profit.

- 출력: 종목 기술적 상태, 이벤트 노출, 포지션 위험, 다음 체크포인트.

## 8.3 News & Intelligence

- 뉴스 수집 후 market/sector/symbol/event-linked/position-relevant 카테고리로 분류한다.

- 뉴스 원문 저장은 최소화하고 title, source, published_at, url, summary, sentiment, related_tickers, related_events 메타데이터를 저장한다.

- 중요도는 뉴스 영향도, 보유 비중, 이벤트 근접도, 시장 regime 과열도를 조합해 산출한다.

- AI 요약은 캐시 기반으로 제공하며 같은 뉴스/같은 상태에서는 재생성하지 않는다.

## 8.4 Sector Rotation

- 섹터별 1주/1개월/3개월 수익률, RSI, 거래량, 상대강도, 모멘텀 점수 계산.

- 포트폴리오 섹터 노출과 시장 주도 섹터를 비교하여 crowding risk를 판단.

- 섹터 로테이션 변화는 Market Regime과 Portfolio Risk에 이벤트로 전파한다.

# 9. Kernel Layer 설계

Kernel은 데이터 갱신, 신호 계산, regime 판정, guard 실행, state snapshot 갱신을 조율한다. 모든 작업은 dependency graph를 기반으로 최소 재계산만 수행한다.

```text
MARKET_DATA_UPDATED
→ CALCULATE_TECHNICAL_SIGNALS
→ CALCULATE_SECTOR_MOMENTUM
→ UPDATE_REGIME
→ REFRESH_INTERPRETATION
PORTFOLIO_UPDATED
→ CALCULATE_EXPOSURE
→ RUN_RISK_GUARDS
→ UPDATE_GOAL
→ REFRESH_COMMAND_CENTER_SNAPSHOT
NEWS_UPDATED
→ MAP_NEWS_TO_SYMBOLS_AND_EVENTS
→ SCORE_NEWS_IMPACT
→ UPDATE_EVENT_RADAR
→ UPDATE_RESEARCH_HUB_NEWS
```

# 10. Regime Engine 설계

| **Regime**           | **의미**    | **행동 모드**       |
|----------------------|-------------|---------------------|
| PANIC                | 공포 과매도 | 관찰/분할 기회 검토 |
| RECOVERY             | 회복 초기   | 소액 진입 가능      |
| HEALTHY_BULL         | 안정 상승   | 정상 운용           |
| AGGRESSIVE_RISK_ON   | 강한 상승   | 공격 가능           |
| RISK_ON_OVERHEAT     | 과열 상승   | 신규 추격 제한      |
| DISTRIBUTION_RISK    | 분배 위험   | 익절/축소 경계      |
| DEFENSIVE_TRANSITION | 방어 전환   | 현금 확대           |
| RISK_OFF             | 위험 회피   | 단타 중단/방어      |

# 11. Interpretation Layer 설계

해석 레이어는 지표를 의미로 번역한다. 기본 해석은 룰/템플릿 기반으로 생성하고, LLM은 상세 리포트, 주간 복기, 지표 충돌 설명 요청 시에만 사용한다.

```text
입력 예시:
Fear & Greed = 84, VIX = 13.8, QQQ RSI = 72, SMH RSI = 78, TSLA RSI = 63
출력 예시:
현재 시장은 Risk-On 흐름이 유지되고 있으나 과열 신호가 증가하고 있습니다.
추세 붕괴보다는 신규 고점 추격 제한과 포지션 크기 관리가 중요한 구간입니다.
```

# 12. Decision Guard 설계

| **Guard**                  | **역할**                                               |
|----------------------------|--------------------------------------------------------|
| Drawdown Guard             | 고점 대비 -8%, -10%, -15% 경보 및 모드 전환            |
| Single Position Guard      | 종목당 1천만원 또는 설정 비중 초과 경고                |
| Sector Concentration Guard | AI CAPEX 연동 섹터 과집중 감지                         |
| Overheat Guard             | Fear & Greed, RSI, 거래량 과열 조합으로 신규 진입 제한 |
| Event Risk Guard           | 이벤트 전후 기대감 선반영/차익실현 위험 감지           |
| Goal Protection Guard      | 목표 1억원 근접 시 공격성 축소 및 조기 종료 준비       |

# 13. Application Layer 설계

| **앱**             | **설명**                                                             |
|--------------------|----------------------------------------------------------------------|
| Command Center App | state snapshot을 읽어 시장 상태, 목표, 리스크, 행동 모드를 즉시 표시 |
| Market Regime App  | regime history, 지표 해석, 지표 충돌 설명 표시                       |
| Portfolio Risk App | 보유 종목, 섹터 노출, 현금 비중, guard 경고 표시                     |
| Event Radar App    | 이벤트 캘린더, 포지션 영향도, 이벤트 연동 뉴스 표시                  |
| Goal Tracker App   | 목표 진행률, 시나리오, milestone mode, completion guard 표시         |
| Trade Journal App  | 매매 기록과 regime/섹터/실수 태그별 복기                             |
| Research Hub App   | Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 제공     |

# 14. UI 렌더링 전략

- Command Center는 state snapshot만 읽어 1.5초 이내 렌더링을 목표로 한다.

- Research Hub의 차트와 뉴스는 탭 진입 시 lazy load한다.

- Index/Symbol 차트는 최근 6개월을 기본값으로 하고 전체 기간은 옵션으로 제공한다.

- overlay 차트는 normalized price series를 캐싱한다.

- 복잡한 뉴스 요약과 주간 리포트는 on-demand 생성 후 DB에 캐시한다.

# 15. 최적화 설계

| **기법**                  | **적용 방식**                                                            |
|---------------------------|--------------------------------------------------------------------------|
| Snapshot-first            | 첫 화면은 DB snapshot만 읽는다.                                          |
| Incremental compute       | 가격/지표는 마지막 저장일 이후만 갱신한다.                               |
| Cache-heavy               | 차트 데이터, 해석 결과, 뉴스 요약을 캐시한다.                            |
| Rule-first interpretation | 기본 해석은 deterministic rule/template로 생성한다.                      |
| LLM-on-demand             | LLM은 상세 해석/주간 리포트/복기 요약에 한정한다.                        |
| Lazy rendering            | Research Hub와 무거운 차트는 사용자가 볼 때만 렌더링한다.                |
| Observability             | data load, signal compute, chart render, cache hit/miss를 로그로 남긴다. |

# 16. 성능 예산

| **작업**                      | **목표**                 |
|-------------------------------|--------------------------|
| Command Center initial render | \< 1.5s                  |
| Portfolio risk refresh        | \< 500ms                 |
| Regime calculation            | \< 300ms                 |
| Signal update for 20 tickers  | \< 3s                    |
| Full market data refresh      | \< 15s                   |
| Research Hub chart render     | \< 2s for cached data    |
| News impact refresh           | \< 5s after news fetch   |
| Weekly report generation      | \< 10s, cached afterward |

# 17. 데이터 흐름

```text
Market/News/Event/Portfolio Data
↓
Data Services normalize and cache
↓
Signal & Analytics compute indicators
↓
Regime Engine + Risk Guards evaluate state
↓
Interpreter creates natural-language summary
↓
State Snapshot stored in PostgreSQL
↓
UX Shell renders Command Center / Research Hub / Reports
```

# 18. 개발 우선순위

| **Phase** | **구현 범위**                                                    |
|-----------|------------------------------------------------------------------|
| 0         | PostgreSQL foundation, SQLAlchemy, Alembic, 기본 모델/Repository |
| 1         | Portfolio + Goal + Command Center snapshot                       |
| 2         | MarketData + RSI/EMA/Bollinger + Market Regime v1                |
| 3         | Risk Guards + Interpretation Layer                               |
| 4         | Research Hub v1: Index Lab + Symbol Lab 기본 차트                |
| 5         | News & Intelligence + Event Radar 연동                           |
| 6         | Trade Journal + Weekly Reflection Report                         |
| 7         | 성능 최적화, 캐시, observability, test hardening                 |

# 19. 테스트 전략

- DB model/repository unit tests: unique constraints, JSONB, index target 검증.

- Signal tests: RSI/EMA/Bollinger 계산 정확도와 결측 처리 검증.

- Regime tests: 입력 지표 조합별 상태 판정 검증.

- Guard tests: 종목당 1천만원 제한, drawdown, 섹터 집중, 목표 보호 룰 검증.

- Research tests: Index overlay 데이터 정규화, Symbol chart indicator load, 뉴스-종목-이벤트 매핑 검증.

- UI smoke tests: 핵심 탭 렌더링과 fallback 상태 검증.

# 20. v2.1 시스템 변경 요약

| **항목**    | **내용**                                                                       |
|-------------|--------------------------------------------------------------------------------|
| 추가 모듈   | research/index_lab.py, symbol_lab.py, news_intelligence.py, sector_rotation.py |
| 추가 서비스 | NewsService, ResearchService                                                   |
| 추가 데이터 | news_items, news_impacts, chart_cache, sector_rotation_snapshots 후보          |
| UI 변경     | Research Hub 도입, 운영 탭과 분석 탭 분리                                      |
| 최적화 변경 | Research Hub lazy rendering, normalized overlay cache, 뉴스 요약 캐시          |
| 제품 효과   | 차트/뉴스/계좌/이벤트/해석을 하나의 투자 OS로 연결                             |

# 21. v2.1 추가 데이터 후보

| **후보 테이블**           | **역할**                                                                      |
|---------------------------|-------------------------------------------------------------------------------|
| news_items                | 뉴스 제목, 출처, 발행시각, URL, 원문 요약, 중복 해시를 저장한다.              |
| news_impacts              | 뉴스와 ticker/theme/event/account exposure를 연결하고 영향도 점수를 저장한다. |
| chart_cache               | ticker, timeframe, indicator set 기준으로 렌더링용 시계열을 캐시한다.         |
| sector_rotation_snapshots | 섹터별 상대강도, RSI, 거래량, 모멘텀 점수를 일자별 저장한다.                  |
| research_annotations      | 사용자가 특정 차트/뉴스에 남긴 해석 메모와 후속 체크포인트를 저장한다.        |
