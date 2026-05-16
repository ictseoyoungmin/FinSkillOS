# 03. FinSkillOS v2.1 DB / Data Model 설계서

PostgreSQL-first 데이터 구조와 Research Hub 확장 모델

| Version | Status | Updated |
|---|---|---|
| v2.1 | Review Draft | 2026-05-15 |

> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서 없이 읽어도 전체 맥락과 구현 기준을 이해할 수 있도록 작성되었습니다.

## 문서 목적

- FinSkillOS v2.1의 핵심 데이터 저장소와 데이터 흐름을 정의한다.

- Research Hub 확장에 필요한 Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 모델을 추가한다.

- 운영 화면은 빠르게, 분석 화면은 깊게 동작하도록 hot/cold data path를 분리한다.

- 장기적으로 매매 복기, Regime별 성과 분석, 이벤트 영향도 분석이 가능하도록 관계형 구조를 설계한다.

> **핵심 원칙:** MVP라도 데이터 구조는 낮추지 않는다. PostgreSQL-first, Snapshot-first, Research-ready 구조로 시작한다.

# 목차

- 1. 설계 방향
- 2. 전체 데이터 아키텍처
- 3. Core PostgreSQL Schema
- 4. Research Hub 확장 모델
- 5. 지표/차트 데이터 모델
- 6. 뉴스/이벤트 인텔리전스 모델
- 7. 최적화와 인덱스 전략
- 8. 마이그레이션 및 운영 원칙

# 1. 설계 방향

FinSkillOS v2.1은 단순 CSV 분석 도구가 아니라 개인 투자 운영체제이다. 따라서 데이터베이스는 단기 MVP용 임시 저장소가 아니라 장기 운영을 위한 core system database로 설계한다.

- PostgreSQL-first: 계좌, 포지션, 거래, Regime, 이벤트, 뉴스, 해석 결과의 source of truth를 PostgreSQL에 둔다.

- Research-ready: 지수 overlay, 캔들, 거래량, EMA, Bollinger Band, RSI, 뉴스 영향도까지 확장 가능한 구조를 선반영한다.

- Snapshot-first: Command Center는 매번 원천 데이터를 재계산하지 않고 최신 스냅샷을 읽는다.

- Append-only audit: 알림, 데이터 갱신, 해석 결과, 위험 경고는 추적 가능한 로그로 남긴다.

- MVP에서도 과소설계하지 않음: SQLite-only 구조는 지양하고 Docker 기반 PostgreSQL을 기본으로 한다.

## 핵심 데이터 원칙

| **원칙**                 | **의미**                                    | **적용 위치**                           |
|--------------------------|---------------------------------------------|-----------------------------------------|
| Source of Truth          | 중요 업무 데이터는 PostgreSQL에 저장        | 계좌, 포지션, 거래, 이벤트, 알림        |
| Cache as Acceleration    | 대용량 가격/지표는 Parquet/DuckDB 캐시 가능 | 장기 OHLCV, 지표 계산 결과              |
| Explainable State        | Regime과 Guard 판단 근거를 함께 저장        | market_regimes, alerts, interpretations |
| Position-aware Research  | 차트와 뉴스는 내 포지션 맥락과 연결         | symbol_context, news_impacts            |
| Timeframe-aware Charting | 분/시간/일/주/월 데이터를 구분              | market_bars, chart_presets              |

# 2. 전체 데이터 아키텍처

External Sources  
- Market OHLCV / Index / ETF / Macro  
- News / Events / User-entered Portfolio  
↓  
Data Services  
- MarketDataService / NewsService / PortfolioService / EventService  
↓  
PostgreSQL Core Store  
- accounts, positions, trades, market_bars, indicators, regimes, events, news, alerts  
↓  
Signal / Regime / Guard / Interpreter Services  
↓  
State Snapshots + UI Read Models  
↓  
Command Center / Market Regime / Portfolio Risk / Research Hub

