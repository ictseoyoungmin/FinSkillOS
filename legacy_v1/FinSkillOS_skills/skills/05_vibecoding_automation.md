# 05_vibecoding_automation.md

**Skill Name:** Vibe Coding Automation Skill  
**Role:** Skills.md 문서를 기반으로 투자 대시보드 웹 서비스를 생성하기 위한 구현 지침을 정의한다.  
**Primary Evaluation Target:** 바이브코딩 활용 15점

---

## 1. Purpose

이 Skill은 FinSkillOS가 단순히 문서를 제출하는 수준을 넘어, `Skills.md`를 기반으로 실제 웹 대시보드를 생성했다는 점을 증명하기 위한 바이브코딩 지침이다.

핵심 목표는 다음과 같다.

1. 문서가 코드 구조를 결정해야 한다.
2. Rule ID가 앱의 함수, UI 섹션, 인사이트 결과와 연결되어야 한다.
3. 수동 구현은 최소화하고, 분석 정책은 문서에 위치해야 한다.
4. 웹앱은 데이터 업로드 후 자동으로 분석 흐름을 실행해야 한다.

---

## 2. Recommended Tech Stack

### AUTO-STACK-001: MVP Stack

대회용 MVP는 다음 스택을 권장한다.

```text
Python
Streamlit
Pandas
NumPy
Plotly
Jinja2
Markdown
```

**Reason**

- 빠른 구현 가능
- 금융 데이터 분석에 적합
- 웹 링크 배포가 쉬움
- 차트와 테이블 구현이 간단함
- Skills.md 기반 구조를 시각적으로 보여주기 좋음

---

## 3. Required Project Structure

### AUTO-STRUCT-001: File Layout

바이브코딩 결과물은 다음 구조를 권장한다.

```text
FinSkillOS/
  app.py
  README.md
  Skills.md
  requirements.txt

  skills/
    01_data_understanding.md
    02_financial_metrics.md
    03_visualization_dashboard.md
    04_insight_guardrails.md
    05_vibecoding_automation.md
    06_extension_ideas.md

  engine/
    __init__.py
    data_profiler.py
    schema_mapper.py
    metrics.py
    chart_planner.py
    insight_engine.py
    rule_engine.py
    report_builder.py

  sample_data/
    single_asset_price.csv
    multi_asset_portfolio.csv
    mixed_schema_assets.csv

  reports/
    sample_report.html
```

---

## 4. Code Generation Contract

### AUTO-CONTRACT-001: Rule Engine

`rule_engine.py`는 다음 역할을 수행한다.

- Rule ID 등록
- Rule 적용 로그 저장
- 대시보드 Applied Skill Rules 섹션 출력
- report export 시 rule audit 포함

Recommended data structure:

```python
@dataclass
class AppliedRule:
    rule_id: str
    step: str
    condition: str
    action: str
    result: str
    severity: str = "INFO"
```

---

### AUTO-CONTRACT-002: Data Profiler

`data_profiler.py`는 다음 함수를 가져야 한다.

```python
def profile_dataframe(df: pd.DataFrame) -> dict:
    """Detect row count, column types, missingness, date candidates, numeric candidates."""
```

Required output:

```python
{
    "row_count": int,
    "column_count": int,
    "missing_rates": dict,
    "date_candidates": list,
    "numeric_columns": list,
    "categorical_columns": list,
    "quality_warnings": list,
    "applied_rules": list,
}
```

---

### AUTO-CONTRACT-003: Schema Mapper

`schema_mapper.py`는 다음 함수를 가져야 한다.

```python
def infer_schema(df: pd.DataFrame, profile: dict) -> dict:
    """Map arbitrary input columns to FinSkillOS standard schema."""
```

Required output:

```python
{
    "schema_type": "single_asset_price | multi_asset_long | multi_asset_wide | allocation | unknown",
    "mapping": {
        "date": {"source": "trade_dt", "confidence": 0.98},
        "asset": {"source": "ticker_name", "confidence": 0.94},
        "price": {"source": "nav_value", "confidence": 0.91}
    },
    "standardized_df": pd.DataFrame,
    "applied_rules": list,
}
```

---

### AUTO-CONTRACT-004: Metric Engine

`metrics.py`는 다음 함수를 가져야 한다.

```python
def compute_metrics(std_df: pd.DataFrame, schema: dict, risk_free_rate: float = 0.0) -> dict:
    """Compute return, risk, and multi-asset metrics according to metric rules."""
```

Required metrics:

- total_return
- annualized_return
- annualized_volatility
- max_drawdown
- sharpe_ratio
- asset_metric_table
- correlation_matrix if applicable

---

### AUTO-CONTRACT-005: Chart Planner

`chart_planner.py`는 다음 함수를 가져야 한다.

```python
def plan_charts(schema: dict, metrics: dict) -> list[dict]:
    """Select charts according to VIS rules."""
```

Required chart plan schema:

```python
[
    {
        "chart_id": "cumulative_return_chart",
        "rule_id": "VIS-002",
        "title": "Cumulative Return Comparison",
        "priority": 1,
        "reason": "Multiple asset return series are available."
    }
]
```

---

### AUTO-CONTRACT-006: Insight Engine

`insight_engine.py`는 다음 함수를 가져야 한다.

```python
def generate_insights(metrics: dict, quality: dict, schema: dict) -> list[dict]:
    """Generate risk-first, evidence-linked insights."""
```

Each insight must include:

```python
{
    "category": "drawdown",
    "severity": "HIGH",
    "fact": str,
    "interpretation": str,
    "caution": str,
    "evidence": dict,
    "rule_ids": list[str]
}
```

---

### AUTO-CONTRACT-007: Report Builder

`report_builder.py`는 다음 함수를 가져야 한다.

```python
def build_html_report(analysis_result: dict) -> str:
    """Build exportable HTML report with metrics, insights, and applied rules."""
```

Report sections:

1. Dataset summary
2. Schema mapping
3. Metric summary
4. Risk insights
5. Applied rules
6. Disclaimer

---

## 5. App Behavior Contract

### AUTO-APP-001: Main Flow

`app.py`는 다음 흐름을 구현해야 한다.

```text
load data
  -> profile_dataframe
  -> infer_schema
  -> compute_metrics
  -> plan_charts
  -> generate_insights
  -> render dashboard
  -> build report
```

---

### AUTO-APP-002: Rule Trace Visibility

웹 화면에는 반드시 `Applied Skill Rules` 섹션이 있어야 한다.

Minimum display:

| Rule ID | Step | Result |
|---|---|---|
| DATA-001 | Schema Detection | trade_dt mapped to date |
| METRIC-007 | Risk Metric | max drawdown calculated |
| VIS-004 | Chart Planning | correlation heatmap rendered |
| INSIGHT-003 | Insight | risk-first insight generated |

---

### AUTO-APP-003: No Silent Failure

어떤 지표나 차트를 계산할 수 없으면 조용히 숨기지 말고 이유를 표시한다.

Example:

```text
Correlation heatmap was not generated because only one asset was detected.
```

---

## 6. Vibe Coding Prompt Template

해당 프로젝트를 바이브코딩으로 구현할 때 사용할 수 있는 기본 프롬프트는 다음과 같다.

```text
Build a Streamlit web app named FinSkillOS using the attached Skills.md documents.
The app must not be a static dashboard. It must read arbitrary CSV files, infer the financial schema, calculate metrics, select charts, generate insights, and display applied Skill rule IDs.

Use the following modules:
- data_profiler.py for DATA rules
- schema_mapper.py for SCHEMA rules
- metrics.py for METRIC and RISK rules
- chart_planner.py for VIS rules
- insight_engine.py for INSIGHT and SAFE rules
- rule_engine.py for Applied Skill Rules
- report_builder.py for exportable HTML report

The app must support:
1. CSV upload
2. sample dataset selection
3. auto schema detection
4. metric calculation
5. chart auto-selection
6. risk-first insights
7. applied rule audit table
8. report download

Do not generate direct buy/sell/hold investment advice.
```

---

## 7. Sample Data Generation Rules

### AUTO-SAMPLE-001: Single Asset Sample

Generate synthetic single asset price data with columns:

```text
date, close, volume
```

Length:

- 252 rows preferred

Behavior:

- mild upward drift
- volatility
- one drawdown period

---

### AUTO-SAMPLE-002: Multi Asset Sample

Generate synthetic multi-asset long data with columns:

```text
date, asset, price
```

Assets:

- Growth Equity
- Defensive Bond
- Commodity
- Global Tech

Behavior:

- different return/volatility profiles
- non-perfect correlations

---

### AUTO-SAMPLE-003: Mixed Schema Sample

Generate synthetic mixed schema data with columns:

```text
trade_dt, ticker_name, nav_value, trading_amount
```

Purpose:

- demonstrate schema adaptation
- show mapping confidence

---

## 8. Minimum Acceptance Tests

### AUTO-TEST-001: Upload Works

Given a valid CSV, the app must complete analysis without code modification.

---

### AUTO-TEST-002: Mixed Schema Detection Works

Given columns:

```text
trade_dt, ticker_name, nav_value, trading_amount
```

The app must map them to:

```text
date, asset, price, volume
```

---

### AUTO-TEST-003: Multi Asset Charts Work

Given multiple assets, the app must show:

- cumulative return chart
- risk-return scatter
- correlation heatmap
- metric table

---

### AUTO-TEST-004: Forbidden Advice Blocked

The app must not display direct investment advice terms.

---

### AUTO-TEST-005: Applied Rules Visible

The app must show at least 5 applied rule IDs after analysis.

---

## 9. Manual Implementation Minimization Rules

### AUTO-MIN-001: Avoid Hard-Coded Dataset Columns

Do not hard-code only one dataset schema.

Bad:

```python
df["close"]
```

Better:

```python
price_col = schema["mapping"]["price"]["source"]
```

---

### AUTO-MIN-002: Avoid Static Chart List

Do not render every chart blindly. Use `chart_planner.py` to select charts based on data availability.

---

### AUTO-MIN-003: Avoid Static Insights

Do not write fixed text unrelated to actual metrics. Insight text must be populated from calculated values.

---

## 10. Deployment Rules

### AUTO-DEPLOY-001: Streamlit Cloud or Equivalent

The final app must be deployable through a public URL.

Required files:

- `app.py`
- `requirements.txt`
- all engine modules
- sample data
- Skills.md documents

---

### AUTO-DEPLOY-002: Repository Readability

If GitHub link is provided, repository root should contain:

- README.md
- Skills.md
- skills folder
- app.py
- requirements.txt
- sample_data folder

---

## 11. Final Vibe Coding Principle

> 바이브코딩 활용의 핵심은 AI가 코드를 대신 많이 쓰는 것이 아니라, 문서화된 Skill 규칙이 코드 구조와 실행 흐름을 지배하도록 만드는 것이다.
