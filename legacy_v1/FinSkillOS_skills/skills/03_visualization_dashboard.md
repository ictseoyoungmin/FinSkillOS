# 03_visualization_dashboard.md

**Skill Name:** Visualization & Dashboard Composition Skill  
**Role:** 데이터 구조와 분석 목적에 맞는 차트를 자동 선택하고, 투자 대시보드 레이아웃을 구성한다.  
**Primary Evaluation Target:** 대시보드 자동 생성 25점

---

## 1. Purpose

이 Skill은 FinSkillOS가 투자 데이터를 분석한 뒤 어떤 차트를 보여줄지, 어떤 순서로 대시보드를 구성할지, 어떤 UI 요소를 제공할지를 정의한다.

대시보드는 단순히 여러 차트를 나열하지 않는다. 사용자는 다음 순서로 분석을 이해해야 한다.

```text
데이터가 무엇인가?
  -> 수익률은 어땠는가?
  -> 리스크는 얼마나 컸는가?
  -> 자산 간 관계는 어떠한가?
  -> 어떤 규칙이 어떤 결론을 만들었는가?
```

---

## 2. Dashboard Layout Rules

### DASH-001: Default Section Order

대시보드는 다음 순서를 기본으로 한다.

1. Header & Upload Panel
2. Data Profile
3. Schema Mapping Result
4. Executive Summary
5. Return Analysis
6. Risk Analysis
7. Correlation & Diversification
8. Rule-Based Insights
9. Applied Skill Rules
10. Export Report

---

### DASH-002: Header Requirements

Header는 다음 정보를 포함한다.

- 서비스명: FinSkillOS
- 짧은 설명: Skill-Governed Investment Analytics Dashboard
- 현재 분석 모드: Single Asset / Multi Asset / Allocation / Auto
- 데이터 파일명 또는 sample dataset명

---

### DASH-003: Sidebar Requirements

Sidebar는 다음 기능을 제공한다.

| UI Element | Required | Description |
|---|---|---|
| CSV upload | Yes | 사용자 데이터 업로드 |
| Sample dataset selector | Yes | 데모용 샘플 데이터 선택 |
| Analysis mode selector | Yes | Auto / Single Asset / Multi Asset / Allocation |
| Risk-free rate input | Yes | Sharpe 계산용 |
| Run Analysis button | Yes | 분석 실행 |
| Export Report button | Yes | HTML/PDF 변환용 리포트 다운로드 |

---

## 3. Chart Selection Rules

### VIS-001: Price Trend Line Chart

**Condition**

- price column exists
- single asset or selected asset exists

**Chart**

- x-axis: date
- y-axis: price
- chart type: line

**Purpose**

가격 흐름과 추세를 직관적으로 보여준다.

---

### VIS-002: Indexed Cumulative Return Chart

**Condition**

- multiple assets exist
- price or return series can be converted to cumulative return

**Chart**

- x-axis: date
- y-axis: indexed cumulative return
- each line: asset
- starting value: 100 or 0% cumulative return

**Purpose**

자산 간 성과 비교를 가능하게 한다.

---

### VIS-003: Drawdown Chart

**Condition**

- return series exists or can be computed

**Chart**

- x-axis: date
- y-axis: drawdown
- chart type: area or line
- y-axis should be negative or zero

**Purpose**

손실 구간과 회복 과정을 시각화한다.

---

### VIS-004: Correlation Heatmap

**Condition**

- two or more asset return series exist
- overlapping observation count is sufficient

**Chart**

- x-axis: asset
- y-axis: asset
- value: Pearson correlation

**Purpose**

자산 간 분산효과와 동조화 정도를 보여준다.

---

### VIS-005: Risk-Return Scatter Plot

**Condition**

- two or more assets exist
- annualized return and volatility are calculable

**Chart**

- x-axis: annualized volatility
- y-axis: annualized return
- point label: asset
- optional point size: max drawdown absolute value

**Purpose**

각 자산의 리스크 대비 성과를 비교한다.

---

### VIS-006: Metric Summary Table

**Condition**

- one or more metrics are calculable

**Table Columns**

- asset
- total_return
- annualized_return
- volatility
- max_drawdown
- sharpe_ratio
- observation_count

**Purpose**

차트의 해석을 수치로 검증할 수 있게 한다.

---

### VIS-007: Allocation Donut or Treemap

**Condition**

- weight column exists

**Chart**

- donut chart for small number of assets
- treemap for many assets or sector hierarchy

**Purpose**

포트폴리오 비중과 집중도를 보여준다.

---

### VIS-008: Data Quality Bar Chart

**Condition**

- missing value rate or quality warning exists

**Chart**

- x-axis: column name
- y-axis: missing ratio

**Purpose**

분석 신뢰도를 판단할 수 있게 한다.

---

## 4. Chart Priority Rules

### VIS-PRIORITY-001: Single Asset Priority

단일 자산 데이터에서는 다음 순서로 차트를 표시한다.

1. Price Trend
2. Cumulative Return
3. Drawdown
4. Return Distribution
5. Metric Summary

---

### VIS-PRIORITY-002: Multi Asset Priority

다중 자산 데이터에서는 다음 순서로 차트를 표시한다.

1. Indexed Cumulative Return
2. Metric Summary Table
3. Risk-Return Scatter
4. Correlation Heatmap
5. Drawdown Comparison