| **저장 계층**   | **역할**                      | **예시 데이터**                                 |
|-----------------|-------------------------------|-------------------------------------------------|
| PostgreSQL      | 업무 데이터 source of truth   | 계좌, 포지션, 거래, 이벤트, 뉴스 영향도, Regime |
| Parquet/DuckDB  | 대량 시계열/분석 캐시         | 일봉/분봉 OHLCV, 장기 indicator cache           |
| JSONL           | 감사 로그와 append-only trace | scheduler log, guard log, data refresh log      |
| In-memory cache | UI 렌더링 속도 향상           | latest_state_snapshot, active_alerts            |

# 3. Core PostgreSQL Schema

아래 테이블은 FinSkillOS v2.1의 core schema이다. MVP 단계에서도 이 스키마 골격을 유지하면 이후 Research Hub와 Agent 기능 확장 시 마이그레이션 비용을 줄일 수 있다.

| **테이블**          | **핵심 책임**             | **주요 필드**                                                            |
|---------------------|---------------------------|--------------------------------------------------------------------------|
| accounts            | 계좌와 목표 단위          | id, name, base_currency, target_value, created_at                        |
| portfolio_snapshots | 일별 계좌 평가와 drawdown | snapshot_date, total_value, cash_value, peak_value, drawdown_pct         |
| positions           | 현재 보유 종목과 thesis   | ticker, sector, theme, strategy_type, market_value, pnl_pct, thesis      |
| trades              | 매매 일지와 복기 원천     | ticker, side, amount, reason, catalyst, emotion_state, market_regime     |
| market_bars         | 통합 OHLCV 시계열         | ticker, timeframe, bar_time, open, high, low, close, volume              |
| indicator_snapshots | 계산된 기술 지표          | rsi_14, ema_20, ema_60, bb_upper, bb_lower, macd, volume_zscore          |
| market_regimes      | 시장 상태 히스토리        | regime, risk_level, decision_mode, factors, summary                      |
| events              | 일정형 촉매               | title, start_date, end_date, affected_themes, related_tickers, risk_type |
| alerts              | Risk Guard 결과           | severity, guard_name, title, payload, resolved                           |
| interpretations     | 해석 결과 캐시            | cache_key, summary, explanation, suggested_actions                       |

## market_bars: 통합 가격 데이터

v2.1에서는 Symbol Lab과 Index Lab이 추가되므로 기존 일봉 중심 market_prices보다 timeframe-aware market_bars 구조가 적합하다.

```sql
CREATE TABLE market_bars (
id BIGSERIAL PRIMARY KEY,
ticker TEXT NOT NULL,
timeframe TEXT NOT NULL, -- 1m, 5m, 1h, 1d, 1w, 1mo
bar_time TIMESTAMPTZ NOT NULL,
open NUMERIC,
high NUMERIC,
low NUMERIC,
close NUMERIC,
adj_close NUMERIC,
volume NUMERIC,
source TEXT,
created_at TIMESTAMPTZ DEFAULT now(),
UNIQUE(ticker, timeframe, bar_time)
);
```

## indicator_snapshots: 기술 지표 저장

```sql
CREATE TABLE indicator_snapshots (
id BIGSERIAL PRIMARY KEY,
ticker TEXT NOT NULL,
timeframe TEXT NOT NULL,
snapshot_time TIMESTAMPTZ NOT NULL,
rsi_14 NUMERIC,
ema_20 NUMERIC,
ema_60 NUMERIC,
ema_120 NUMERIC,
bb_mid NUMERIC,
bb_upper NUMERIC,
bb_lower NUMERIC,
macd NUMERIC,
macd_signal NUMERIC,
volume_zscore NUMERIC,
trend_state TEXT,
created_at TIMESTAMPTZ DEFAULT now(),
UNIQUE(ticker, timeframe, snapshot_time)
);
```

# 4. Research Hub 확장 모델

Research Hub는 Index Lab, Symbol Lab, News & Intelligence, Sector Rotation으로 구성된다. 이 영역은 운영 탭보다 많은 데이터를 다루므로 별도의 read model과 user preference 모델이 필요하다.

