# Skill Catalog (auto-generated)

Generated from the live skill registries by `finskillos.skills.catalog.build_catalog` (Phase 20.x). Do not edit by hand — run `python -m finskillos.skills.catalog` to regenerate. A test keeps this file in sync with the registries.

## RISK

### RISK.CASH_RATIO — `cash-ratio-v1-2026-06-17`

Cash ratio — liquidity buffer vs the account minimum

- **reads:** cash_value, total_value, min_cash_ratio

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.CASH_RATIO-001` | PASS | GREEN | 현금비중이 최소 기준을 충족합니다. |
| `RISK.CASH_RATIO-002` | WARN | YELLOW | 현금비중이 목표 최소치 아래로 내려갔습니다. |
| `RISK.CASH_RATIO-003` | FAIL | ORANGE | 현금비중이 위험 수준까지 낮아졌습니다. |
| `RISK.CASH_RATIO-000` | INFO | UNKNOWN | 포트폴리오 총평가금액이 0이라 현금비중을 계산할 수 없습니다. |

### RISK.SINGLE_POSITION — `single-position-v1-2026-06-17`

Single position limit — per-name size ceiling

- **reads:** positions, single_position_limit

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.SINGLE_POSITION-002` | FAIL | ORANGE | 단일 종목 한도를 초과한 포지션이 있습니다. |
| `RISK.SINGLE_POSITION-001` | WARN | YELLOW | 단일 종목 한도 근접 포지션이 있습니다. |
| `RISK.SINGLE_POSITION-000` | PASS | GREEN | 모든 포지션이 단일 종목 한도 이내입니다. |

### RISK.SECTOR_CONCENTRATION — `sector-concentration-v1-2026-06-17`

Sector concentration — heaviest-sector share band

- **reads:** positions

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.SECTOR_CONCENTRATION-003` | FAIL | ORANGE | 섹터 집중도가 위험 수준까지 높아졌습니다. |
| `RISK.SECTOR_CONCENTRATION-002` | WARN | YELLOW | 특정 섹터 비중이 빠르게 커지고 있습니다. |
| `RISK.SECTOR_CONCENTRATION-001` | PASS | GREEN | 섹터 집중도가 안전 구간에 있습니다. |
| `RISK.SECTOR_CONCENTRATION-004` | INFO | UNKNOWN | 포지션 평가금액이 0이라 섹터 노출을 계산할 수 없습니다. |
| `RISK.SECTOR_CONCENTRATION-000` | INFO | UNKNOWN | 포지션이 없어 섹터 노출을 계산할 수 없습니다. |

### RISK.DRAWDOWN — `drawdown-v1-2026-06-17`

Drawdown — peak-to-current loss band

- **reads:** drawdown_pct, peak_value, total_value

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.DRAWDOWN-001` | PASS | GREEN | 고점 대비 drawdown이 일반 변동 범위입니다. |
| `RISK.DRAWDOWN-002` | WARN | YELLOW | 고점 대비 -5% ~ -8% 구간 — 최근 수익 일부 반납. |
| `RISK.DRAWDOWN-003` | WARN | YELLOW | 고점 대비 -8% ~ -10% 구간 — Yellow Alert. |
| `RISK.DRAWDOWN-004` | FAIL | ORANGE | 고점 대비 -10% 이상 손실 — Risk Reduction Mode. |
| `RISK.DRAWDOWN-005` | FAIL | RED | 고점 대비 -15% 이상 손실 — Defensive Mode. |
| `RISK.DRAWDOWN-000` | INFO | UNKNOWN | drawdown을 계산할 수 있는 peak / total_value 정보가 없습니다. |

### RISK.GOAL_PROTECTION — `goal-v1-2026-06-17`

Goal protection — progress-band operating posture

- **reads:** goal_progress_pct

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.GOAL_PROTECTION-004` | BLOCKED | RED | 목표 달성 — 챌린지 완료 단계입니다. |
| `RISK.GOAL_PROTECTION-003` | FAIL | ORANGE | 목표 근접 구간 — 보호 모드로 전환할 시점입니다. |
| `RISK.GOAL_PROTECTION-002` | WARN | YELLOW | 목표 진행률이 상승 구간 — 무리한 위험 확대 경계. |
| `RISK.GOAL_PROTECTION-001` | PASS | GREEN | 목표 진행률이 정상 운영 구간에 있습니다. |
| `RISK.GOAL_PROTECTION-000` | INFO | UNKNOWN | 목표 진행률 정보가 없어 보호 모드를 평가할 수 없습니다. |

### RISK.REGIME_RISK — `regime-risk-v1-2026-06-17`

Regime risk — operating posture by market regime

- **reads:** regime, regime_risk_level, decision_mode

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.REGIME_RISK-001` | PASS | GREEN | 시장 regime이 우호적인 구간입니다. |
| `RISK.REGIME_RISK-002` | WARN | YELLOW | 시장 regime이 주의 구간으로 진입했습니다. |
| `RISK.REGIME_RISK-003` | FAIL | (dynamic) | 시장 regime이 방어 구간입니다. |
| `RISK.REGIME_RISK-004` | INFO | UNKNOWN | 시장 regime 정보를 해석할 수 없습니다. |
| `RISK.REGIME_RISK-000` | INFO | UNKNOWN | 시장 regime 정보가 아직 수집되지 않았습니다. |

