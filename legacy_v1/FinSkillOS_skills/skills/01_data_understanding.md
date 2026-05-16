# 01_data_understanding.md

**Skill Name:** Data Understanding & Schema Adaptation Skill  
**Role:** 투자 데이터 구조를 자동으로 이해하고 FinSkillOS 표준 스키마로 변환한다.  
**Primary Evaluation Target:** 범용성 25점

---

## 1. Purpose

이 Skill은 서로 다른 컬럼명, 데이터 구조, 자산 표현 방식, 가격/수익률 형식을 가진 투자 데이터를 일관된 내부 구조로 변환하기 위한 규칙을 정의한다.

FinSkillOS는 특정 파일 형식에 종속되지 않아야 한다. 사용자가 업로드한 데이터의 컬럼명이 `date`, `trade_dt`, `일자`, `기준일`, `timestamp`처럼 달라도 날짜 컬럼을 추론해야 하며, `close`, `price`, `nav`, `종가`, `기준가`처럼 표현이 달라도 가격 컬럼을 추론해야 한다.

---

## 2. Supported Input Structures

### DATA-STRUCT-001: Single Asset Price Table

**Condition**

- 날짜형 컬럼 1개 이상 존재
- 가격형 numeric 컬럼 1개 이상 존재
- 자산 식별 컬럼이 없거나 단일 자산으로 간주 가능

**Expected Standard Schema**

```text
date, price, optional volume
```

**Example**

```csv
date,close,volume
2025-01-01,100.0,120000
2025-01-02,101.5,135000
```

---

### DATA-STRUCT-002: Multi Asset Long Table

**Condition**

- 날짜형 컬럼 1개 이상 존재
- 자산 식별 컬럼 1개 이상 존재
- 가격형 또는 수익률형 numeric 컬럼 1개 이상 존재

**Expected Standard Schema**

```text
date, asset, price or return, optional volume, optional weight
```

**Example**

```csv
date,asset,price
2025-01-01,A_Equity,100.0
2025-01-01,B_Bond,100.0
```

---

### DATA-STRUCT-003: Multi Asset Wide Table

**Condition**

- 날짜형 컬럼 1개 존재
- 나머지 다수 numeric 컬럼이 가격 또는 수익률 계열로 보임
- 자산 식별 컬럼은 없지만 numeric 컬럼명이 자산명으로 사용 가능

**Expected Standard Schema**

Wide format은 long format으로 변환한다.

```text
date, asset, price_or_return
```

**Example Before**

```csv
date,AAPL,MSFT,SPY
2025-01-01,100,100,100
2025-01-02,101,99,100.5
```

**Example After**

```csv
date,asset,price
2025-01-01,AAPL,100
2025-01-01,MSFT,100
2025-01-01,SPY,100
```

---

### DATA-STRUCT-004: Portfolio Allocation Table

**Condition**

- 날짜 컬럼이 없을 수 있음
- 자산명 컬럼 존재
- 비중 또는 금액 컬럼 존재

**Expected Analysis Mode**

- concentration analysis
- allocation chart
- sector exposure analysis if category columns exist

---

## 3. Column Detection Rules

### DATA-001: Date Column Detection

**Condition**

- 컬럼 값의 80% 이상이 datetime으로 파싱 가능하거나,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
date, dt, datetime, timestamp, time, 일자, 날짜, 기준일, 거래일, 평가일
```

**Action**

- 해당 컬럼을 `date` 후보로 분류한다.
- 후보가 여러 개면 파싱 성공률이 가장 높은 컬럼을 우선한다.
- 동률이면 결측률이 낮은 컬럼을 우선한다.

**Failure Behavior**

- 날짜 컬럼을 찾지 못하면 time-series 분석을 비활성화하고 allocation/static 분석 모드로 전환한다.

---

### DATA-002: Asset Identifier Detection

**Condition**

- 문자열 또는 범주형 컬럼이며,
- 고유값 수가 전체 행 수보다 충분히 작고,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
asset, ticker, symbol, code, name, fund, product, 종목, 티커, 자산, 펀드, 상품, 코드
```

**Action**

- 해당 컬럼을 `asset`으로 매핑한다.

**Heuristic**

- `unique_count / row_count <= 0.5`이면 자산 식별자 후보로 간주한다.
- 다만 행 수가 적은 데이터에서는 이 조건을 완화할 수 있다.

---

### DATA-003: Price Column Detection

**Condition**

- numeric 컬럼이며,
- 대부분 양수이고,
- 시간에 따라 연속적인 값을 가지며,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
price, close, adj_close, adjusted, nav, value, index, level, 종가, 가격, 기준가, 지수, 평가금액
```

**Action**

- 해당 컬럼을 `price`로 매핑한다.

**Priority**

1. adjusted close / 수정종가
2. close / 종가
3. nav / 기준가
4. price / 가격
5. value / 평가금액

---

### DATA-004: Return Column Detection

**Condition**

- numeric 컬럼이며,
- 값의 대부분이 -1과 1 사이에 있고,
- 평균이 0 근처이며,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
return, ret, yield, pct, change, 수익률, 등락률, 변화율
```

**Action**

- 해당 컬럼을 `return`으로 매핑한다.

**Additional Rule**

- 값의 절댓값이 100보다 작은데 컬럼명이 percent 또는 pct를 포함하면, 100으로 나누어 decimal return으로 변환할지 후보로 표시한다.

---

### DATA-005: Volume Column Detection

**Condition**

