# 07_cleanup.md — Post-Slice-07 Quality Gate Before Slice 08

## Purpose

This cleanup task is a quality gate after `.devmd/07_Command_Center_UI.md` and before starting Slice 08.

Slice 07 is considered structurally complete, but this cleanup must resolve several consistency and safety issues found during code review:

1. Post-Slice-06 direct-advice safety hardening appears incomplete or inconsistent.
2. The Streamlit DB-connection fallback may still render pages with a `_NullSession`.
3. Risk Firewall UI text says alerts are automatically accumulated, while the page currently uses `persist_alerts=False`.
4. Market Kernel empty-state text references a `Regime 재계산` action that is not currently implemented in System Ops.

Do **not** rework the overall UI architecture. Do **not** begin Slice 08.

The goal is to make Slice 07 truly passable as the first usable Control Room UI.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/guards/base.py
tests/test_risk_guards.py
tests/test_risk_guard_service.py
finskillos/ui/app_shell.py
finskillos/ui/pages/risk_firewall.py
finskillos/ui/pages/system_ops.py
finskillos/ui/components/cards.py
tests/test_control_room_ui.py
tests/test_ui_view_models.py
.devmd/06_Risk_Guards.md
.devmd/07_Command_Center_UI.md
```

Optional, only if needed:

```text
finskillos/services/regime_service.py
finskillos/db/repositories/indicator_repo.py
finskillos/db/repositories/market_repo.py
```

Do **not** implement:

```text
Slice 08 Research Hub / Index Lab
News Intelligence
Event Radar / Catalyst Watch
Trade Memory
Brokerage integration
Direct buy/sell recommendation features
Pixel-perfect HTML mockup reproduction
```

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

# Task 1 — Complete / verify 06 cleanup safety checker

## Problem

Review found a likely mismatch:

- `tests/test_ui_view_models.py` expects `"Sell TSLA now"` to be blocked.
- Current safety checker may still use case-sensitive substring matching, which would miss `"Sell"` and `"sell"`.
- `sell-the-news` should remain allowed as a descriptive market idiom.

## Required change

Update:

```text
finskillos/guards/base.py
```

Implement a safety checker that:

1. Blocks direct advice case-insensitively:
   - `BUY`
   - `buy`
   - `Buy`
   - `SELL`
   - `sell`
   - `Sell`
2. Blocks Korean direct-advice wording:
   - `매수`
   - `매도`
   - `지금 사라`
   - `지금 팔아라`
   - `무조건`
   - `확실`
   - `수익 보장`
   - `원금 보장`
   - `반드시`
3. Allows the market idiom:
   - `sell-the-news`

Suggested implementation:

```python
import re
from typing import Final

_ALLOWED_MARKET_IDIOMS: Final[tuple[str, ...]] = (
    "sell-the-news",
)

_DIRECT_ADVICE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"매수"),
    re.compile(r"매도"),
    re.compile(r"지금\s*사라"),
    re.compile(r"지금\s*팔아라"),
    re.compile(r"무조건"),
    re.compile(r"확실"),
    re.compile(r"수익\s*보장"),
    re.compile(r"guaranteed", re.IGNORECASE),
    re.compile(r"원금\s*보장"),
    re.compile(r"반드시"),
)


def _strip_allowed_market_idioms(text: str) -> str:
    scan = text
    for idiom in _ALLOWED_MARKET_IDIOMS:
        scan = re.sub(re.escape(idiom), "", scan, flags=re.IGNORECASE)
    return scan
```

Then `assert_no_forbidden_wording()` should:

- collect visible strings from:
  - `GuardResult.title`
  - `GuardResult.message`
  - `GuardResult.watch_next`
  - string values in `GuardResult.evidence`
- strip allowed idioms
- apply `_DIRECT_ADVICE_PATTERNS`
- raise `AssertionError` on direct-advice wording

Do not use raw case-sensitive substring matching as the only safety mechanism.

## Required tests

Update:

```text
tests/test_risk_guards.py
```

Add or verify tests:

```python
@pytest.mark.parametrize(
    "message",
    [
        "Sell TSLA now.",
        "sell TSLA now.",
        "BUY NVDA.",
        "buy NVDA.",
        "지금 사라.",
        "지금 팔아라.",
        "이 종목은 무조건 수익 보장입니다.",
        "원금 보장입니다.",
        "This is guaranteed profit.",
        "반드시 진입하세요.",
    ],
)
def test_forbidden_wording_check_blocks_direct_advice_case_insensitively(
    message: str,
) -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status="WARN",
        risk_level="YELLOW",
        title="Safety check",
        message=message,
    )

    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(result)