### RISK.OVERHEAT_ENTRY — `overheat-v1-2026-06-17`

Overheat entry — chase-exposure constraint by regime

- **reads:** regime, decision_mode

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.OVERHEAT_ENTRY-002` | FAIL | ORANGE | 시장이 RISK_ON_OVERHEAT — 추격형 노출 제약 구간입니다. |
| `RISK.OVERHEAT_ENTRY-001` | WARN | YELLOW | DISTRIBUTION_RISK — 공격적 노출 확대에 제약이 붙습니다. |
| `RISK.OVERHEAT_ENTRY-003` | PASS | GREEN | 현재 regime 기준 추격형 노출 제약은 낮습니다. |
| `RISK.OVERHEAT_ENTRY-000` | INFO | UNKNOWN | 시장 regime 정보가 없어 overheat 진입 제한을 평가할 수 없습니다. |

### RISK.EVENT_RISK — `event-risk-v1-2026-06-17`

Event risk — descriptive Catalyst Watch exposure

- **reads:** event_risk

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.EVENT_RISK-002` | INFO | GREEN | (dynamic) |
| `RISK.EVENT_RISK-001` | INFO | GREEN | 추적 중인 예정 이벤트가 없습니다. |
| `RISK.EVENT_RISK-000` | INFO | GREEN | Catalyst Watch 이벤트 근거가 아직 없습니다. |

### RISK.CONCENTRATION_HHI — `concentration-hhi-v1-2026-06-17`

Concentration — Herfindahl index + max single-name weight

- **reads:** positions, total_value

| Rule | Status | Risk | Title |
|---|---|---|---|
| `RISK.CONCENTRATION_HHI-003` | WARN | YELLOW | 단일 종목 비중이 과반입니다. |
| `RISK.CONCENTRATION_HHI-002` | WARN | YELLOW | HHI 기준 집중도가 높습니다. |
| `RISK.CONCENTRATION_HHI-001` | PASS | GREEN | 종목 집중도가 분산 범위입니다. |
| `RISK.CONCENTRATION_HHI-000` | INFO | UNKNOWN | 집중도를 계산할 포지션 / 총액 정보가 없습니다. |

## REGIME

### REGIME.CLASSIFY — `regime-v1-2026-05-18`

Classification seam — the priority ladder below is a shared table the
engine and skill both walk (first match wins); prose / confidence stay in
the engine.

| Rule | Regime state |
|---|---|
| `REGIME.CLASSIFY-000` | UNKNOWN (too few inputs) |
| `REGIME.CLASSIFY-001` | PANIC |
| `REGIME.CLASSIFY-002` | RISK_OFF |
| `REGIME.CLASSIFY-003` | DEFENSIVE_TRANSITION |
| `REGIME.CLASSIFY-004` | RISK_ON_OVERHEAT |
| `REGIME.CLASSIFY-005` | RISK_ON_OVERHEAT |
| `REGIME.CLASSIFY-006` | DISTRIBUTION_RISK |
| `REGIME.CLASSIFY-007` | AGGRESSIVE_RISK_ON |
| `REGIME.CLASSIFY-008` | HEALTHY_BULL |
| `REGIME.CLASSIFY-009` | RECOVERY |
| `REGIME.CLASSIFY-010` | HEALTHY_BULL |
| `REGIME.CLASSIFY-999` | UNKNOWN (no rule matched) |

## EVENT

### EVENT.SCORE — `event-score-v1-2026-06-17`

Event risk score — exposure band (LOW / MODERATE / HIGH / CRITICAL)

- **reads:** event_risk_score

| Rule | Status | Risk | Title |
|---|---|---|---|
| `EVENT.SCORE-004` | INFO | RED | 이벤트 노출도 CRITICAL. |
| `EVENT.SCORE-003` | INFO | ORANGE | 이벤트 노출도 HIGH. |
| `EVENT.SCORE-002` | INFO | YELLOW | 이벤트 노출도 MODERATE. |
| `EVENT.SCORE-001` | INFO | GREEN | 이벤트 노출도 LOW. |
| `EVENT.SCORE-000` | INFO | UNKNOWN | 이벤트 리스크 점수를 계산할 수 없습니다. |