---

### VIS-PRIORITY-003: Allocation Priority

비중 데이터에서는 다음 순서로 차트를 표시한다.

1. Allocation Donut or Treemap
2. Concentration Table
3. Sector or Category Exposure
4. Concentration Warning

---

## 5. Executive Summary Card Rules

### DASH-SUMMARY-001: Required Cards

Executive Summary는 다음 카드를 우선 표시한다.

| Card | Condition |
|---|---|
| Total Return | return 또는 price가 존재할 때 |
| Annualized Return | 충분한 time-series가 있을 때 |
| Volatility | return series가 있을 때 |
| Maximum Drawdown | return series가 있을 때 |
| Sharpe Ratio | volatility가 0보다 클 때 |
| Risk Level | risk rules 적용 가능할 때 |

---

### DASH-SUMMARY-002: Risk Level Badge

Risk Level은 다음 badge로 표시한다.

| Level | Meaning |
|---|---|
| LOW | 낮은 관측 리스크 |
| MODERATE | 중간 수준 리스크 |
| HIGH | 높은 리스크 |
| VERY HIGH | 매우 높은 리스크 |
| UNKNOWN | 데이터 부족 또는 계산 불가 |

---

## 6. UI Interaction Rules

### UI-001: Auto Mode Default

기본 분석 모드는 `Auto Detect`로 설정한다.

**Reason**

대회 평가 항목 중 범용성과 자동 분석 동작을 직접 보여주기 위함이다.

---

### UI-002: Manual Override

자동 스키마 추론이 불확실하면 사용자가 컬럼 매핑을 수동으로 바꿀 수 있어야 한다.

**Minimum Implementation**

- 자동 매핑 결과 표시
- confidence score 표시
- 불확실한 경우 selectbox 제공

---

### UI-003: Applied Rules Expandable Panel

대시보드 하단에는 Applied Skill Rules 섹션을 표시한다.

**Required Fields**

- rule_id
- step
- condition summary
- action result
- output affected

---

### UI-004: Insight Evidence Link

각 인사이트는 관련 metric 또는 chart를 함께 표시해야 한다.

Example:

```text
[INSIGHT-003] 최대낙폭이 -24.8%로 HIGH 구간에 해당합니다.
Evidence: max_drawdown = -24.8%, applied rule RISK-001
```

---

## 7. Dashboard Generation Output Schema

Dashboard Composer는 다음 구조를 생성해야 한다.

```json
{
  "dashboard_mode": "multi_asset",
  "sections": [
    {
      "id": "data_profile",
      "title": "Data Profile",
      "components": ["row_count", "column_count", "schema_mapping_table"]
    },
    {
      "id": "return_analysis",
      "title": "Return Analysis",
      "components": ["cumulative_return_chart", "metric_table"]
    },
    {
      "id": "risk_analysis",
      "title": "Risk Analysis",
      "components": ["drawdown_chart", "risk_badges"]
    }
  ],
  "applied_rules": ["DASH-001", "VIS-002", "VIS-003", "VIS-004"]
}
```

---

## 8. Visual Design Rules

### DESIGN-001: Professional Financial Dashboard Tone

UI는 다음 인상을 주어야 한다.

- 금융권 내부 분석 도구
- 과도하게 화려하지 않음
- 데이터 중심
- 리스크 경고가 명확함
- 차트와 지표가 한눈에 들어옴

---

### DESIGN-002: Color Semantics

색상은 다음 의미 체계를 따른다.

| Meaning | Use |
|---|---|
| Positive performance | 수익률 증가 |
| Negative performance | 손실 또는 drawdown |
| Warning | 데이터 품질 또는 리스크 경고 |
| Neutral | 일반 지표, 테이블 |

단, 구현체는 접근성을 고려해 색상만으로 의미를 전달하지 않고 텍스트 라벨도 함께 제공해야 한다.

---

### DESIGN-003: Chart Minimalism

차트는 다음을 피해야 한다.

- 3D chart
- 과도한 애니메이션
- 불필요한 배경 장식
- 너무 많은 색상
- 해석하기 어려운 복합 차트

---

## 9. Report Export Rules

### REPORT-001: Exportable HTML Report

대시보드는 분석 결과를 HTML 리포트로 export할 수 있어야 한다.

Required sections:

1. Dataset summary
2. Schema mapping
3. Metric summary
4. Main charts
5. Risk interpretation
6. Skill rule audit log
7. Disclaimer

---

### REPORT-002: PDF Conversion Readiness

HTML 리포트는 PDF 변환을 고려하여 다음 구조를 가져야 한다.

- 명확한 heading structure
- table captions
- chart titles
- page-break friendly sections
- disclaimer at the end

---

## 10. Acceptance Tests

### Test A: Single Asset

Expected charts:

- price trend line
- cumulative return chart
- drawdown chart
- metric summary

---

### Test B: Multi Asset

Expected charts:

- cumulative return comparison
- risk-return scatter
- correlation heatmap
- metric table

---

### Test C: Allocation Data

Expected charts:

- allocation chart
- concentration analysis
- sector exposure if available

---

## 11. Final Visualization Principle

> 좋은 금융 대시보드는 많은 차트를 보여주는 것이 아니라, 사용자가 성과와 리스크를 같은 흐름에서 이해하도록 차트를 배치하는 것이다.
