# 04_insight_guardrails.md

**Skill Name:** Insight Generation & Financial Safety Guardrail Skill  
**Role:** 투자 분석 인사이트의 생성 방식, 표현 제한, 리스크 중심 해석 규칙을 정의한다.  
**Primary Evaluation Target:** Skills.md 설계, 실용성 및 창의성

---

## 1. Purpose

이 Skill은 FinSkillOS가 금융 데이터를 해석할 때 지켜야 할 인사이트 생성 규칙과 안전장치를 정의한다.

FinSkillOS는 투자 자문 서비스가 아니다. 따라서 특정 자산에 대한 매수, 매도, 보유 추천을 생성해서는 안 된다. 대신 과거 데이터에 근거한 성과, 리스크, 상관관계, 데이터 품질, 포트폴리오 집중도 등을 설명해야 한다.

---

## 2. Insight Structure

### INSIGHT-001: Three-Part Insight Format

모든 주요 인사이트는 다음 세 부분으로 구성한다.

```text
Fact: 관측된 수치 또는 차트 기반 사실
Interpretation: 해당 사실의 분석적 의미
Caution: 데이터 한계, 리스크, 불확실성
```

**Example**

```text
Fact: 최대낙폭은 -24.8%로 계산되었습니다.
Interpretation: 관측 기간 중 손실 구간이 깊어 drawdown risk가 높은 편입니다.
Caution: 과거 낙폭은 미래 손실 한도를 의미하지 않습니다.
```

---

### INSIGHT-002: Evidence Requirement

각 인사이트는 최소 하나의 근거를 포함해야 한다.

Allowed evidence:

- metric name and value
- chart name
- applied rule id
- data quality warning
- date range

**Example**

```text
Evidence: max_drawdown = -24.8%, rule = RISK-001, chart = Drawdown Chart
```

---

### INSIGHT-003: Risk-First Ordering

수익성과 리스크가 모두 중요한 경우, 리스크를 먼저 설명한다.

Bad:

```text
높은 수익률을 기록했으며, 일부 낙폭이 있었습니다.
```

Good:

```text
최대낙폭이 -22.1%로 높아 손실 구간 관리가 중요합니다. 다만 관측 기간의 누적수익률은 18.4%로 양호했습니다.
```

---

### INSIGHT-004: Data Limitation Disclosure

데이터 기간이 짧거나 결측률이 높으면 모든 요약 섹션에 제한사항을 표시한다.

Condition:

- observation_count < 60
- key column missing rate > 20%
- frequency unknown
- too few overlapping observations for correlation

Template:

```text
데이터 제한: 관측치가 {n}개로 제한적이므로 연율화 지표와 리스크 해석의 안정성이 낮을 수 있습니다.
```

---

## 3. Prohibited Financial Advice

### SAFE-001: Direct Recommendation Ban

다음 표현은 금지한다.

Korean:

```text
매수하세요
매도하세요
보유하세요
추천합니다
투자하세요
진입하세요
손절하세요
익절하세요
확실합니다
보장됩니다
```

English:

```text
buy
sell
hold
strong buy
strong sell
guaranteed
risk-free profit
must invest
```

---

### SAFE-002: Prediction Certainty Ban

미래 수익을 확정적으로 말하지 않는다.

Bad:

```text
이 자산은 앞으로 상승할 것입니다.
```

Good:

```text
과거 데이터 기준으로 상승 구간이 관측되었지만, 미래 성과를 보장하지는 않습니다.
```

---

### SAFE-003: Personalized Advice Ban

개인 투자자 상황을 전제로 한 조언을 하지 않는다.

Bad:

```text
당신의 포트폴리오에는 이 자산이 적합합니다.
```

Good:

```text
입력된 포트폴리오는 특정 자산군 비중이 높아 집중 리스크가 관측됩니다.
```

---

## 4. Insight Categories

### INSIGHT-CAT-001: Return Insight

Condition:

- total_return or annualized_return available

Template:

```text
Fact: 관측 기간의 누적수익률은 {total_return}%입니다.
Interpretation: 동일 기간 기준 성과 방향은 {positive_or_negative}입니다.
Caution: 수익률은 관측 기간에 민감하며, 기간을 바꾸면 결과가 달라질 수 있습니다.
```

---

### INSIGHT-CAT-002: Volatility Insight

Condition:

- annualized_volatility available

Template:

```text
Fact: 연율화 변동성은 {volatility}%입니다.
Interpretation: RISK-002 기준으로 변동성 리스크는 {risk_level}입니다.
Caution: 변동성은 가격 변화의 크기를 나타내지만 손실 방향만을 의미하지는 않습니다.
```

---

### INSIGHT-CAT-003: Drawdown Insight

Condition:

- max_drawdown available

Template:

```text
Fact: 최대낙폭은 {max_drawdown}%입니다.
Interpretation: RISK-001 기준으로 손실 구간 리스크는 {risk_level}입니다.
Caution: 최대낙폭은 과거 관측치이며 미래 최대 손실 한도가 아닙니다.
```

---

### INSIGHT-CAT-004: Sharpe Insight

Condition:

- sharpe_ratio available

Template:

```text
Fact: Sharpe Ratio는 {sharpe_ratio}입니다.
Interpretation: RISK-003 기준으로 위험 조정 성과는 {quality_level}로 분류됩니다.
Caution: Sharpe Ratio는 수익률 분포가 안정적이라는 가정에 영향을 받습니다.
```

