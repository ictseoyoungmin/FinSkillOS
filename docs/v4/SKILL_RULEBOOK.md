# Skill Rulebook (v4.3) — absorbed from legacy v1

Canonical rule definitions for the Skill Layer (Phase 20). This document
**absorbed the rule IP from the v1 `Skills.md` set** (formerly `legacy_v1/`,
removed in slice 282) so the precise formulas, thresholds, insight structure, and
safety vocabulary it defined are preserved. It is the reference the migration
targets; `docs/v4/PHASE_20_Skill_Layer.md` is the architecture.

Status legend per rule: **[live]** implemented in the current engine ·
**[skill]** implemented in the new Skill Layer · **[ref]** preserved here as the
spec to implement when a consumer exists (not yet in code).

The legacy product analysed *uploaded CSV datasets*; the current product reads a
*live portfolio + market state*. Some legacy rules therefore become reference
definitions for skills we will add (Sharpe/Sortino/Calmar/HHI/VaR), not literal
ports. Where the current engine already encodes a stricter, account-specific
version (e.g. the Drawdown guard), that version wins and the legacy band table is
kept only as the descriptive-classification reference.

---

## 1. Metric definitions (legacy `02_financial_metrics.md`)

Global assumptions:
- **METRIC-BASE-001** returns are decimal internally (5% → 0.05); a detected
  percent-scale input is /100 with the conversion recorded in the audit. *[live]*
- **METRIC-BASE-002** annualization periods/year: Daily 252 · Weekly 52 ·
  Monthly 12 · Quarterly 4 · Yearly 1 · Unknown 252 (+warning). *[ref]*
- **METRIC-BASE-003** risk-free rate defaults to 0.0 and the dashboard must
  disclose the assumption when used in Sharpe. *[ref]*

Formulas (all `[ref]` unless marked — none of Sharpe/Sortino/Calmar/MaxDD-from-
returns/VaR/HHI exist in the current engine today; preserve for the future
`SIGNAL.*` / `RISK.*` skill family):

| ID | Metric | Formula |
|---|---|---|
| METRIC-001 | Period return | `price_t / price_{t-1} - 1` (first = null) |
| METRIC-002 | Cumulative return | `∏(1 + return_i) - 1` |
| METRIC-003 | Total return | `final/initial - 1` or `∏(1+r) - 1` |
| METRIC-004 | Annualized return | `(1 + total_return)^(ppy / n_periods) - 1`; skip if `n ≤ 1`; <60d → uncertainty warning |
| METRIC-005 | Annualized volatility | `std(period_return) * sqrt(ppy)` |
| METRIC-006 | Downside deviation | `sqrt(mean(min(r - target, 0)^2)) * sqrt(ppy)`; target 0.0 |
| METRIC-007 | Max drawdown | `wealth_t = ∏(1+r); dd_t = wealth_t/running_max_t - 1; max_dd = min(dd_t)` |
| METRIC-008 | Historical VaR | length ≥ 60: `percentile(r, 5)` / `percentile(r, 1)`; label "approximation", not a loss cap |
| METRIC-009 | Sharpe | `(ann_return - rf) / ann_vol`; skip if vol 0/null |
| METRIC-010 | Sortino | `(ann_return - target) / downside_dev`; skip if dd 0/null |
| METRIC-011 | Calmar | `ann_return / abs(max_dd)`; skip if max_dd 0/null |
| METRIC-012 | Per-asset metric table | per asset: total/ann return, ann vol, max_dd, sharpe, sortino, obs_count |
| METRIC-013 | Correlation matrix | Pearson, pairwise-valid; hide if too few common obs |
| METRIC-014 | Portfolio return from weights | `∑ w_i * r_{i,t}`; disclose rebalancing assumption |
| METRIC-015 | Concentration | `max_weight = max(w_i); hhi = ∑ w_i^2`; max_weight>0.5 → warn; hhi>0.25 → high |

Display: returns/vol/drawdown as percent; ratios to 2 dp; uncomputable → `N/A`
with a reason note. *[live policy — matches memory `display-decimal-policy`]*

> **HHI is a precision upgrade candidate.** The current `concentration_guard`
> uses sector-weight bands (35%/50%); METRIC-015's Herfindahl index + max-weight
> is a more precise concentration measure. See §5 refinement note.

## 2. Risk classification bands (legacy `02 §7`) — descriptive-classification reference

| ID | Dimension | Bands |
|---|---|---|
| RISK-001 | Drawdown | ≥-5% LOW · -5..-15 MODERATE · -15..-25 HIGH · <-25 VERY_HIGH |
| RISK-002 | Volatility (ann.) | <10% LOW · 10-20 MODERATE · 20-35 HIGH · >35 VERY_HIGH |
| RISK-003 | Sharpe quality | <0 negative · 0-0.5 weak · 0.5-1 moderate · 1-2 strong · >2 very strong (verify data) |
| RISK-004 | Data sufficiency | <30 very limited · 30-59 limited · 60-251 medium · ≥252 sufficient |