- numeric 컬럼이며,
- 대부분 0 이상이고,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
volume, amount, turnover, 거래량, 거래대금, 금액
```

**Action**

- 해당 컬럼을 `volume`으로 매핑한다.

---

### DATA-006: Weight Column Detection

**Condition**

- numeric 컬럼이며,
- 값의 합이 1.0 또는 100에 가깝거나,
- 컬럼명이 아래 키워드 중 하나를 포함한다.

**Keywords**

```text
weight, allocation, ratio, 비중, 배분, 구성비
```

**Action**

- 해당 컬럼을 `weight`로 매핑한다.
- 합계가 100 근처이면 100으로 나누어 0~1 범위로 표준화한다.

---

### DATA-007: Category Column Detection

**Condition**

- 문자열 또는 범주형 컬럼이며,
- sector, industry, region, class, type, category 등 의미를 가진다.

**Keywords**

```text
sector, industry, region, country, class, type, category, 섹터, 업종, 국가, 지역, 자산군, 유형
```

**Action**

- 해당 컬럼을 category metadata로 저장한다.

---

## 4. Data Quality Rules

### DATA-QA-001: Missing Value Check

**Action**

- 컬럼별 결측률을 계산한다.
- 핵심 컬럼의 결측률이 20%를 초과하면 warning을 표시한다.

**Insight Template**

```text
데이터 품질 경고: 핵심 컬럼 `{column}`의 결측률이 {missing_rate}%로 높아 분석 결과의 안정성이 낮을 수 있습니다.
```

---

### DATA-QA-002: Duplicate Date-Asset Check

**Condition**

- `date`와 `asset` 조합이 중복된다.

**Action**

- 중복 행 수를 표시한다.
- 기본값은 마지막 값을 사용한다.
- 리포트에 중복 처리 방식을 명시한다.

---

### DATA-QA-003: Insufficient History Warning

**Condition**

- time-series 데이터 포인트가 60개 미만이다.

**Action**

- 연율화 지표와 리스크 해석에 불확실성 경고를 추가한다.

---

### DATA-QA-004: Extreme Return Detection

**Condition**

- 일간 수익률 절댓값이 50%를 초과한다.

**Action**

- 이상치 후보로 표시한다.
- 자동 제거하지 않는다.
- 사용자가 확인할 수 있도록 데이터 품질 섹션에 노출한다.

---

### DATA-QA-005: Non-Monotonic Date Check

**Condition**

- 날짜가 오름차순으로 정렬되어 있지 않다.

**Action**

- 날짜 기준 정렬을 수행한다.
- 정렬 수행 여부를 Applied Skill Rules에 기록한다.

---

## 5. Frequency Detection Rules

### DATA-FREQ-001: Daily Frequency

**Condition**

- 연속 날짜 차이의 중앙값이 1~3일이다.

**Action**

- trading_days = 252 사용

---

### DATA-FREQ-002: Weekly Frequency

**Condition**

- 날짜 차이 중앙값이 5~9일이다.

**Action**

- periods_per_year = 52 사용

---

### DATA-FREQ-003: Monthly Frequency

**Condition**

- 날짜 차이 중앙값이 25~35일이다.

**Action**

- periods_per_year = 12 사용

---

### DATA-FREQ-004: Unknown Frequency

**Condition**

- 위 조건으로 빈도를 안정적으로 판단할 수 없다.

**Action**

- 기본값은 daily frequency로 두되, 리포트에 가정을 명시한다.

---

## 6. Schema Confidence Score

각 표준 컬럼 매핑에는 confidence score를 부여한다.

| Score Range | Meaning | UI Behavior |
|---|---|---|
| 0.90 - 1.00 | 매우 확실 | 자동 매핑 |
| 0.70 - 0.89 | 대체로 확실 | 자동 매핑 + 사용자 확인 표시 |
| 0.50 - 0.69 | 불확실 | 후보로 표시 |
| below 0.50 | 낮음 | 자동 매핑하지 않음 |

Confidence는 다음 요소로 계산한다.

```text
confidence = 0.4 * name_match_score
           + 0.3 * dtype_score
           + 0.2 * distribution_score
           + 0.1 * missingness_score
```

---

## 7. Standard Output

Data Understanding 단계는 다음 JSON 구조를 생성해야 한다.

```json
{
  "detected_schema": "multi_asset_long_price",
  "columns": {
    "date": {"source": "trade_dt", "confidence": 0.98},
    "asset": {"source": "ticker_name", "confidence": 0.94},
    "price": {"source": "nav_value", "confidence": 0.91},
    "volume": {"source": "trading_amount", "confidence": 0.87}
  },
  "frequency": "daily",
  "quality_warnings": [],
  "applied_rules": ["DATA-001", "DATA-002", "DATA-003", "DATA-005", "DATA-FREQ-001"]
}
```

---

## 8. Acceptance Tests

### Test A: Korean Column Names

Input columns:

```text
일자, 종목명, 기준가, 거래대금
```

Expected mapping:

```text
일자 -> date
종목명 -> asset
기준가 -> price
거래대금 -> volume
```

---

### Test B: English Mixed Column Names

Input columns:

```text
trade_dt, ticker_name, nav_value, trading_amount
```

Expected mapping:

```text
trade_dt -> date
ticker_name -> asset
nav_value -> price
trading_amount -> volume
```

---

### Test C: Wide Format

Input columns:

```text
date, KOSPI, NASDAQ, GOLD, BOND
```

Expected behavior:

- `date`를 date로 매핑
- 나머지 numeric columns를 asset series로 변환
- long format으로 melt

---

## 9. Final Data Understanding Principle

> FinSkillOS는 사용자가 데이터를 시스템에 맞추게 만들지 않는다. 시스템이 데이터를 이해하고 표준 분석 구조로 맞춰야 한다.
