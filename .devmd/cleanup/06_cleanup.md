# 06_cleanup.md — Post-Slice-06 Safety Cleanup Before Slice 07

## Purpose

This cleanup task is a small hardening pass after `.devmd/06_Risk_Guards.md` and before the UI-oriented Slice 07 work.

Slice 06 is considered complete. Do **not** rework the Risk Guard architecture, rename guard constants, add new guard categories, rewrite alert persistence, or begin UI implementation in this cleanup.

The goal is to improve direct-advice safety checks while preserving common market terminology.

Important nuance:

- The phrase `sell-the-news` is a common market idiom.
- Do **not** remove it from `event_risk_guard.py` only because it contains the substring `sell`.
- The safety checker should distinguish between:
  - disallowed direct transaction instructions, such as `Sell TSLA now`, `BUY NVDA`, `지금 사라`, `매수하세요`
  - allowed descriptive market idioms, such as `sell-the-news risk`

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/guards/base.py
tests/test_risk_guards.py
tests/test_risk_guard_service.py
.devmd/06_Risk_Guards.md
```

Optional only if needed:

```text
finskillos/regime/regime_rules.py
```

Do **not** implement:

```text
Slice 07 UI
Risk Firewall UI
Control Room UI
New Risk Guard categories
OvertradingGuard
News Intelligence
Event Radar
Trade Journal
Brokerage integration
Direct buy/sell recommendation features
```

---

## Task 1 — Harden forbidden-wording safety without blocking market idioms

### Problem

`assert_no_forbidden_wording()` currently checks forbidden terms with simple substring matching.

This is too weak in one direction and too strict in another direction:

1. It may miss lowercase direct instructions:
   - `sell TSLA now`
   - `buy NVDA`
   - `매수하세요`

2. A naive case-insensitive check would incorrectly block common descriptive idioms:
   - `sell-the-news risk`

The cleanup should make the checker stronger against direct advice while allowing explicitly approved market idioms.

### Required behavior

Update:

```text
finskillos/guards/base.py
```

Implement helper functions similar to:

```python
_ALLOWED_MARKET_IDIOMS: Final[tuple[str, ...]] = (
    "sell-the-news",
)

def _strip_allowed_market_idioms(text: str) -> str:
    lowered = text.lower()
    for idiom in _ALLOWED_MARKET_IDIOMS:
        lowered = lowered.replace(idiom, "")
    return lowered
```

Then update `assert_no_forbidden_wording()` to:

1. collect strings from:
   - title
   - message
   - watch_next
   - string evidence values
2. strip explicitly allowed idioms
3. detect direct English/Korean instruction wording case-insensitively

The checker should catch at least:

```text
buy
sell
매수
매도
지금 사라
지금 팔아라
무조건
확실
수익 보장
guaranteed
원금 보장
반드시
```

But it should **not** fail only because the phrase contains:

```text
sell-the-news
```

### Suggested implementation

Use word-boundary checks for English `buy` and `sell`, not raw substring matching.

Example approach:

```python
import re

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
```

Before applying patterns:

```python
scan_text = _strip_allowed_market_idioms(haystack)
```

Then:

```python
for pattern in _DIRECT_ADVICE_PATTERNS:
    if pattern.search(scan_text):
        raise AssertionError(...)
```

If you prefer to reuse `FORBIDDEN_WORDS`, keep it, but do not rely on raw case-sensitive substring matching. The key requirement is behavior, not exact implementation.

### Acceptance criteria

- `assert_no_forbidden_wording()` catches lowercase and mixed-case direct instructions.
- `assert_no_forbidden_wording()` catches Korean direct instruction wording.
- `assert_no_forbidden_wording()` allows the market idiom `sell-the-news`.
- Existing guard outputs still pass safety checks.
- No guard output becomes a direct buy/sell recommendation.

---

## Task 2 — Add focused safety tests

Update:

```text
tests/test_risk_guards.py
```

Add tests similar to:

```python
import pytest

from finskillos.guards import GuardResult, assert_no_forbidden_wording


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

Add an explicit idiom allow test:

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

Also add one test that scans the actual event placeholder guard output:

```python
def test_event_placeholder_guard_sell_the_news_idiom_is_allowed() -> None:
    result = event_risk_guard.evaluate(_base_input())
    assert_no_forbidden_wording(result)
```

### Acceptance criteria

- Lowercase `sell` and `buy` direct instructions fail.
- Uppercase `SELL` and `BUY` direct instructions fail.
- Korean direct instruction wording fails.
- `sell-the-news` idiom passes.
- Existing parametric safety tests still pass.

---

## Task 3 — Ensure persistence path still enforces safety

`RiskGuardService._persist_alerts()` already calls:

```python
assert_no_forbidden_wording(result)
```

Keep this behavior.

Update or add a test in:

```text
tests/test_risk_guard_service.py
```

Only if not already covered, add a direct unit-level persistence safety test by monkeypatching a bad guard result or directly testing `assert_no_forbidden_wording()` is called before alert creation.

A lightweight option is enough:

```python
def test_persisted_alert_messages_are_checked_for_safety(...):
    ...
```

Do not over-engineer this. The most important coverage is the helper behavior in `tests/test_risk_guards.py`.

### Acceptance criteria

- Alert persistence path still calls `assert_no_forbidden_wording()`.
- No unsafe direct advice can enter `alerts.message` through `RiskGuardService`.

---

## Task 4 — Update `.devmd/06_Risk_Guards.md`

Append a short cleanup block below the existing Slice 06 completion section:

```text
Post-Slice-06 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/guards/base.py
- tests/test_risk_guards.py
- tests/test_risk_guard_service.py
- .devmd/06_Risk_Guards.md

Behavior change:
- Guard safety checker now blocks direct buy/sell wording case-insensitively.
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

---

## Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_risk_guards.py \
  tests/test_risk_guard_service.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/guards \
  finskillos/services \
  tests/test_risk_guards.py \
  tests/test_risk_guard_service.py
```

If ruff finds unrelated old issues outside Slice 06 cleanup files, do not perform broad cleanup. Keep fixes scoped.

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin Slice 07 UI work until the user explicitly asks to proceed.
