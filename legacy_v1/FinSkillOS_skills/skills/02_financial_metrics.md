# 02_financial_metrics.md

**Skill Name:** Financial Metric Calculation Skill  
**Role:** 투자 대시보드에서 사용하는 수익률, 리스크, 상관관계, 포트폴리오 지표의 계산 기준을 정의한다.  
**Primary Evaluation Target:** Skills.md 설계 25점

---

## 1. Purpose

이 Skill은 투자 분석 결과가 일관되게 생성되도록 금융 지표 계산 규칙을 정의한다. 모든 지표는 재현 가능해야 하며, 계산 가정은 대시보드와 리포트에 표시되어야 한다.

FinSkillOS는 직접 투자 추천이 아니라 데이터 기반 분석을 제공한다. 따라서 지표는 다음 목적으로 사용된다.

- 과거 성과 요약
- 변동성 및 손실 위험 파악
- 위험 조정 성과 비교
- 자산 간 상관관계와 분산효과 확인
- 데이터 기반 인사이트 생성

---

## 2. Global Metric Assumptions

### METRIC-BASE-001: Return Representation

모든 수익률은 내부적으로 decimal format을 사용한다.

```text
5% -> 0.05
-3% -> -0.03
```

입력 데이터가 5, -3처럼 percent scale로 감지되면 100으로 나누어 변환할 수 있다. 이 경우 변환 사실을 Applied Skill Rules에 기록한다.

---

### METRIC-BASE-002: Annualization Periods

빈도별 연율화 기준은 다음과 같다.

| Frequency | periods_per_year |
|---|---:|
| Daily | 252 |
| Weekly | 52 |
| Monthly | 12 |
| Quarterly | 4 |
| Yearly | 1 |
| Unknown | 252 with warning |

---

### METRIC-BASE-003: Risk-Free Rate

사용자가 무위험 수익률을 입력하지 않으면 기본값은 0.0으로 둔다.

Dashboard must disclose:

```text
무위험 수익률이 제공되지 않아 Sharpe Ratio 계산에는 0.0을 사용했습니다.
```

---

## 3. Return Metrics

### METRIC-001: Period Return from Price

**Condition**

- price series가 존재한다.

**Formula**

```text
period_return_t = price_t / price_{t-1} - 1
```

**Action**

- 첫 번째 수익률은 null로 처리한다.
- 이후 지표 계산에서는 null을 제외한다.

---

### METRIC-002: Cumulative Return

**Condition**

- return series가 존재한다.

**Formula**

```text
cumulative_return_t = product(1 + return_i for i = 1..t) - 1
```

**Output**

- 누적수익률 series
- 최종 누적수익률

---

### METRIC-003: Total Return

**Formula from Price**

```text
total_return = final_price / initial_price - 1
```

**Formula from Return**

```text
total_return = product(1 + return_t) - 1
```

---

### METRIC-004: Annualized Return

**Formula**

```text
annualized_return = (1 + total_return) ^ (periods_per_year / number_of_periods) - 1
```

**Exception**

- `number_of_periods <= 1`이면 계산하지 않는다.
- 데이터 기간이 60일 미만이면 uncertainty warning을 추가한다.

---

## 4. Risk Metrics

### METRIC-005: Annualized Volatility

**Formula**

```text
annualized_volatility = std(period_return) * sqrt(periods_per_year)
```

**Interpretation Use**

- 변동성 리스크 분류
- risk-return scatter
- Sharpe Ratio 계산

---

### METRIC-006: Downside Deviation

**Formula**

```text
downside_returns = min(return_t - target_return, 0)
downside_deviation = sqrt(mean(downside_returns^2)) * sqrt(periods_per_year)
```

**Default target_return**

```text
target_return = 0.0
```

---

### METRIC-007: Maximum Drawdown

**Formula**

```text
wealth_index_t = product(1 + return_i for i = 1..t)
running_max_t = max(wealth_index_i for i <= t)
drawdown_t = wealth_index_t / running_max_t - 1
max_drawdown = min(drawdown_t)
```

**Output**

- drawdown series
- max drawdown value
- max drawdown start/end date if calculable

---

### METRIC-008: Value at Risk Approximation

**Condition**

- return series length >= 60

**Formula**

```text
historical_var_95 = percentile(return_series, 5)
historical_var_99 = percentile(return_series, 1)
```

**Output Label**

- Historical VaR approximation

**Guardrail**

- VaR는 최악 손실 한도가 아니며, 과거 분포 기반 추정치라고 표시한다.

---

## 5. Risk-Adjusted Return Metrics

### METRIC-009: Sharpe Ratio

**Formula**

```text
sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
```

**Exception**

- annualized_volatility가 0 또는 null이면 계산하지 않는다.

---

### METRIC-010: Sortino Ratio

**Formula**

```text
sortino_ratio = (annualized_return - target_return) / downside_deviation
```

**Exception**

- downside_deviation이 0 또는 null이면 계산하지 않는다.

---

### METRIC-011: Calmar Ratio

**Formula**

```text
calmar_ratio = annualized_return / abs(max_drawdown)
```