```

Add or verify:

```python
def test_forbidden_wording_check_allows_sell_the_news_idiom() -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status="INFO",
        risk_level="GREEN",
        title="Event reaction risk",
        message="The system will track sell-the-news risk once event data is connected.",
    )

    assert_no_forbidden_wording(result)
```

Also verify the UI safety test remains meaningful:

```text
tests/test_ui_view_models.py::test_view_model_safety_check_blocks_injected_direct_advice
```

## Acceptance criteria

- `Sell TSLA now` fails.
- `sell TSLA now` fails.
- `BUY NVDA` fails.
- `buy NVDA` fails.
- Korean direct-advice wording fails.
- `sell-the-news risk` passes.
- Existing guard outputs pass safety checks.
- UI view-model safety tests pass.

---

# Task 2 — Prevent DB fallback from rendering pages with `_NullSession`

## Problem

`finskillos/ui/app_shell.py` currently catches DB/session startup errors and yields `_NullSession`, but page renderers may still call repositories/services with that null object. This can produce a second crash after the friendly Streamlit error banner.

## Required change

Update:

```text
finskillos/ui/app_shell.py
```

The shell should show the DB error and stop dispatching page renderers if a real DB session is unavailable.

Acceptable implementation:

```python
with _session_scope() as session:
    if isinstance(session, _NullSession):
        return
    _dispatch(nav_key, session)
```

Or change `_session_scope()` to yield `None` and check:

```python
with _session_scope() as session:
    if session is None:
        return
    _dispatch(nav_key, session)
```

Keep the friendly error banner.

## Required tests

Update:

```text
tests/test_control_room_ui.py
```

Add a lightweight import/behavior test for the fallback decision. Since this is Streamlit-adjacent, do not over-engineer browser tests.

Possible approaches:

1. Test `_NullSession` exists and `run_app` keeps imports lazy.
2. If practical, extract a helper:

```python
def _can_dispatch(session: object) -> bool:
    return not isinstance(session, _NullSession)
```

Then test:

```python
def test_null_session_is_not_dispatchable() -> None:
    from finskillos.ui.app_shell import _NullSession, _can_dispatch
    assert not _can_dispatch(_NullSession())
```

## Acceptance criteria

- DB connection failure renders an error banner but does not proceed into page renderers.
- Import tests still do not require Streamlit.
- No UI page is called with `_NullSession`.

---

# Task 3 — Fix Risk Firewall alert persistence wording / behavior mismatch

## Problem

`Risk Firewall` page currently says WARN+ results are automatically accumulated in `alerts`, but it builds the view model with `persist_alerts=False`.

This creates a user-facing mismatch.

## Required change

Choose one of the following options.

### Option A — Text-only fix, safest

Update:

```text
finskillos/ui/pages/risk_firewall.py
```

Change caption from something like:

```text
WARN 이상 결과는 자동으로 alerts 테이블에 누적됩니다.
```

to:

```text
WARN 이상 결과는 System Ops의 "Risk Guard 재실행"을 실행하면 alerts 테이블에 저장됩니다.
현재 화면은 읽기 전용 점검 결과입니다.
```

### Option B — Add a page-local Run Risk Check button

Add a button in `Risk Firewall` page:

```text
Run risk check / Risk Guard 재실행
```

When clicked:

- call `RiskGuardService.evaluate(..., persist_alerts=True)`
- commit session
- re-render or show success message
- keep default page render read-only

This requires carefully resolving the current account from the view model.

For this cleanup, **Option A is preferred** unless implementation is already trivial.

## Required tests

Update:

```text
tests/test_control_room_ui.py
```

Add a simple source/import smoke test if appropriate, or a constant-level test if you extract the caption.

Do not add browser tests.

## Acceptance criteria

- The UI no longer claims alerts are automatically accumulated on read-only render.
- System Ops remains the source of explicit alert persistence unless Option B is implemented.
- No hidden DB write occurs during normal Risk Firewall page render.

---

# Task 4 — Resolve Market Kernel “Regime 재계산” mismatch

## Problem

Regime empty-state text tells the user to use a `Regime 재계산` action in System Ops, but System Ops currently only has:

- sample account / initial snapshot seed
- Risk Guard rerun

There is no visible Regime recalculation button.

## Required change

Choose one of the following.

### Option A — Add Regime recalculation action to System Ops

Update:

```text
finskillos/ui/pages/system_ops.py
```

Add a button:

```text
Regime 재계산
```

Behavior:

1. Use `RegimeService(session).evaluate_and_record(...)` or the equivalent existing method.
2. Commit session.
3. Show success message with regime, confidence, decision_mode.
4. If required market indicator data is missing, show a friendly warning rather than crashing.

Use the exact existing `RegimeService` public API. Do not invent a new market-data pipeline in this cleanup.

If the existing service only evaluates from available latest indicators and returns `UNKNOWN`, that is acceptable.

### Option B — Text-only fix

Update:

```text
finskillos/ui/components/cards.py
finskillos/ui/pages/market_kernel.py
```

Change text to avoid referencing a non-existent button:

```text
아직 평가된 regime이 없습니다. Slice 05 RegimeService를 실행해 market_regimes가 생성되면 이 카드에 표시됩니다.
```

For Slice 07 experience, **Option A is preferred** if existing `RegimeService` has a suitable method.  
If not, use Option B and defer the action button.

## Required tests

If Option A is implemented, update tests to import `system_ops.py` and, if practical, test a small helper that formats success/error messages.

If Option B is used, no extra test beyond import smoke is required.

## Acceptance criteria

- No UI text references a missing `Regime 재계산` action.
- Either the button exists and works safely, or the copy is corrected.
- Missing market data does not crash the UI.

---

# Task 5 — Update completion notes

## Required update in `.devmd/06_Risk_Guards.md`

Append or verify a post-cleanup block:

```text
Post-Slice-06 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/guards/base.py
- tests/test_risk_guards.py
- tests/test_risk_guard_service.py
- .devmd/06_Risk_Guards.md

