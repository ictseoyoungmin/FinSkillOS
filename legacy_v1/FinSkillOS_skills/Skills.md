# FinSkillOS Skills.md

**Project:** FinSkillOS - Skill-Governed Investment Analytics Dashboard  
**Version:** 1.0.0  
**Submission Type:** Main Skill Orchestrator  
**Purpose:** 투자 데이터 구조가 달라도 동일한 분석 기준으로 데이터 이해, 지표 계산, 시각화 선택, 인사이트 생성, 대시보드 구성을 자동 수행하도록 정의하는 최상위 Skills.md 문서

---

## 0. Executive Skill Definition

FinSkillOS는 투자 데이터를 단순히 시각화하는 웹앱이 아니라, `Skills.md`에 정의된 분석 정책을 기반으로 작동하는 **문서 기반 금융 분석 대시보드 생성 시스템**이다.

이 문서는 다음 다섯 가지 역할을 수행한다.

1. 다양한 투자 데이터의 구조를 자동 이해하기 위한 규칙을 정의한다.
2. 금융 지표 계산 기준과 예외 처리 기준을 정의한다.
3. 데이터 특성별 시각화 선택 기준을 정의한다.
4. 투자 인사이트 생성 시 표현 방식과 안전장치를 정의한다.
5. 웹 대시보드를 문서 기반으로 자동 생성하기 위한 바이브코딩 지침을 정의한다.

FinSkillOS는 사용자가 업로드한 CSV 또는 표 형식 투자 데이터를 분석하여, 다음 결과물을 자동으로 생성해야 한다.

- 데이터 프로파일
- 표준 스키마 매핑 결과
- 수익률 분석
- 리스크 분석
- 상관관계 및 분산 분석
- 자동 선택된 차트
- 리스크 우선 인사이트
- 적용된 Skill Rule 추적 로그
- 다운로드 가능한 투자 분석 리포트

---

## 1. Skill Document Set

본 제출물은 여러 개의 Skills.md 문서를 기능별로 분리한다. 각 문서는 독립적으로 읽을 수 있어야 하며, 동시에 전체 시스템에서는 아래 순서로 연결된다.

| File | Role | Evaluation Target |
|---|---|---|
| `Skills.md` | 최상위 오케스트레이터 | 전체 설계, 범용성, 자동 생성 구조 |
| `skills/01_data_understanding.md` | 데이터 구조 이해 및 표준 스키마 변환 | 범용성 |
| `skills/02_financial_metrics.md` | 투자 지표 계산 규칙 | Skills.md 설계 |
| `skills/03_visualization_dashboard.md` | 차트 선택 및 대시보드 구성 규칙 | 대시보드 자동 생성 |
| `skills/04_insight_guardrails.md` | 인사이트 생성 및 금융 표현 안전장치 | 실용성, 신뢰성 |
| `skills/05_vibecoding_automation.md` | 문서 기반 코드 생성 및 구현 지침 | 바이브코딩 활용 |
| `skills/06_extension_ideas.md` | 확장 기능, 제품화, 엔터프라이즈 적용 아이디어 | 실용성 및 창의성 |

---

## 2. System Role

FinSkillOS는 다음 역할을 가진다.

> A skill-governed financial analytics dashboard engine that transforms heterogeneous investment datasets into consistent, explainable, risk-aware, and auditable dashboards.

시스템은 다음 원칙을 반드시 따른다.

1. **Rule-first:** 분석 결과는 임의의 추론이 아니라 Skill Rule에 근거해야 한다.
2. **Schema-adaptive:** 컬럼명이 달라도 날짜, 자산, 가격, 수익률, 거래량, 비중 등을 추론해야 한다.
3. **Risk-first:** 수익보다 리스크를 먼저 해석해야 한다.
4. **Evidence-traced:** 모든 주요 인사이트는 근거 지표 또는 차트와 연결되어야 한다.
5. **No direct investment advice:** 매수, 매도, 보유 등 직접적인 투자 권유를 생성하지 않는다.
6. **Reusable:** 데이터셋이 바뀌어도 동일한 Skill 문서를 재사용할 수 있어야 한다.
7. **Vibe-codeable:** 개발자는 이 문서만 보고 핵심 앱 구조를 생성할 수 있어야 한다.

---

## 3. Target Data Types

FinSkillOS는 다음 데이터 유형을 지원해야 한다.

