# 08. FinSkillOS v2.1 API / Data Source 설계서

> 문서 상태: v2.1 독립 실행형 설계 문서  
> 대상 경로: `docs/v2_1/08_API_Data_Source_Design.md`  
> 상위 기준: FinSkillOS v2.1 제품 기획서, 시스템 설계서, DB/Data Model 설계서, UI/UX 설계서, Regime/Risk Guard 룰북  
> 핵심 원칙: **데이터는 판단의 재료이고, FinSkillOS의 출력은 투자 추천이 아니라 해석 가능한 운영 상태다.**

---

## 1. 목적

본 문서는 FinSkillOS v2.1에서 사용하는 외부/내부 데이터 소스와 API 흐름을 정의한다.

FinSkillOS v2.1은 단순 주가 차트 앱이 아니라 다음 기능을 수행하는 개인 투자 운영체제다.

- 시장 상태 감지
- 포트폴리오 위험 제어
- 이벤트/뉴스 촉매 해석
- 목표 1억 달성까지의 진행률 관리
- 매매 복기 및 행동 오류 감지
- Research Hub 기반 심화 차트/뉴스 분석

따라서 API/Data Source 설계의 목표는 “많은 데이터를 가져오는 것”이 아니라, **의사결정에 필요한 데이터를 안정적으로, 재현 가능하게, 지연 없이 공급하는 것**이다.

---

## 2. 설계 원칙

### 2.1 Source-of-Truth 분리

FinSkillOS는 모든 데이터를 같은 수준으로 신뢰하지 않는다.

| 데이터 종류 | 신뢰 수준 | 저장 위치 | 비고 |
|---|---:|---|---|
| 사용자 계좌/포지션 입력 | 최고 | PostgreSQL | 사용자가 입력한 값이 계좌 판단의 기준 |
| 매매 일지 | 최고 | PostgreSQL | 복기/성과 분석 기준 |
| 목표 설정 | 최고 | PostgreSQL | Goal Engine 기준 |
| 시장 가격 데이터 | 중간~높음 | PostgreSQL + Parquet Cache | 소스 품질에 따라 등급 부여 |
| 뉴스 데이터 | 중간 | PostgreSQL | 중복/노이즈 제거 필요 |
| 이벤트 일정 | 중간~높음 | PostgreSQL | 수동 검증 가능해야 함 |
| AI 해석 결과 | 보조 | PostgreSQL cache | 룰/지표의 설명 레이어 |
| 실시간성 데이터 | 가변 | Cache | stale policy 필요 |

---

### 2.2 Provider-Agnostic 설계

특정 데이터 공급자에 종속되지 않도록 Adapter 패턴을 사용한다.

```text
External Provider
    ↓
Provider Adapter
    ↓
Canonical DTO
    ↓
Validation / Normalization
    ↓
Repository
    ↓
PostgreSQL / Parquet Cache
```

예:

```text
YFinanceAdapter
PolygonAdapter
FinnhubAdapter
AlphaVantageAdapter
ManualCsvAdapter
```

모든 Adapter는 내부 표준 모델로 변환되어야 한다.

---

### 2.3 Dev Source와 Production Source 분리

MVP 개발 단계에서는 무료/저비용 데이터 소스를 사용할 수 있다.  
그러나 FinSkillOS는 투자 운영 보조 도구이므로, 최종적으로는 데이터 안정성이 중요하다.

| 구분 | 목적 | 예시 |
|---|---|---|
| Dev Source | 개발/테스트/목업 | yfinance, sample CSV, 수동 입력 |
| Semi-Production Source | 개인 운영 | Alpha Vantage, Finnhub, Tiingo, EODHD 등 후보 |
| Production-Grade Source | 장기 운영/정확도 우선 | Polygon, Nasdaq Data Link, 유료 마켓데이터 벤더 등 후보 |

> 실제 공급자 선택 전에는 가격, 이용약관, 지연시간, rate limit, 재배포 제한, 뉴스 사용권을 반드시 확인한다.

---

### 2.4 Stale-While-Revalidate

앱이 데이터 소스 장애 때문에 열리지 않으면 안 된다.

기본 정책:

```text
1. 최신 캐시가 있으면 먼저 표시한다.
2. 백그라운드 또는 수동 refresh로 새 데이터를 받는다.
3. 실패하면 기존 캐시를 stale 상태로 표시한다.
4. stale 상태가 길어지면 Command Center에 Data Health 경고를 띄운다.
```

---

### 2.5 해석 우선 데이터 공급

Research Hub는 차트와 뉴스를 깊게 보여주지만, Command Center와 Market Regime은 핵심 상태만 빠르게 보여줘야 한다.

따라서 API Layer는 두 경로를 분리한다.

```text
Hot Path:
- latest state snapshot
- latest portfolio snapshot
- latest regime
- active alerts
- today decision mode

Cold Path:
- full chart data
- historical overlays
- news archive
- scenario simulation
- weekly report
```

---

## 3. 데이터 도메인

FinSkillOS v2.1에서 필요한 데이터 도메인은 다음과 같다.

```text
1. Portfolio Data
2. Market Bars
3. Technical Indicators
4. Macro / Sentiment Data
5. News Data
6. Event Calendar
7. Sector / Theme Mapping
8. Interpretation Cache
9. Audit / Refresh Logs
```

---

## 4. Portfolio Data

### 4.1 입력 방식

초기 MVP에서는 증권사 API 연동을 우선하지 않는다.  
대신 다음 세 가지 입력을 지원한다.

```text
1. 수동 입력
2. CSV 업로드
3. 템플릿 기반 포트폴리오 스냅샷 import
```

증권사 API 연동은 보안, 인증, 장애 대응, 약관 문제가 있으므로 후순위로 둔다.

---

### 4.2 표준 포트폴리오 입력 스키마

```csv
account_name,snapshot_date,ticker,name,sector,theme,strategy_type,quantity,avg_price,market_price,cost_basis,market_value,pnl,pnl_pct,stop_loss,take_profit,thesis
Main,2026-05-15,TSLA,Tesla,Consumer Discretionary,Musk Ecosystem,swing,20,350,390,7000000,7800000,800000,11.4,360,430,"SpaceX IPO sentiment + rebound thesis"
```

---

### 4.3 내부 저장 흐름

```text
CSV / Manual Input
    ↓
PortfolioInputDTO
    ↓
Validation
    ↓
positions
portfolio_snapshots
    ↓
Risk Guard
Goal Engine
Command Center Snapshot
```

---

## 5. Market Bars

### 5.1 대상 티커

초기 기본 watch universe:

```text
Core Index / ETF:
- SPY
- QQQ
- SMH
- ARKX
- SRVR
- PAVE
- VIX proxy
- DXY proxy
- TNX / 10Y yield proxy

High-interest Symbols:
- TSLA
- NVDA
- RKLB
- ASTS
- PLTR
- AAPL
- MSFT
- AMZN
```

사용자는 Settings / Data에서 watchlist를 추가/삭제할 수 있어야 한다.

---

### 5.2 Timeframe

Symbol Lab과 Index Lab은 여러 시간 단위를 지원한다.

| Timeframe | 목적 | 기본 저장 |
|---|---|---|
| 1m / 5m / 15m | 단기 확인 | 선택적, 캐시 중심 |
| 1h | 장중 흐름 | 선택적 |
| 1d | 기본 분석 | 필수 |
| 1w | 중기 추세 | 계산/저장 |
| 1mo | 장기 추세 | 계산/저장 |

MVP에서는 일봉 중심으로 시작하고, 시간봉은 Adapter 구조만 열어둔다.

---

### 5.3 Canonical MarketBar DTO

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class MarketBarDTO:
    ticker: str
    ts: datetime
    timeframe: str
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: Decimal | None
    source: str
    adjusted: bool = True