| **하위 모듈**       | **필요 데이터**                              | **DB 모델**                                                     |
|---------------------|----------------------------------------------|-----------------------------------------------------------------|
| Index Lab           | 지수/ETF 가격, overlay, 상대강도             | market_bars, indicator_snapshots, index_universe, chart_presets |
| Symbol Lab          | 캔들, 거래량, EMA, Bollinger, 내 포지션 맥락 | market_bars, indicator_snapshots, positions, symbol_notes       |
| News & Intelligence | 뉴스, 요약, 영향도, 관련 종목/섹터           | news_articles, news_impacts, news_summaries                     |
| Sector Rotation     | 섹터별 성과, 상대강도, 모멘텀                | sector_map, sector_snapshots, sector_constituents               |

## 신규/확장 테이블

| **테이블**       | **목적**                 | **주요 필드**                                               |
|------------------|--------------------------|-------------------------------------------------------------|
| ticker_master    | 종목/ETF/지수 메타데이터 | ticker, name, asset_type, sector, theme, exchange, currency |
| watchlists       | 사용자 관심 종목 그룹    | name, description, created_at                               |
| watchlist_items  | 관심 종목 구성           | watchlist_id, ticker, display_order                         |
| chart_presets    | 차트 설정 저장           | name, tickers, timeframe, overlays, indicators              |
| symbol_notes     | 종목 thesis와 관찰 메모  | ticker, thesis, catalyst, risk_notes, updated_at            |
| sector_map       | 섹터/테마 표준화         | sector_key, display_name, benchmark_ticker                  |
| sector_snapshots | 섹터 모멘텀 스냅샷       | sector_key, return_1w, return_1m, rsi_14, momentum_score    |

# 5. 지표/차트 데이터 모델

차트 기능은 고성능 UI를 위해 원천 OHLCV와 계산된 지표를 분리한다. Symbol Lab은 캔들/거래량/EMA/Bollinger/RSI/MACD를 읽고, Index Lab은 normalized overlay와 relative strength를 읽는다.

| **차트 기능**     | **필요 데이터**                | **계산/저장 전략**                     |
|-------------------|--------------------------------|----------------------------------------|
| Candlestick       | open, high, low, close, volume | market_bars에서 timeframe별 조회       |
| Volume            | volume, volume_zscore          | market_bars + indicator_snapshots      |
| EMA               | close 기반 ema_20/60/120       | 증분 계산 후 indicator_snapshots 저장  |
| Bollinger Band    | bb_mid, bb_upper, bb_lower     | window=20 기본, timeframe별 저장       |
| RSI/MACD          | rsi_14, macd, macd_signal      | vectorized 계산 후 cache               |
| Overlay           | 정규화 가격 series             | UI 요청 시 계산 또는 materialized view |
| Relative Strength | ticker / benchmark ratio       | 섹터/지수 비교용 별도 snapshot 가능    |

권장 타임프레임은 1h, 1d, 1w, 1mo를 MVP 기본으로 하고, 1m/5m intraday는 데이터 소스 안정성이 확보된 후 확장한다.

# 6. 뉴스/이벤트 인텔리전스 모델

News & Intelligence는 원문 기사 나열이 아니라 “내 포지션에 어떤 영향을 줄 수 있는가”를 보여줘야 한다. 따라서 news_articles와 news_impacts를 분리한다.

```sql
CREATE TABLE news_articles (
id UUID PRIMARY KEY,
source TEXT,
title TEXT NOT NULL,
url TEXT UNIQUE,
published_at TIMESTAMPTZ,
tickers TEXT[],
themes TEXT[],
raw_summary TEXT,
sentiment TEXT, -- bullish, neutral, cautious, bearish
importance INT DEFAULT 3,
created_at TIMESTAMPTZ DEFAULT now()
);
```
  
