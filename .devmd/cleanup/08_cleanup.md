# 08_cleanup.md — Post-Slice-08 Scope Alignment Before Slice 09

## Purpose

This cleanup task is a small scope-alignment and copy-consistency pass after `.devmd/08_Research_Hub_Index_Lab.md` and before starting Slice 09.

Slice 08 is considered complete **as Index Lab v0**, but the original `.devmd/08` acceptance criteria are chart-heavy and broader than what was intentionally implemented. The cleanup should make that distinction explicit and remove UI copy that references actions not yet available in System Ops.

Do **not** implement the chart-heavy original acceptance items in this cleanup.

The goal is to prevent future confusion:

- Current implementation: Analysis Workspace / Index Lab v0
- Deferred future work: interactive charts, normalized overlays, indicator toggles, chart presets, lazy chart rendering, full Research Hub chart lab

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Scope

Modify only the files needed for this cleanup:

```text
.devmd/08_Research_Hub_Index_Lab.md
finskillos/ui/view_models/index_lab_vm.py
finskillos/ui/pages/analysis_workspace.py
tests/test_index_lab_view_model.py
tests/test_analysis_workspace_ui.py
```

Optional, only if necessary:

```text
finskillos/ui/pages/system_ops.py
tests/test_control_room_ui.py
```

Do **not** implement:

```text
Slice 09 Symbol Lab
interactive chart rendering
overlay / normalized comparison chart
indicator toggle UI
chart preset model/table
saved chart presets
live market-data fetching
News Intelligence
Event Radar / Catalyst Watch
Trade Memory
brokerage integration
direct buy/sell recommendation features
```

---

# Task 1 — Re-label Slice 08 completion as Index Lab v0

## Problem

`.devmd/08_Research_Hub_Index_Lab.md` originally requires:

```text
- User can select one or more indices/ETFs.
- Overlay chart normalizes selected assets to a common starting value.
- Indicators can be toggled.
- Chart presets can be saved.
- Interpretation panel updates based on selected assets/timeframe.
- Chart rendering is lazy-loaded.
```

Current Slice 08 intentionally implements:

```text
- Analysis Workspace route
- Index Lab view model
- U.S. index / ETF / macro universe table
- relative strength ranking
- strongest / weakest panels
- regime context
- missing-data safe state
- watchpoints
- safety scan
```

This is a good v0 implementation, but the completion note should not imply the entire original chart-heavy spec is done.

## Required change

Update `.devmd/08_Research_Hub_Index_Lab.md`.

Change:

```text
Status: DONE (2026-05-18)
```

to:

```text
Status: DONE_AS_INDEX_LAB_V0 (2026-05-18)
```

Add a clear scope note below the implemented list:

```text
Scope note:
- Slice 08 is complete as Analysis Workspace / Index Lab v0.
- The original chart-heavy acceptance criteria are intentionally deferred:
  - multi-select chart view
  - normalized overlay chart
  - indicator toggles
  - chart presets
  - lazy chart rendering
  - full timeframe selector
- These deferred items should be handled in a future chart-polish / Research Hub expansion slice.
- Do not treat them as already implemented.
```

Also update `Known issues` to explicitly include:

```text
- Original chart-heavy Index Lab items remain deferred and must not be assumed complete.
```

## Acceptance criteria

- `.devmd/08` clearly says Index Lab v0, not full chart lab completion.
- Deferred chart items are explicit.
- Future agents will not assume overlay charts / presets / indicator toggles already exist.

---

# Task 2 — Fix missing-data copy that references non-existent System Ops actions

## Problem

Analysis Workspace currently tells the user:

```text
System Ops에서 Market Refresh / Indicators 재계산을 실행하세요.
```

But System Ops currently has:

```text
- sample account / initial snapshot seed
- Risk Guard rerun
- Regime recalculation
```

It does **not** yet expose:

```text
Market Refresh
Indicators 재계산
```

This is the same kind of UI copy mismatch that was fixed in Slice 07 cleanup.

## Required change

Update copy in:

```text
finskillos/ui/view_models/index_lab_vm.py
finskillos/ui/pages/analysis_workspace.py
```

Replace wording that instructs the user to use unavailable System Ops actions.

Recommended wording for `setup_hint`:

```text
지수 / ETF 데이터가 비어 있습니다. market_bars / indicator_snapshots 데이터가 저장되면 이 화면에 표시됩니다. 현재 Slice 08에서는 자동 refresh를 수행하지 않습니다.
```

Recommended wording for missing-data section caption:

```text
다음 종목은 market_bars 또는 indicator_snapshots가 비어 있습니다. 현재 화면은 저장된 데이터를 읽는 전용 뷰이며, 자동 refresh는 수행하지 않습니다.
```

Do not add a fake button.  
Do not implement Market Refresh in this cleanup.

## Required tests

Update `tests/test_index_lab_view_model.py` or `tests/test_analysis_workspace_ui.py`.

Add/adjust tests to ensure the view-model setup hint does not reference unavailable actions:

```python
def test_empty_db_setup_hint_does_not_reference_missing_system_ops_actions(
    db_session: Session,
) -> None:
    vm = build_index_lab_view_model(db_session, generated_at=NOW)

    assert vm.setup_hint is not None
    assert "Market Refresh" not in vm.setup_hint
    assert "Indicators 재계산" not in vm.setup_hint
    assert "자동 refresh" in vm.setup_hint or "저장" in vm.setup_hint
```