```

---

### 5.4 DB 저장 테이블

주요 테이블:

```text
market_bars
```

권장 필드:

```text
id
ticker
ts
timeframe
open
high
low
close
adj_close
volume
source
is_adjusted
created_at
updated_at
UNIQUE(ticker, ts, timeframe, source)
```

---

### 5.5 증분 업데이트 정책

전체 데이터를 매번 다시 받지 않는다.

```text
1. ticker + timeframe별 마지막 ts 확인
2. last_ts 이후 데이터만 요청
3. 중복 row는 upsert
4. 새 데이터가 들어온 ticker만 indicator 재계산
```

---

## 6. Technical Indicator Data

### 6.1 계산 대상

Index Lab / Symbol Lab / Market Regime에서 공통 사용한다.

```text
- EMA 5 / 20 / 60 / 120
- SMA 20 / 60 / 120
- Bollinger Band 20, 2σ
- RSI 14
- MACD 12/26/9
- Volume moving average
- Volume z-score
- Drawdown
- Relative strength
```

---

### 6.2 계산 위치

외부 공급자가 제공하는 지표를 그대로 쓰지 않고, 기본 지표는 내부에서 계산한다.

이유:

```text
- 계산 기준 통일
- 백테스트 재현성
- 지표 변경 이력 관리
- Provider dependency 감소
```

---

### 6.3 IndicatorSnapshot DTO

```python
@dataclass
class IndicatorSnapshotDTO:
    ticker: str
    ts: datetime
    timeframe: str
    rsi_14: float | None
    ema_20: float | None
    ema_60: float | None
    ema_120: float | None
    bb_mid: float | None
    bb_upper: float | None
    bb_lower: float | None
    macd: float | None
    macd_signal: float | None
    volume_zscore: float | None
    momentum_score: float | None
    trend_state: str | None
```

---

### 6.4 재계산 정책

```text
EMA/RSI/MACD:
- 새 bar가 들어온 ticker만 재계산
- 기본은 최근 200개 bar window 재계산
- 전체 재계산은 수동 maintenance command로만 실행

Bollinger Band:
- 최근 60~120개 window로 충분

Relative Strength:
- 비교 대상 index가 갱신된 경우 연동 재계산
```

---

## 7. Macro / Sentiment Data

### 7.1 필요 지표

```text
- Fear & Greed
- VIX
- 10Y Treasury Yield
- Dollar Index
- CPI / PPI 일정 및 결과
- FOMC 일정
- 시장 breadth proxy
```

---

### 7.2 저장 테이블

```text
macro_snapshots
sentiment_snapshots
```

권장 필드:

```text
id
metric_name
metric_value
metric_state
as_of
source
payload_json
created_at
```

---

### 7.3 갱신 주기

| 지표 | 갱신 주기 | UI 표시 |
|---|---:|---|
| Fear & Greed | 일 1회 | stale 허용 |
| VIX | 장중/일 1회 | 중요 |
| 10Y Yield | 일 1회 | 중요 |
| DXY | 일 1회 | 보조 |
| CPI/PPI/FOMC | 일정 변경 시 | Event Radar |
| Breadth proxy | 일 1회 | Market Regime |

---

## 8. News Data

### 8.1 뉴스의 역할

FinSkillOS에서 뉴스는 원문 나열용이 아니다.

뉴스는 다음 질문에 답해야 한다.

```text
이 뉴스가 내 보유 종목에 영향을 주는가?
이 뉴스가 현재 시장 regime을 강화하는가, 약화하는가?
이 뉴스가 이벤트 기대감을 과열시키는가?
좋은 뉴스인데 주가 반응이 약한가?
```

---

### 8.2 뉴스 분류

```text
- Market News
- Macro News
- Sector News
- Symbol News
- Event-linked News
- Position-relevant News
```

---

### 8.3 NewsArticle DTO

```python
@dataclass
class NewsArticleDTO:
    source: str
    title: str
    url: str
    published_at: datetime
    summary: str | None
    tickers: list[str]
    themes: list[str]
    sentiment: str | None
    importance: int | None
    raw_payload: dict
```

---

### 8.4 NewsImpact DTO

```python
@dataclass
class NewsImpactDTO:
    article_id: str
    affected_tickers: list[str]
    affected_themes: list[str]
    portfolio_exposure_pct: float
    impact_level: str       # LOW / MEDIUM / HIGH
    sentiment_state: str    # BULLISH / NEUTRAL / CAUTIOUS / RISK_OFF
    interpretation: str
    watch_next: list[str]
```

---

### 8.5 뉴스 처리 흐름

```text
News Provider
    ↓
News Adapter
    ↓
Deduplication
    ↓
Ticker / Theme Mapping
    ↓
Position Impact Scoring
    ↓
News Interpretation
    ↓
news_articles
news_impacts
    ↓
