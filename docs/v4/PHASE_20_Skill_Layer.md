# Phase 20 — Skill Layer (v4.3)

Continues the integer slice sequence (v4.2 / Phase 19 ended at slice 278). Each
slice is one Docker-verified commit on `main`.

> **Why now.** The product is named Fin**Skill**OS, but the "skill" abstraction
> that defined v1 — a *governed, document-defined, auditable rule pack* whose
> central promise was "change behaviour by editing the skill spec, not the code"
> — was dissolved during the v2.1 rewrite into a set of hardcoded Python
> subsystems (`guards/`, `regime/`, `signals/`, `interpretation/`). This phase
> re-establishes **Skill as a first-class layer**, without throwing away the
> mature engine code underneath it.

This is a **redesign of an internal abstraction, not a product rewrite.** The
descriptive-only contract, the live/empty/error data layer, the v4.2 cockpit,
and every existing engine rule stay. We are giving the rules a common home,
a common shape, and a common audit trail.

---

## 1. What a "Skill" was, is, and will be

### v1 (rule IP absorbed into `docs/v4/SKILL_RULEBOOK.md`; `legacy_v1/` removed in slice 282)
`Skills.md` + `skills/01–06` defined analysis policy as **Rule IDs** (`DATA-001`,
`RISK-001`, …) with `condition → action → output → failure_behavior`, plus a
global safety guardrail and an **Applied Skill Rules audit trail**. The engine
read the spec and recorded which rules fired. Core principle (§14):

> 데이터가 바뀌어도 분석 기준은 흔들리지 않아야 하며, 분석 기준이 바뀌면 코드를
> 다시 작성하지 않고 Skill 문서를 수정하여 시스템 행동을 바꿀 수 있어야 한다.

### Current (v2.1–v4.2) — the same idea, fragmented and hardcoded
| Subsystem | Shape today | Skill-like traits it already has | What's missing |
|---|---|---|---|
| `signals/` (technical, macro, sector, sentiment, portfolio) | pure feature functions | deterministic, pure | not a skill — these are skill *inputs* |
| `regime/` (engine + `regime_rules` + conflict_resolver) | classifier over a thresholds module | **`RULE_VERSION`**, conflict resolution | thresholds hardcoded; no Rule-ID audit |
| `guards/` (8× `evaluate(GuardInput)→GuardResult`) | pure rule-pack functions | **evidence dict**, **watch_next**, **safety enforcement**, deterministic | thresholds hardcoded in `base.py`; guard *name* but no per-band Rule IDs; risk-domain only |
| `interpretation/` (market/news/portfolio + safety_filter) | prose builders | safety filter, templates | decoupled from the rules that produced the state |
| `kernel/rule_engine.py` | **empty stub** | — | the intended-but-never-built home for a unified runner |
| `services/*_service.py` | per-domain orchestration | builds input → runs → aggregates → persists | one orchestrator per domain; no unified skill run/audit |

The `guards/` package is already 90% of the target shape — it is the migration
template, not something to discard.

### v4.3 target — Skill as a first-class governing rule pack
A **Skill** is a versioned, declarative, auditable unit that:
1. **Declares its inputs** — which signal/state slices it reads (no DB access
   inside a skill; the runner assembles the snapshot, exactly as
   `RiskGuardService` assembles `GuardInput` today).
2. **Holds an ordered rule ladder** — each rung is a `Rule` with a stable
   **Rule ID**, a condition, and the descriptive result it produces. The common
   threshold-band case is expressed as *data* (so thresholds + copy change
   without touching logic); a Python predicate is the escape hatch for the rare
   rule that needs real computation.
3. **Emits a standard `SkillResult`** in the v4.2 evidence shape
   (judgment / drivers / conflicts / watchpoints + evidence + the **fired Rule
   IDs**) so a skill feeds the cockpit and the agent directly.
4. **Inherits one safety contract** — the existing
   `assert_no_forbidden_wording` runs on every `SkillResult`, centrally, so no
   skill can leak buy/sell wording.
5. **Writes an audit trail** — a `SkillRunRecord` capturing skill id + version +
   which Rule IDs fired with what evidence. This revives v1's "Applied Skill
   Rules" and is the same idea the cockpit's v4.2 evidence panels already show,
   now generated uniformly.

---

## 2. Architecture