If the missing-data caption is not extracted as a constant, add a source-level test similar to existing UI smoke tests:

```python
def test_analysis_workspace_copy_does_not_reference_missing_system_ops_actions() -> None:
    import inspect
    from finskillos.ui.pages import analysis_workspace

    source = inspect.getsource(analysis_workspace)
    assert "Market Refresh / Indicators 재계산을 실행" not in source
```

## Acceptance criteria

- Analysis Workspace no longer tells the user to click actions that do not exist.
- The page clearly states it is a read-only stored-data view.
- No automatic refresh is implied.
- Tests pin this copy consistency.

---

# Task 3 — Improve missing-data watchpoint wording

## Problem

When both `market_bars` and `indicator_snapshots` are missing, current watchpoint text says:

```text
No indicator snapshot is available yet.
```

But the data-status condition means both the market bar and the indicator snapshot are missing.

## Required change

Update:

```text
finskillos/ui/view_models/index_lab_vm.py
```

Change missing-data watchpoint to:

```text
No market bar or indicator snapshot is available yet.
```

If feasible, improve partial-data watchpoints to distinguish:

```text
- market bar exists, indicator snapshot missing
- indicator snapshot exists, market bar missing
```

This is optional; the required part is making the missing-data watchpoint accurate.

## Required tests

Update the existing missing-data watchpoint test.

Current expected text may check:

```text
no indicator snapshot
```

Change it to check:

```python
joined = " ".join(dia.watchpoints).lower()
assert "market bar" in joined
assert "indicator snapshot" in joined
```

## Acceptance criteria

- Missing-data watchpoint accurately mentions both market bar and indicator snapshot.
- Existing empty DB and missing-data tests pass.
- Safety scan still passes.

---

# Task 4 — Optional source-level guard for chart-heavy items

## Problem

The current implementation intentionally does not include chart-heavy features. Future agents may still infer from `.devmd/08` that chart functionality exists.

## Optional test

Add a source-level test to `tests/test_analysis_workspace_ui.py` or a simple doc assertion if appropriate.

Example:

```python
def test_slice_08_completion_notes_mark_chart_items_deferred() -> None:
    from pathlib import Path

    text = Path(".devmd/08_Research_Hub_Index_Lab.md").read_text(encoding="utf-8")
    assert "DONE_AS_INDEX_LAB_V0" in text
    assert "normalized overlay chart" in text
    assert "indicator toggles" in text
    assert "deferred" in text.lower()
```

This is optional but recommended.

## Acceptance criteria

- Tests make the scope boundary explicit.
- A future refactor that removes the scope note should fail a test.

---

# Task 5 — Update completion note

Append a cleanup block below the existing Slice 08 completion section in:

```text
.devmd/08_Research_Hub_Index_Lab.md
```

Use:

```text
Post-Slice-08 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- .devmd/08_Research_Hub_Index_Lab.md
- finskillos/ui/view_models/index_lab_vm.py
- finskillos/ui/pages/analysis_workspace.py
- tests/test_index_lab_view_model.py
- tests/test_analysis_workspace_ui.py

Behavior change:
- Slice 08 completion is now explicitly labeled DONE_AS_INDEX_LAB_V0.
- Original chart-heavy acceptance items are marked as deferred rather than implicitly complete.
- Analysis Workspace missing-data copy no longer references unavailable System Ops Market Refresh / Indicators recalculation actions.
- Missing-data watchpoint now accurately mentions both market_bars and indicator_snapshots.
- Index Lab remains a read-only stored-data view in this slice.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_index_lab_view_model.py tests/test_analysis_workspace_ui.py -q
- python3 -m pytest tests/test_ui_view_models.py tests/test_control_room_ui.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/ui tests/test_index_lab_view_model.py tests/test_analysis_workspace_ui.py

Known issues:
- Interactive charts, normalized overlays, timeframe selector, indicator toggles, and chart presets remain deferred.
- Symbol Lab remains deferred to Slice 09.
- News Intelligence remains deferred to Slice 10.
- Catalyst Watch / Event Radar remains deferred to Slice 11.
- Trade Memory remains deferred to Slice 12.
- Pixel-perfect parity with the HTML prototype remains deferred.
- Live brokerage / execution remains out of scope.
```

---

# Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest   tests/test_index_lab_view_model.py   tests/test_analysis_workspace_ui.py   -q

python3 -m pytest   tests/test_ui_view_models.py   tests/test_control_room_ui.py   -q

python3 -m pytest tests -q

python3 -m ruff check   finskillos/ui   tests/test_index_lab_view_model.py   tests/test_analysis_workspace_ui.py
```

Optional manual smoke:

```bash
streamlit run app.py
```

or Docker:

```bash
docker compose down -v
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
docker compose --profile app up --build
```

Then verify:

```text
- Analysis Workspace renders.
- Empty DB / missing data states are visible.
- Missing-data text does not reference unavailable System Ops actions.
- The page makes clear that it reads stored market_bars / indicator_snapshots.
- No direct buy/sell wording appears.
```

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin Slice 09 until the user explicitly asks to proceed.