News & Intelligence UI
Event Radar UI
Command Center Alerts
```

---

### 8.6 중복 제거

중복 뉴스가 많기 때문에 다음 키를 사용한다.

```text
normalized_title_hash
source
published_date
url_hash
```

유사 제목 중복은 후속 단계에서 embedding 또는 fuzzy matching으로 확장 가능하다.

---

## 9. Event Calendar Data

### 9.1 이벤트 유형

```text
- Earnings
- Macro Event
- Fed / Rate Event
- Product Event
- Space Launch
- IPO Window
- Regulatory Event
- Policy / Infrastructure Event
```

---

### 9.2 Event DTO

```python
@dataclass
class EventDTO:
    title: str
    event_type: str
    start_date: str
    end_date: str | None
    affected_themes: list[str]
    related_tickers: list[str]
    importance: int
    risk_type: str
    description: str | None
    source_url: str | None
```

---

### 9.3 이벤트 위험 점수

```text
event_risk_score =
  event_importance
  × portfolio_exposure_weight
  × days_to_event_weight
  × market_overheat_weight
```

예:

```text
SpaceX IPO Window
- importance: 5
- affected themes: space, musk_ecosystem, ai_infra
- related holdings: TSLA, RKLB, ASTS
- risk_type: event_hype_reversal
```

---

## 10. Sector / Theme Mapping

### 10.1 목적

종목 단위 분산이 실제 리스크 분산이 아닐 수 있다.

예:

```text
TSLA
NVDA
SMH
PLTR
Data center infra
```

모두 다른 종목처럼 보여도 하나의 “AI CAPEX / Growth Risk-On” 요인에 묶일 수 있다.

---

### 10.2 기본 Theme Taxonomy

```text
- semiconductor
- ai_infra
- data_center
- power_infrastructure
- space
- musk_ecosystem
- mega_cap_tech
- software_ai
- defense
- macro_rate_sensitive
- cash
```

---

### 10.3 Mapping Table

```text
ticker_theme_map
```

필드:

```text
ticker
sector
primary_theme
secondary_themes
risk_factor_group
updated_at
```

---

## 11. Internal API / Service Interface

초기에는 FastAPI 없이 Streamlit + Service Layer로 구현한다.  
하지만 내부 서비스 인터페이스는 API처럼 명확히 정의한다.

---

### 11.1 PortfolioService

```python
class PortfolioService:
    def import_snapshot(self, account_id, rows): ...
    def get_current_positions(self, account_id): ...
    def get_portfolio_summary(self, account_id): ...
    def calculate_exposure(self, account_id): ...
```

---

### 11.2 MarketDataService

```python
class MarketDataService:
    def refresh_bars(self, tickers, timeframe="1d"): ...
    def get_bars(self, ticker, timeframe, start, end): ...
    def get_latest_price(self, ticker): ...
```

---

### 11.3 SignalService

```python
class SignalService:
    def compute_indicators(self, ticker, timeframe="1d"): ...
    def compute_sector_momentum(self): ...
    def get_latest_indicators(self, tickers): ...
```

---

### 11.4 RegimeService

```python
class RegimeService:
    def evaluate_today_regime(self): ...
    def get_latest_regime(self): ...
    def get_regime_history(self, days=30): ...
```

---

### 11.5 NewsService

```python
class NewsService:
    def refresh_news(self, tickers, themes): ...
    def get_position_relevant_news(self, account_id, days=7): ...
    def compute_news_impacts(self, account_id): ...
```

---

### 11.6 EventService

```python
class EventService:
    def upsert_event(self, event): ...
    def get_upcoming_events(self, days=30): ...
    def compute_event_risk(self, account_id): ...
```

---

## 12. Cache Policy

### 12.1 Cache Key

```text
{domain}:{provider}:{ticker}:{timeframe}:{start}:{end}
```

예:

```text
market:yfinance:TSLA:1d:2025-01-01:2026-05-15
news:finnhub:TSLA:2026-05-01:2026-05-15
```

---

### 12.2 Cache TTL

| Domain | TTL |
|---|---:|
| daily price bars | 12~24h |
| intraday bars | 1~15m |
| news | 15~60m |
| event calendar | 24h |
| macro snapshots | 12~24h |
| interpretation | until input state changes |
| chart presets | permanent until user changes |

---

## 13. Data Health

Command Center에는 Data Health 상태가 있어야 한다.

```text
Data Health: OK / Stale / Partial / Failed
```

### 13.1 Data Health 계산

```text
OK:
- 핵심 데이터가 TTL 내 갱신됨