| Data Type | Example Columns | Required Behavior |
|---|---|---|
| 단일 자산 가격 데이터 | date, close, volume | 가격 추세, 수익률, 변동성, 낙폭 분석 |
| 다중 자산 long-format 데이터 | date, asset, price | 자산별 누적수익률, 상관관계, 리스크-수익 비교 |
| 다중 자산 wide-format 데이터 | date, AAPL, MSFT, SPY | 각 컬럼을 자산 가격 또는 수익률로 추론 |
| 포트폴리오 비중 데이터 | asset, weight, sector | 비중, 집중도, 섹터 노출 분석 |
| 혼합 스키마 데이터 | trade_dt, ticker_name, nav_value | 표준 스키마 자동 매핑 |
| 수익률 데이터 | date, asset, return | 가격 없이도 누적수익률 및 리스크 계산 |

---

## 4. Standard Schema

모든 입력 데이터는 내부적으로 다음 표준 스키마 중 하나로 변환되어야 한다.

### 4.1 Time Series Price Schema

| Standard Field | Description | Required |
|---|---|---|
| `date` | 관측 날짜 | Yes |
| `asset` | 자산명 또는 티커 | Optional for single asset, required for multi asset |
| `price` | 가격, 종가, NAV, 기준가 | Yes |
| `volume` | 거래량 또는 거래대금 | Optional |
| `weight` | 포트폴리오 비중 | Optional |
| `sector` | 업종, 자산군, 카테고리 | Optional |

### 4.2 Return Series Schema

| Standard Field | Description | Required |
|---|---|---|
| `date` | 관측 날짜 | Yes |
| `asset` | 자산명 또는 티커 | Optional for single asset, required for multi asset |
| `return` | 기간 수익률 | Yes |
| `weight` | 포트폴리오 비중 | Optional |

### 4.3 Allocation Schema

| Standard Field | Description | Required |
|---|---|---|
| `asset` | 자산명 | Yes |
| `weight` | 포트폴리오 비중 | Yes |
| `sector` | 섹터 또는 자산군 | Optional |
| `region` | 국가 또는 지역 | Optional |

---

## 5. Global Analysis Flow

FinSkillOS는 모든 데이터셋에 대해 다음 순서를 따른다.

```text
Input CSV
  -> Data Quality Check
  -> Column Type Inference
  -> Standard Schema Mapping
  -> Frequency Detection
  -> Metric Calculation
  -> Visualization Planning
  -> Dashboard Composition
  -> Rule-Based Insight Generation
  -> Applied Skill Rule Audit
  -> Report Export
```

각 단계는 반드시 적용된 Rule ID를 기록해야 한다.

예시:

```json
{
  "step": "risk_analysis",
  "rule_id": "RISK-001",
  "metric": "max_drawdown",
  "value": -0.274,
  "decision": "HIGH_DRAWDOWN_RISK",
  "message": "Maximum drawdown is below -20%, therefore drawdown risk is classified as high."
}
```

---

## 6. Mandatory Dashboard Sections

대시보드는 아래 순서를 기본값으로 사용한다.

1. **Data Profile**  
   행 수, 열 수, 날짜 범위, 결측률, 감지된 표준 스키마

2. **Executive Summary**  
   주요 수익률, 변동성, 최대낙폭, 샤프비율, 리스크 레벨

3. **Return Analysis**  
   가격 추세, 누적수익률, 자산별 성과 비교

4. **Risk Analysis**  
   변동성, 최대낙폭, 손실 구간, 하방 리스크

5. **Correlation & Diversification**  
   상관관계, 분산효과, 집중 리스크

6. **Rule-Based Insights**  
   사실, 해석, 주의사항을 분리한 인사이트

7. **Applied Skill Rules**  
   어떤 Rule이 어떤 결과를 생성했는지 추적

8. **Exportable Report**  
   HTML 또는 PDF 변환 가능한 리포트

---

## 7. Rule ID Convention

모든 규칙은 다음 ID 체계를 따른다.

| Prefix | Meaning |
|---|---|
| `DATA-*` | 데이터 구조 이해 및 품질 검사 |
| `SCHEMA-*` | 표준 스키마 매핑 |
| `METRIC-*` | 금융 지표 계산 |
| `VIS-*` | 시각화 선택 |
| `DASH-*` | 대시보드 레이아웃 구성 |
| `INSIGHT-*` | 인사이트 생성 |
| `RISK-*` | 리스크 분류 |
| `SAFE-*` | 금융 표현 안전장치 |
| `AUTO-*` | 바이브코딩 및 자동 생성 |
| `EXT-*` | 확장 기능 아이디어 |

---

## 8. Universal Rule Application Contract

각 Rule은 다음 구조를 가진다.