```sql
CREATE TABLE news_impacts (
id UUID PRIMARY KEY,
article_id UUID REFERENCES news_articles(id),
account_id UUID REFERENCES accounts(id),
affected_positions JSONB,
impact_level TEXT, -- high, medium, low
interpretation TEXT,
watch_points JSONB,
created_at TIMESTAMPTZ DEFAULT now()
);
```

| **뉴스 처리 단계** | **출력**                         | **사용 화면**                  |
|--------------------|----------------------------------|--------------------------------|
| 수집               | title, url, source, published_at | News & Intelligence            |
| 태깅               | tickers, themes, event_link      | Event Radar, Symbol Lab        |
| 영향도 평가        | impact_level, affected_positions | Command Center, Portfolio Risk |
| 해석 생성          | summary, watch_points            | News & Intelligence            |
| 경고 연결          | alert payload                    | Risk Control                   |

# 7. 최적화와 인덱스 전략

PostgreSQL-first 구조는 장기 확장에 유리하지만, 시계열/차트/뉴스가 추가되면 인덱스와 캐시 전략이 필수적이다.

```sql
CREATE INDEX idx_market_bars_lookup
ON market_bars(ticker, timeframe, bar_time DESC);
```
```sql
CREATE INDEX idx_indicators_lookup
ON indicator_snapshots(ticker, timeframe, snapshot_time DESC);
```
```sql
CREATE INDEX idx_trades_account_date
ON trades(account_id, trade_date DESC);
```
```sql
CREATE INDEX idx_snapshots_account_date
ON portfolio_snapshots(account_id, snapshot_date DESC);
```
```sql
CREATE INDEX idx_events_window
ON events(start_date, end_date);
```
```sql
CREATE INDEX idx_news_published
ON news_articles(published_at DESC);
```
```sql
CREATE INDEX idx_news_tickers_gin
ON news_articles USING GIN(tickers);
```
```sql
CREATE INDEX idx_news_themes_gin
ON news_articles USING GIN(themes);
```
```sql
CREATE INDEX idx_alerts_active
ON alerts(resolved, severity, alert_date DESC);
```

| **최적화 대상**     | **전략**                                            |
|---------------------|-----------------------------------------------------|
| Command Center      | latest_state_snapshot 또는 materialized view만 읽기 |
| Research Hub charts | timeframe/ticker/date 인덱스 + 최근 기간 기본 조회  |
| Indicator 계산      | 전체 재계산 대신 lookback window 증분 계산          |
| News feed           | published_at + GIN(tickers/themes) 인덱스           |
| Portfolio guard     | current positions read model 기반 즉시 평가         |
| Reports             | 주간/월간 summary table을 사전 집계                 |

# 8. 마이그레이션 및 운영 원칙

- Alembic migration을 필수로 사용한다. 수동 ALTER TABLE은 금지한다.

- 처음부터 Docker Compose 기반 PostgreSQL을 개발 표준으로 둔다.

- 개인 투자 데이터는 민감 정보이므로 .env, DB dump, 로그 파일을 Git에 포함하지 않는다.

- 모든 외부 데이터 수집은 source와 fetched_at을 남겨 재현성을 확보한다.

- Regime, Guard, Interpretation 결과는 판단 근거와 함께 저장한다.

- MVP의 핵심은 완전 자동화가 아니라 신뢰 가능한 수동 입력 + 자동 해석 + 빠른 UI이다.

| **완료 기준** | **설명**                                                                       |
|---------------|--------------------------------------------------------------------------------|
| DB 기동       | docker compose로 PostgreSQL이 구동되고 DATABASE_URL로 연결된다.                |
| 마이그레이션  | core schema와 Research Hub 확장 테이블이 Alembic으로 생성된다.                 |
| Seed data     | 57,000,000 KRW 현재 자산, 100,000,000 KRW 목표, 기본 티커 universe가 입력된다. |
| 조회 성능     | Command Center read model 조회가 500ms 이하로 동작한다.                        |
| 테스트        | repository/service 단위 테스트와 migration smoke test가 통과한다.              |