Stale:
- 일부 데이터가 TTL 초과
- 이전 캐시는 사용 가능

Partial:
- 일부 provider 실패
- 핵심 화면은 표시 가능

Failed:
- 핵심 데이터 없음
- 사용자 입력/캐시 확인 필요
```

---

## 14. Security / Secrets

API Key는 코드에 저장하지 않는다.

`.env` 예시:

```bash
DATABASE_URL=postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos

MARKET_DATA_PROVIDER=yfinance
NEWS_PROVIDER=none

POLYGON_API_KEY=
FINNHUB_API_KEY=
ALPHA_VANTAGE_API_KEY=
NEWS_API_KEY=

APP_ENV=local
```

---

## 15. Licensing / Compliance

데이터 공급자별로 다음을 확인한다.

```text
- 개인 사용 가능 여부
- 상업적 사용 가능 여부
- 데이터 재배포 금지 여부
- 뉴스 원문 저장 가능 여부
- 지연 데이터 표시 조건
- API rate limit
- attribution 요구사항
```

FinSkillOS는 외부 데이터를 재판매하거나 공개 배포하지 않는 개인 운영 도구로 시작한다.  
향후 public service로 바꾸려면 데이터 라이선스 검토가 별도로 필요하다.

---

## 16. MVP 구현 범위

### Phase API-0: Adapter Interface

- `BaseMarketDataAdapter`
- `BaseNewsAdapter`
- `BaseMacroAdapter`
- 공통 DTO 정의

### Phase API-1: Manual / CSV Portfolio Input

- 수동 입력
- CSV import
- validation
- DB 저장

### Phase API-2: Market Bars

- 기본 watchlist
- 일봉 가격 수집
- `market_bars` 저장
- 증분 업데이트

### Phase API-3: Indicators

- RSI
- EMA
- Bollinger Band
- MACD
- indicator snapshot 저장

### Phase API-4: News & Events

- 뉴스 저장 스키마
- event calendar 수동 입력
- news impact score v1
- event risk score v1

### Phase API-5: Data Health

- provider status
- cache age
- stale warning
- Command Center 표시

---

## 17. Acceptance Criteria

API/Data Source 설계 구현은 다음 기준을 만족해야 한다.

```text
[API-AC-001] 포트폴리오 CSV를 import하면 positions와 portfolio_snapshots에 정상 저장된다.
[API-AC-002] 기본 watchlist의 일봉 market_bars를 수집하거나 샘플 데이터로 fallback할 수 있다.
[API-AC-003] 새 market_bars가 들어온 ticker만 indicator가 갱신된다.
[API-AC-004] 데이터 공급자 실패 시 앱이 죽지 않고 stale cache를 표시한다.
[API-AC-005] 뉴스/이벤트는 종목 및 theme과 연결되어야 한다.
[API-AC-006] Data Health 상태가 Command Center에서 확인 가능해야 한다.
[API-AC-007] API key는 코드/테스트 fixture에 하드코딩되지 않는다.
```

---

## 18. 구현 금지사항

```text
- 앱 실행 시 모든 데이터를 무조건 전체 다운로드하지 말 것.
- 외부 API 실패 때문에 Command Center 렌더링을 막지 말 것.
- provider 응답 구조를 UI에서 직접 사용하지 말 것.
- 뉴스 원문 전체를 무단 저장/재배포하지 말 것.
- 투자 추천 문구를 생성하지 말 것.
- “매수/매도하라” 식의 직접 지시를 News Interpretation에 넣지 말 것.
```

---

## 19. 요약

FinSkillOS v2.1의 API/Data Source Layer는 다음 구조로 구현한다.

```text
Provider Adapter
→ Canonical DTO
→ Validation / Normalization
→ PostgreSQL / Parquet Cache
→ Signal / Regime / Risk / Research Hub
```

핵심은 데이터 수집량이 아니라 **데이터의 해석 가능성, 재현성, 안정성, 캐시 가능성**이다.