Behavior change:
- Guard safety checker blocks direct buy/sell wording case-insensitively.
- Korean direct-advice wording is explicitly blocked.
- The common market idiom "sell-the-news" remains allowed as descriptive market terminology.
- Alert persistence continues to run the safety checker before creating/updating alerts.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_risk_guards.py tests/test_risk_guard_service.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/guards finskillos/services tests/test_risk_guards.py tests/test_risk_guard_service.py

Known issues:
- Risk Firewall UI remains deferred.
- OvertradingGuard remains deferred until Trade Journal exposes frequency/recent-loss signals.
```

## Required update in `.devmd/07_Command_Center_UI.md`

Append a post-cleanup block:

```text
Post-Slice-07 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/ui/app_shell.py
- finskillos/ui/pages/risk_firewall.py
- finskillos/ui/pages/system_ops.py
- finskillos/ui/components/cards.py
- tests/test_control_room_ui.py
- tests/test_ui_view_models.py
- .devmd/07_Command_Center_UI.md

Behavior change:
- Streamlit shell no longer dispatches pages after DB session startup failure.
- Risk Firewall copy no longer implies alerts are written during read-only render.
- Market Kernel empty-state text no longer references a missing action, or System Ops now exposes a safe Regime recalculation action.
- UI safety tests rely on the hardened case-insensitive direct-advice checker.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_ui_view_models.py tests/test_control_room_ui.py -q
- python3 -m pytest tests/test_risk_guards.py tests/test_risk_guard_service.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/ui finskillos/guards finskillos/services tests/test_ui_view_models.py tests/test_control_room_ui.py tests/test_risk_guards.py tests/test_risk_guard_service.py

Known issues:
- Pixel-perfect parity with the HTML prototype remains deferred.
- Catalyst Watch, Trade Memory, News Intelligence, and Event Radar remain deferred.
- Live brokerage / trading execution remains out of scope.
```

---

# Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_ui_view_models.py \
  tests/test_control_room_ui.py \
  tests/test_risk_guards.py \
  tests/test_risk_guard_service.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/ui \
  finskillos/guards \
  finskillos/services \
  tests/test_ui_view_models.py \
  tests/test_control_room_ui.py \
  tests/test_risk_guards.py \
  tests/test_risk_guard_service.py
```

Optional manual smoke:

```bash
streamlit run app.py
```

Then verify:

```text
- Empty DB shows setup hint and does not crash.
- Bad DATABASE_URL shows friendly error and does not render a page with `_NullSession`.
- Control Room renders with sample account.
- Risk Firewall copy matches actual alert persistence behavior.
- Market Kernel empty state does not reference a missing button.
- Direct-advice wording is blocked in tests.
- sell-the-news idiom remains allowed.
```

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin Slice 08 until the user explicitly asks to proceed.
