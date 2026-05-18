# 07 — Command Center UI

## Goal

Implement the primary cockpit screen for FinSkillOS v2.1.

## UX priority

The first screen should immediately answer:

```text
What is the current state?
What is the risk?
What mode should I operate in today?
What should I watch next?
```

## Required sections

```text
Market State Banner
Goal Progress
Portfolio Value
Decision Mode
Key Risk Alerts
AI/Template Interpretation
Suggested Action Mode
Portfolio Overview
Cash / Buying Power
```

## Data source

The page should read a compact state snapshot first:

```text
current account state
latest portfolio snapshot
latest market regime
latest risk alerts
latest goal status
```

Avoid heavy chart rendering on first load.

## UI wording examples

Good:

```text
"Risk-On / Overheat Warning"
"Momentum is strong but crowded."
"Existing winner management is favored over aggressive new chase entries."
"Watch breadth and VIX for deterioration."
```

Avoid:

```text
"Buy now."
"Sell today."
"This will go up."
```

## Files

```text
finskillos/ui/pages/command_center.py
finskillos/ui/components/state_banner.py
finskillos/ui/components/metric_card.py
finskillos/ui/components/alert_card.py
finskillos/ui/components/interpreter_panel.py
```

## Acceptance criteria

- Initial render does not trigger full market data refresh.
- Page shows goal progress, regime, risk alerts, and interpretation.
- Empty-state UI exists if there is no portfolio data.
- Safety language is used consistently.
- Page renders with sample seed data.

## Test commands

```bash
pytest tests/test_ui_command_center.py -q
streamlit run app.py
```

## Completion placeholder

```text
Status: DONE (2026-05-18)

Implemented:
- Streamlit app shell (finskillos/ui/app_shell.py) with OS-style top
  navigation (Control Room / Market Kernel / Risk Firewall /
  Mission Control / Catalyst Watch / Trade Memory /
  Analysis Workspace / System Ops) and a tabbed sidebar radio.
  Streamlit and DB-session imports are kept inside run_app so the
  module imports cleanly in non-Streamlit contexts (tests, type-check).
- Control Room page (finskillos/ui/pages/control_room.py) — single-pass
  render of the four core cards using the new ControlRoomViewModel.
- Mission Control / goal summary card — current value, target value,
  remaining amount, progress %, goal mode badge, early-stop banner.
- Market Kernel / regime summary card — regime label, decision mode,
  risk-level coloured banner, summary, positive / risk factor lists,
  and a What happened / What it means / Watch next expander.
- Risk Firewall / guard report card — full 8-guard ladder rendered as
  a dataframe with status emoji + risk colour, plus per-guard detail
  panels for WARN/FAIL/BLOCKED rows.
- Active alerts display backed by AlertRepository.list_active() with
  severity-priority ordering preserved.
- Empty DB / missing data safe states — view model returns a setup
  hint when no account exists; cards render informative placeholders
  for missing portfolio / regime / alerts.
- System Ops page with "샘플 계좌 / 초기 스냅샷 생성" button (uses
  seed_default_account) and "Risk Guard 재실행" button (calls
  RiskGuardService.evaluate(..., persist_alerts=True)).
- DB-free view-model layer (finskillos/ui/view_models/control_room_vm.py)
  that aggregates AccountRepository + PortfolioService + GoalService +
  MarketRegimeRepository + RiskGuardService + AlertRepository into a
  single frozen dataclass tree (ControlRoomViewModel).
- Pure formatting helpers (finskillos/ui/components/formatting.py:
  format_krw, format_pct, format_ratio, risk_color, status_label,
  status_emoji) so card rendering stays deterministic and testable.
- Direct-advice safety check (assert_view_model_is_safe) reuses the
  hardened guard-safety regex (06 cleanup) over every visible string
  in the VM and is verified by tests with both forbidden wording and
  the allowed "sell-the-news" idiom.

Tests added:
- tests/test_ui_view_models.py — 7 tests covering empty DB setup
  hint, seeded account goal/portfolio summary, latest MarketRegime
  surfacing, full guard-report aggregation, severity-sorted active
  alerts, and SAFE-AC-001 enforcement on injected direct-advice text
  vs the allowed sell-the-news idiom.
- tests/test_control_room_ui.py — 20 smoke tests verifying app.py
  imports without Streamlit, every UI page / component / view-model
  module imports cleanly, NAV_ITEMS exposes the OS-style label set,
  and the formatting helpers behave on the values cards render.

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_ui_view_models.py tests/test_control_room_ui.py -q            ✅ 27 passed
- python3 -m pytest tests/test_risk_guards.py tests/test_risk_guard_service.py \
    tests/test_regime_engine.py tests/test_regime_service.py -q                              ✅ 106 passed
- python3 -m pytest tests -q                                                                  ✅ 218 passed (slice 02 + 03 + 04 + 05 + 06 + 06 cleanup + 07)
- python3 -m ruff check finskillos/ui finskillos/services \
    tests/test_ui_view_models.py tests/test_control_room_ui.py                               ✅ All checks passed

Manual smoke:
- streamlit run app.py
- Control Room renders without crash (Streamlit is a runtime-only
  dependency; tests do not require it on the path).
- Empty DB → setup-hint banner shows; "샘플 계좌 / 초기 스냅샷 생성"
  button populates account + initial 57M / 7M snapshot via the
  existing seed_default_account helper.
- After seeding, the Control Room cards render Goal / Portfolio /
  Regime (empty until RegimeService runs) / Risk Firewall / Alerts.

Notes:
- Streamlit is intentionally imported inside each render function and
  inside run_app's session_scope wrapper. Importing
  finskillos.ui.app_shell from a unit test does not pull Streamlit,
  which keeps CI environments simple.
- Pages never touch services directly. All data flows through
  ControlRoomViewModel so the UI logic stays trivially testable.
- The OS-style mockup at prototypes/ui/os_style_mockup/index.html is
  the visual reference; Slice 07 reaches feature parity for Control
  Room cards but does not chase pixel-perfect CSS parity.
- DB connection failures in the Streamlit shell render a friendly
  error banner via _NullSession instead of crashing the process.

Known issues:
- Pixel-perfect parity with the HTML prototype remains deferred.
- Full Catalyst Watch, Trade Memory, News Intelligence, and Event
  Radar remain deferred to Slices 10-12; the placeholders explain
  this in-tab.
- Live brokerage / trading execution remains out of scope.
- Streamlit must be installed at runtime to view the UI; the test
  suite does not require it.
```