```
finskillos/skills/                 ← NEW first-class package
  base.py        SkillContext, Rule, RuleLadder, SkillSpec, SkillResult,
                 SkillRunRecord  (dataclasses, no DB, pure)
  runner.py      SkillRegistry + run_skill()/run_all(): resolve inputs from a
                 state snapshot, evaluate the ladder, enforce safety, build the
                 SkillResult + SkillRunRecord (the audit trail)
  safety.py      thin re-export/adapter of guards.base.assert_no_forbidden_wording
                 generalised to SkillResult copy
  library/       one module per skill (declarative spec + any predicate fns)
    drawdown_skill.py   (first migration — Phase 20.1)

finskillos/kernel/rule_engine.py   ← was empty; becomes a thin façade that
                                     re-exports the skills runner (fulfilling the
                                     stub's original intent)
```

**Snapshot, not DB.** A skill never touches a `Session`. The runner takes a
`SkillContext` — a read snapshot the *service* assembles from the existing
repositories (this is exactly today's `GuardInput`, generalised). This keeps
skills pure, deterministic, and offline-testable (memory `offline-test-data`).

**Additive migration.** The live `RiskGuardService` path is untouched while the
skill layer is proven. Each guard is migrated as a skill *behind a parity test*
(new skill output == legacy guard output for representative inputs) before any
route is switched over. No false-green, no behaviour drift.

### Core types (shape, not final code)
```python
@dataclass(frozen=True)
class Rule:
    rule_id: str                    # e.g. "DRAWDOWN-002"
    when: Callable[[SkillContext], bool]
    status: str                     # PASS / INFO / WARN / FAIL / BLOCKED
    risk_level: str                 # GREEN / YELLOW / ORANGE / RED / UNKNOWN
    title: str
    message: Callable[[SkillContext], str] | str
    evidence: Callable[[SkillContext], dict] | None = None
    watch_next: tuple[str, ...] = ()

@dataclass(frozen=True)
class SkillSpec:
    skill_id: str                   # e.g. "RISK.DRAWDOWN"
    version: str                    # e.g. "drawdown-v1-2026-06-17"
    title: str
    reads: tuple[str, ...]          # declared input slices (audit/doc)
    ladder: tuple[Rule, ...]        # first matching rung wins (ordered)
    fallback: Rule                  # when no rung matches (UNKNOWN/INFO)
    safety: str = "descriptive-only"

@dataclass(frozen=True)
class SkillResult:                  # the v4.2 evidence shape
    skill_id: str; version: str
    status: str; risk_level: str
    title: str; message: str
    evidence: dict
    watch_next: tuple[str, ...]
    fired_rule_ids: tuple[str, ...]

@dataclass(frozen=True)
class SkillRunRecord:               # the audit trail row
    skill_id: str; version: str
    fired_rule_ids: tuple[str, ...]
    status: str; risk_level: str
    evidence: dict
    ran_at: datetime
```

For threshold ladders a small helper (`band_rule(rule_id, lo, hi, …)`) builds
the `Rule` so a guard's bands read as a table — the "edit thresholds without
touching logic" promise, in typed Python rather than YAML (keeps type-safety and
the codebase's dataclass idiom; YAML/JSON authoring is a possible later slice if
non-developer editing is ever needed).

---

## 3. Rule ID convention (revived from v1 §7, namespaced)

`<DOMAIN>.<SKILL>-<NNN>` — e.g. `RISK.DRAWDOWN-002`, `REGIME.TREND-001`,
`NEWS.IMPACT-003`. Domains: `RISK`, `REGIME`, `SIGNAL`, `EVENT`, `NEWS`, `GOAL`,
`OPS`. The audit trail records the fully-qualified fired IDs so any cockpit panel
or the agent can answer "*which rule produced this?*" without re-running.

---

## 4. Phasing

- **20.0 — Skill core + first migration (prototype).** Build `finskillos/skills/`
  (base + runner + safety + audit) and migrate the **Drawdown guard** into
  `library/drawdown_skill.py` as a declarative ladder (`RISK.DRAWDOWN-001..004`).
  Prove it with a **parity test** vs `guards/drawdown_guard.py` across the band
  boundaries + the missing-data case, and an **audit test** (fired Rule IDs +
  safety). Additive — live path untouched. *(This is the slice built alongside
  this doc.)*