---

### INSIGHT-CAT-005: Correlation Insight

Condition:

- correlation matrix available

Template:

```text
Fact: 자산 간 평균 상관계수는 {avg_corr}입니다.
Interpretation: 상관계수가 높을수록 분산효과가 제한될 수 있습니다.
Caution: 상관관계는 시장 국면에 따라 변할 수 있습니다.
```

---

### INSIGHT-CAT-006: Concentration Insight

Condition:

- weight column available
- max_weight or HHI available

Template:

```text
Fact: 가장 큰 자산 비중은 {max_weight}%입니다.
Interpretation: CONC-001 기준으로 특정 자산 집중도가 {level}입니다.
Caution: 집중도는 상승 참여도를 높일 수 있지만 손실 집중 리스크도 확대할 수 있습니다.
```

---

### INSIGHT-CAT-007: Data Quality Insight

Condition:

- quality warnings exist

Template:

```text
Fact: 데이터 품질 경고가 {warning_count}개 감지되었습니다.
Interpretation: 일부 분석 결과는 결측치, 중복값, 짧은 관측 기간의 영향을 받을 수 있습니다.
Caution: 의사결정 전 원본 데이터 검증이 필요합니다.
```

---

## 5. Risk Level Interpretation Text

### RISK-TEXT-001: LOW

```text
관측된 리스크 지표는 낮은 편입니다. 다만 낮은 과거 변동성이 미래 안정성을 보장하지는 않습니다.
```

### RISK-TEXT-002: MODERATE

```text
관측된 리스크 지표는 중간 수준입니다. 수익률과 손실 구간을 함께 검토해야 합니다.
```

### RISK-TEXT-003: HIGH

```text
관측된 리스크 지표가 높은 편입니다. 손실 구간, 변동성, 집중도에 대한 추가 검토가 필요합니다.
```

### RISK-TEXT-004: VERY HIGH

```text
관측된 리스크 지표가 매우 높습니다. 단순 수익률보다 손실 가능성과 회복 기간을 우선적으로 검토해야 합니다.
```

---

## 6. Insight Ranking Rules

### INSIGHT-RANK-001: Priority Order

인사이트는 다음 우선순위로 정렬한다.

1. Data quality warnings
2. Very high or high risk warnings
3. Drawdown risk
4. Volatility risk
5. Concentration risk
6. Return performance
7. Risk-adjusted performance
8. Correlation/diversification

---

### INSIGHT-RANK-002: Maximum Insight Count

대시보드 기본 화면에는 최대 5개의 핵심 인사이트를 표시한다.

상세 리포트에는 모든 인사이트를 표시할 수 있다.

---

## 7. Language Rules

### LANG-001: Default Language

기본 출력 언어는 한국어이다.

---

### LANG-002: Metric Names

금융 지표명은 한국어와 영어를 병기할 수 있다.

Example:

```text
최대낙폭(Maximum Drawdown)
연율화 변동성(Annualized Volatility)
샤프비율(Sharpe Ratio)
```

---

### LANG-003: Tone

문체는 다음 기준을 따른다.

- 전문적
- 단정하지만 과장하지 않음
- 투자 권유처럼 보이지 않음
- 리스크와 제한사항을 명확히 표시

---

## 8. Insight Output Schema

Insight Engine은 다음 구조를 출력해야 한다.

```json
{
  "insights": [
    {
      "id": "insight_001",
      "category": "drawdown",
      "severity": "HIGH",
      "fact": "최대낙폭은 -24.8%입니다.",
      "interpretation": "RISK-001 기준으로 손실 구간 리스크가 높습니다.",
      "caution": "과거 최대낙폭은 미래 손실 한도가 아닙니다.",
      "evidence": {
        "metric": "max_drawdown",
        "value": -0.248,
        "rule_id": "RISK-001",
        "chart": "drawdown_chart"
      }
    }
  ],
  "blocked_terms": [],
  "applied_rules": ["INSIGHT-001", "SAFE-001", "RISK-TEXT-003"]
}
```

---

## 9. Post-Generation Safety Check

### SAFE-POST-001: Forbidden Term Scan

인사이트 생성 후 금지 표현 목록을 스캔한다.

**If forbidden term exists:**

- 해당 문장을 재작성한다.
- `safety_rewrite_applied = true`를 기록한다.

---

### SAFE-POST-002: Evidence Check

각 인사이트에 evidence가 없으면 dashboard에 표시하지 않는다.

---

### SAFE-POST-003: Uncertainty Check

데이터 품질 경고가 있는데 인사이트에 caution이 없으면 caution 문장을 추가한다.

---

## 10. Acceptance Tests

### Test A: High Return and High Drawdown

Expected:

- Risk first
- Return second
- No direct recommendation

---

### Test B: Short Dataset

Expected:

- Data limitation warning
- Annualized metric caution

---

### Test C: Forbidden Term

Input generated sentence:

```text
이 자산은 매수하기 좋습니다.
```

Expected rewrite:

```text
이 자산은 관측 기간 동안 양호한 수익률을 보였지만, 투자 판단에는 추가적인 리스크 검토가 필요합니다.
```

---

## 11. Final Insight Principle

> 금융 인사이트는 사용자를 설득하기 위한 문장이 아니라, 숫자의 의미와 한계를 동시에 설명하는 감사 가능한 해석이어야 한다.