```text
Post-Slice-07 Cleanup Status: DONE (2026-05-18)

Changed files:
- finskillos/ui/app_shell.py
- finskillos/ui/pages/risk_firewall.py
- finskillos/ui/pages/system_ops.py
- tests/test_control_room_ui.py
- .devmd/07_Command_Center_UI.md

Behavior change:
- Task 1 (06 safety checker verified): the hardened regex checker
  blocks "Sell TSLA now", "sell TSLA now", "BUY NVDA", "buy NVDA",
  the Korean direct-advice set (매수/매도/지금 사라/지금 팔아라/
  무조건/확실/수익 보장/원금 보장/반드시), and "guaranteed", while
  still allowing the "sell-the-news" market idiom. Coverage already
  shipped in the 06 cleanup pass and remains green.
- Task 2: Streamlit shell extracted a module-level _can_dispatch(...)
  helper and now guards _dispatch() with `if not _can_dispatch(session):
  return`. A DB connection failure renders the friendly error banner
  and stops — pages are never handed a _NullSession. Three new unit
  tests pin this contract (_NullSession is not dispatchable, real
  objects are, _NullSession still raises if a future code path ever
  forgets the check).
- Task 3: Risk Firewall page caption no longer claims WARN+ results
  auto-accumulate. New copy reads "8개 가드 결과를 한 화면에서 읽기
  전용으로 점검하세요. WARN 이상 결과는 System Ops의 'Risk Guard
  재실행'을 실행하면 alerts 테이블에 저장됩니다." A source-level
  test (test_risk_firewall_caption_does_not_claim_auto_persist)
  pins this so a regression is caught.
- Task 4: System Ops gained a third action button "Regime 재계산"
  that calls RegimeService.evaluate_today_regime(persist=True). The
  success message is built by a new pure helper
  format_regime_recalc_message() so the format stays unit-testable
  without launching Streamlit. Missing indicator data produces a
  friendly warning instead of a crash; UNKNOWN regimes surface an
  explanatory info message rather than failing silently.

Verification:
- python3 -m compileall app.py finskillos scripts                                            ✅ no errors
- python3 -m pytest tests/test_ui_view_models.py tests/test_control_room_ui.py -q            ✅ 32 passed
- python3 -m pytest tests/test_risk_guards.py tests/test_risk_guard_service.py -q            ✅ 66 passed
- python3 -m pytest tests -q                                                                  ✅ 223 passed
- python3 -m ruff check finskillos/ui finskillos/guards finskillos/services \
    tests/test_ui_view_models.py tests/test_control_room_ui.py \
    tests/test_risk_guards.py tests/test_risk_guard_service.py                               ✅ All checks passed

Known issues:
- Pixel-perfect parity with the HTML prototype remains deferred.
- Catalyst Watch, Trade Memory, News Intelligence, and Event Radar
  remain deferred to later slices.
- Live brokerage / trading execution remains out of scope.
- Streamlit must be installed at runtime to view the UI; the test
  suite does not require it.
```