These classify a *historical dataset*. The live **`RISK.DRAWDOWN` skill / drawdown
guard** uses a stricter account-protection ladder (-5/-10/-15 → PASS/WARN/FAIL),
which is the operating-mode trigger and **takes precedence**; RISK-001 above is
kept only as the descriptive-label reference. RISK-002/003/004 are `[ref]` for a
future `SIGNAL.*` skill family.

## 3. Insight structure (legacy `04_insight_guardrails.md`)

- **INSIGHT-001** three-part format: **Fact / Interpretation / Caution.** Maps to
  the v4.2 Integrated-Interpretation shape (verdict / whyItMatters /
  whatRemainsUncertain). *[live, shape-equivalent]*
- **INSIGHT-002** every insight carries ≥1 evidence (metric+value, chart, rule
  id, data-quality warning, or date range). The Skill Layer's `fired_rule_ids` +
  `evidence` satisfy this. *[skill]*
- **INSIGHT-003** **risk-first ordering** — when both matter, state risk before
  return. *[ref — adopt in skill aggregation]*
- **INSIGHT-004** disclose data limitation when obs<60 / key-column missing>20% /
  frequency unknown / too few correlation obs. *[ref]*
- **INSIGHT-RANK-001** priority order: data-quality → very-high/high risk →
  drawdown → volatility → concentration → return → risk-adjusted →
  correlation. *[ref — adopt as the multi-skill aggregation order]*
- **INSIGHT-RANK-002** ≤5 headline insights on the default surface; full set in
  detail/report. *[live — cockpit density follows this]*

## 4. Safety vocabulary (legacy `04 §3` SAFE-001/002/003)

Single forbidden-wording policy lives in `guards.base.find_forbidden_term`
(shared by guards + the Skill Layer). The legacy list is broader than the
original scanner; the **imperative** forms below are absorbed into the scanner
(slice 281) because they are directive and do not collide with descriptive copy
(e.g. regime text "회복 구간으로 진입하고"): `추천합니다`, `진입하세요`,
`손절하세요`, `익절하세요`, `보유하세요`, `투자하세요`, `must invest`,
`risk-free profit`. Bare nouns (`추천`, `보유`, `투자`) are **not** added — they
appear constantly in descriptive copy ("보유 종목", "투자 운영체제") and would
false-positive. `sell-the-news` stays allow-listed (risk pattern, not an order).

Post-generation checks (legacy SAFE-POST-001/002/003): forbidden-term scan with
rewrite flag, evidence-required-to-display, auto-append caution when a
data-quality warning lacks one. *[ref — fold into the runner's safety step]*

## 5. Audit model (legacy `engine/rule_engine.py`) — the "Applied Skill Rules" trail

The legacy `AppliedRule(rule_id, step, condition, action, result, severity)` +
`RuleAuditLog` (prefix→category map, dedup, summary-by-prefix) is a richer audit
than the current `SkillRunRecord` (which holds `fired_rule_ids` + evidence).
**Absorb at Phase 20.2** when the Risk Firewall "Applied Skill Rules" panel is
built: extend `Rule` with optional `condition`/`action` copy and carry them +
the prefix→category mapping into the audit record. Rule-ID prefixes (v1 §7,
namespaced in v4.3 as `<DOMAIN>.<SKILL>-<NNN>`): RISK / REGIME / SIGNAL / EVENT /
NEWS / GOAL / OPS (+ legacy DATA/SCHEMA/METRIC/VIS/DASH/INSIGHT/SAFE/AUTO/EXT).

## 6. Productization vision (legacy `06_extension_ideas.md`)

The legacy roadmap already named this phase: **EXT-001 "Skill-Governed Analytics
Layer"**, EXT-FEATURE-002 "Skill Versioning", EXT-CREATIVE-001 "Skill Rule Audit
Trail", EXT-CREATIVE-002 "Analysis Policy as Markdown", EXT-COMP-001..003
(compliance phrase filter / disclaimer generator / audit export). v4.3 / Phase 20
is the execution of EXT-001. Stress/scenario (EXT-FEATURE-004), benchmark compare
(EXT-FEATURE-006), and API mode (EXT-FEATURE-007) remain open future ideas.

---

## Refinement notes (stale-rule precision candidates — need explicit sign-off)

These change *live risk behaviour*, so they are recorded here, not silently
applied:

1. **Drawdown granularity.** ✅ **Done (slice 283).** The WARN band (-5..-10) was
   split into the two documented YELLOW sub-bands — `RISK.DRAWDOWN-002` (-5..-8,
   give-back) and `-003` (-8..-10, Yellow Alert) — in both the skill and the
   guard, kept in lockstep (parity-tested). status/risk_level are unchanged; only
   the descriptive copy + Rule IDs are finer (ORANGE→-004, RED→-005). The
   skill is the source of truth and the guard follows it.
2. **Concentration → HHI.** Add METRIC-015's Herfindahl index + max-weight to the
   concentration skill alongside the current sector bands. *(in progress — slice
   284)*

Both are good "edit the spec, not the code" demonstrations once approved.