- **20.1 — RISK registry via the Strangler-Fig seam.** ✅ **Done (slice 285).**
  Rather than rewrite all 7 remaining guards before going live, the registry runs
  every guard *now*: `RISK.DRAWDOWN` declarative + 7 `GuardBackedSkill` seams
  (`guard_adapter.py`) wrapping each guard's `evaluate`, in the legacy ladder
  order. `SkillRegistry` is polymorphic (spec or seam); `run_all` produces the
  unified results + audit. Each guard converts to a declarative `SkillSpec` behind
  the seam incrementally, parity-gated. (`RISK.CONCENTRATION_HHI` from slice 284
  is an extra declarative skill, not yet in the live 8.)
- **20.2 — `RiskGuardService` runs through the registry.** ✅ **Done (slice 286).**
  `_run_all_guards` reimplemented over the registry (SkillResult → GuardResult by
  canonical name); `evaluate()` byte-for-byte unchanged → parity-safe. New
  `applied_rules(account_id)` surfaces the **Applied Skill Rules** audit
  (SkillRunRecord per skill) — ready to feed the Risk Firewall panel.
- **20.2b — Convert all 8 guards to declarative.** ✅ **Done (slices 288–291).**
  Goal + Cash (288), Overheat (289), Regime (290, + callable status/risk_level
  for the data-derived RED/ORANGE level), and Single-position + Sector-
  concentration + Event-risk (291). Every guard is now a declarative `SkillSpec`,
  each parity-tested byte-for-byte; the Strangler-Fig seam is retired from
  `risk_registry` (`GuardBackedSkill` kept as reusable infra + unit-tested). The
  RISK domain is fully "edit the spec, not the code".
- **20.2c — Applied Skill Rules panel.** ✅ **Done (slices 293–294).** Backend:
  `evaluate_with_audit` + `AppliedSkillRule` schema + `/api/risk-firewall`
  `appliedRules`. UI: `AppliedSkillRulesPanel` on the Risk Firewall tab (skill id
  + fired Rule ID + status), Playwright-verified live. The RISK domain is now a
  fully-realized governing rule-pack: declarative, live, audited, and surfaced.
- **20.3 — Express the regime classifier as a Skill family** (`REGIME.*`).
  - **20.3a** ✅ **Done (slice 296).** REGIME enters the Skill Layer via the
    classification seam: `SkillResult.label` (category output), `RegimeBackedSkill`
    wrapping `classify_regime`, `build_regime_registry`, parity-tested. Additive.
  - **20.3b** (next) — convert `_classify_state` (the score→state ladder) into
    declarative classification rungs behind the seam; route the regime read path
    through the registry. Larger; the classifier is multi-dimensional (scores),
    not a single threshold ladder, so it needs careful per-rung parity.
- **20.4 — Interpretation as skills** (`NEWS.*`, `SIGNAL.*`): the prose builders
  become skills whose evidence is the fired rule set, unifying state→prose under
  one audit.
- **20.x — Cleanup:** a Skill Catalog doc auto-derivable from the registry
  (id, version, reads, rule ladder) so the spec is browsable; agent read-tool
  that answers "which skills/rules fired for this verdict".

---

## 5. Guardrails carried into every slice
- Descriptive-only, enforced centrally on every `SkillResult` (no buy/sell).
- Skills are pure + deterministic + offline-testable; no DB inside a skill.
- Display-decimal policy unchanged (amounts/qty integer, %/unit-price decimals).
- Migration is parity-gated: never replace a live guard until the new skill
  reproduces it exactly.

---

## 6. Success definition for the phase
A reviewer can open one `library/*_skill.py`, read the rule ladder as a table,
change a threshold or a line of copy, and the system's behaviour + its audit
trail change accordingly — with no edit to engine/service/route code. That is
v1's `Skills.md` promise, restored on top of the v4.x engine.

---
Status: 20.0–20.2c + 20.3a + Skill Catalog done (slices 280–297). The **RISK
domain is fully realized** (8 declarative skills, live, audited, surfaced); REGIME
is in the Skill Layer via the classification seam; the **Skill Catalog**
(`docs/v4/SKILL_CATALOG.md`) auto-derives from the registries. Next: 20.3b
(convert the regime `_classify_state` ladder declaratively + route the regime read
path through the registry), 20.4 (interpretation as `NEWS.*`/`SIGNAL.*` skills),
agent read-tool ("which skills/rules fired for this verdict").