**Exception**

- max_drawdown이 0 또는 null이면 계산하지 않는다.

---

## 6. Multi-Asset Metrics

### METRIC-012: Asset-Level Metric Table

**Condition**

- asset column이 존재한다.

**Action**

각 asset별로 다음 지표를 계산한다.

- total_return
- annualized_return
- annualized_volatility
- max_drawdown
- sharpe_ratio
- sortino_ratio if available
- observation_count

---

### METRIC-013: Correlation Matrix

**Condition**

- 2개 이상의 asset return series가 존재한다.

**Action**

- return series를 wide matrix로 변환한다.
- Pearson correlation을 계산한다.
- 결측치는 pairwise valid observation 방식으로 처리한다.

**Failure Behavior**

- 공통 관측치가 부족하면 correlation heatmap을 표시하지 않는다.

---

### METRIC-014: Portfolio Return from Weights

**Condition**

- asset return series와 weight가 존재한다.

**Formula**

```text
portfolio_return_t = sum(weight_i * return_{i,t})
```

**Assumption**

- 기본값은 고정 비중 buy-and-hold가 아니라 period별 weighted return이다.
- 리밸런싱 여부가 명시되지 않으면 동일 비중 또는 입력 비중을 사용하고 가정을 표시한다.

---

### METRIC-015: Concentration Score

**Condition**

- weight column이 존재한다.

**Formula**

```text
max_weight = max(weight_i)
hhi = sum(weight_i^2)
```

**Interpretation**

- max_weight > 0.5이면 concentration risk warning
- hhi > 0.25이면 concentration score high

---

## 7. Risk Classification Rules

### RISK-001: Drawdown Risk Level

| Max Drawdown | Risk Level |
|---:|---|
| >= -0.05 | LOW |
| -0.05 to -0.15 | MODERATE |
| -0.15 to -0.25 | HIGH |
| < -0.25 | VERY HIGH |

---

### RISK-002: Volatility Risk Level

| Annualized Volatility | Risk Level |
|---:|---|
| < 0.10 | LOW |
| 0.10 to 0.20 | MODERATE |
| 0.20 to 0.35 | HIGH |
| > 0.35 | VERY HIGH |

---

### RISK-003: Sharpe Quality Level

| Sharpe Ratio | Interpretation |
|---:|---|
| < 0 | Negative risk-adjusted performance |
| 0 to 0.5 | Weak |
| 0.5 to 1.0 | Moderate |
| 1.0 to 2.0 | Strong |
| > 2.0 | Very strong, verify data quality |

---

### RISK-004: Data Sufficiency Risk

| Observations | Interpretation |
|---:|---|
| < 30 | Very limited history |
| 30 - 59 | Limited history |
| 60 - 251 | Medium history |
| >= 252 | Sufficient for annualized statistics |

---

## 8. Metric Output Schema

Metric Engine은 다음 구조를 출력해야 한다.

```json
{
  "summary": {
    "total_return": 0.184,
    "annualized_return": 0.121,
    "annualized_volatility": 0.218,
    "max_drawdown": -0.174,
    "sharpe_ratio": 0.55,
    "risk_level": "HIGH"
  },
  "asset_metrics": [
    {
      "asset": "A_Equity",
      "annualized_return": 0.14,
      "annualized_volatility": 0.25,
      "max_drawdown": -0.22,
      "sharpe_ratio": 0.56
    }
  ],
  "applied_rules": [
    "METRIC-001",
    "METRIC-002",
    "METRIC-005",
    "METRIC-007",
    "METRIC-009",
    "RISK-001"
  ]
}
```

---

## 9. Metric Display Rules

### METRIC-DISPLAY-001: Percent Formatting

수익률, 변동성, 최대낙폭은 percent로 표시한다.

```text
0.1234 -> 12.34%
-0.081 -> -8.10%
```

---

### METRIC-DISPLAY-002: Ratio Formatting

Sharpe, Sortino, Calmar는 소수점 둘째 자리까지 표시한다.

```text
1.236 -> 1.24
```

---

### METRIC-DISPLAY-003: Missing Metric Display

계산 불가능한 지표는 `N/A`로 표시하고 이유를 tooltip 또는 note에 표시한다.

---

## 10. Acceptance Tests

### Test A: Constant Price

Input price:

```text
100, 100, 100, 100
```

Expected:

- total_return = 0
- volatility = 0
- sharpe_ratio = N/A
- max_drawdown = 0

---

### Test B: Declining Price

Input price:

```text
100, 90, 80, 70
```

Expected:

- total_return = -30%
- max_drawdown = -30%
- risk warning generated

---

### Test C: Multi Asset Return

Input:

- 3 assets
- 100+ observations

Expected:

- asset metric table generated
- correlation matrix generated
- risk-return scatter generated

---

## 11. Final Metric Principle

> 모든 금융 지표는 계산 가능성, 가정, 한계가 함께 표시되어야 한다. 숫자만 제시하는 대시보드는 금융 분석 도구가 아니라 장식용 차트에 불과하다.