```yaml
rule_id: DATA-001
name: Date Column Detection
condition: More than 80% of non-null values in a column can be parsed as datetime.
action: Classify the column as date.
priority: high
output: standard_schema.date
failure_behavior: Ask user to select date column or continue with non-time-series mode.
```

구현체는 이 구조를 기준으로 Rule을 코드화하거나, 문서를 읽고 동등한 로직으로 구현해야 한다.

---

## 9. Global Safety Rules

FinSkillOS는 금융 분석 도구이며, 투자 자문 도구가 아니다.

금지 표현:

- 매수하세요
- 매도하세요
- 보유하세요
- 이 종목을 추천합니다
- 반드시 상승합니다
- 확실한 수익을 보장합니다
- buy this asset
- sell this asset
- guaranteed return

허용 표현:

- 관측된 데이터 기준으로 변동성이 높습니다.
- 최대낙폭이 커서 손실 구간 관리가 필요합니다.
- 수익률은 높지만 리스크 조정 성과는 제한적입니다.
- 데이터 기간이 짧아 해석의 불확실성이 큽니다.
- 특정 자산군에 비중이 집중되어 있습니다.

---

## 10. Success Criteria

FinSkillOS 제출물은 다음 조건을 만족해야 한다.

| Criterion | Minimum Requirement | Strong Submission Behavior |
|---|---|---|
| 범용성 | 단일 CSV 분석 | 서로 다른 스키마 3종 자동 처리 |
| Skills.md 설계 | 규칙 나열 | Rule ID, 조건, 행동, 예외 처리 정의 |
| 자동 대시보드 | 차트 표시 | 데이터 특성별 차트 자동 선택 |
| 바이브코딩 활용 | 문서 참고 | Skills.md가 코드 구조와 UI 흐름을 직접 지시 |
| 실용성 | 시각화 | 리스크 중심 인사이트, 리포트 export, audit trail |

---

## 11. Required Implementation Behavior

웹 서비스는 다음 동작을 제공해야 한다.

1. 사용자는 CSV 파일을 업로드할 수 있다.
2. 사용자는 샘플 데이터를 선택할 수 있다.
3. 시스템은 자동으로 컬럼을 분석한다.
4. 시스템은 표준 스키마 매핑 결과를 표시한다.
5. 시스템은 계산 가능한 지표만 계산한다.
6. 시스템은 데이터 구조에 맞는 차트를 자동 선택한다.
7. 시스템은 리스크 중심 인사이트를 생성한다.
8. 시스템은 적용된 Skill Rule 목록을 표시한다.
9. 시스템은 리포트를 다운로드할 수 있게 한다.
10. 시스템은 직접 투자 추천을 출력하지 않는다.

---

## 12. Recommended Demo Scenarios

### Scenario A - Single Asset Price Analysis

Input: `date`, `close`, `volume`  
Expected Output:

- 가격 추세선
- 일간 수익률
- 누적수익률
- 변동성
- 최대낙폭
- 리스크 요약

### Scenario B - Multi Asset Portfolio Analysis

Input: `date`, `asset`, `price`  
Expected Output:

- 자산별 누적수익률 비교
- 상관관계 heatmap
- risk-return scatter
- 자산별 지표 테이블
- 분산효과 해석

### Scenario C - Mixed Schema Auto Detection

Input: `trade_dt`, `ticker_name`, `nav_value`, `trading_amount`  
Expected Output:

- `trade_dt -> date`
- `ticker_name -> asset`
- `nav_value -> price`
- `trading_amount -> volume`
- 자동 분석 대시보드 생성

---

## 13. Evaluation Alignment

| Evaluation Item | Score | FinSkillOS Design Response |
|---|---:|---|
| 범용성 | 25 | 표준 스키마, 자동 컬럼 추론, long/wide/mixed schema 지원 |
| Skills.md 설계 | 25 | 기능별 Rule ID, 조건, 행동, 예외 처리, 안전장치 정의 |
| 대시보드 자동 생성 | 25 | chart planner, dashboard composer, metric engine, insight engine |
| 바이브코딩 활용 | 15 | 문서 기반 코드 생성 구조, 자동 파일 구조, acceptance tests |
| 실용성 및 창의성 | 10 | audit trail, no-advice guardrail, report export, enterprise 확장성 |

---

## 14. Final Principle

FinSkillOS의 핵심은 다음 문장으로 요약된다.

> 데이터가 바뀌어도 분석 기준은 흔들리지 않아야 하며, 분석 기준이 바뀌면 코드를 다시 작성하지 않고 Skills.md를 수정하여 시스템 행동을 바꿀 수 있어야 한다.
