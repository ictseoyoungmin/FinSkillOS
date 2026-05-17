# 03 — Portfolio and Goal Tracker

## Goal

Implement the portfolio state and 100,000,000 KRW goal tracking layer.

## User-specific target

```text
Current value baseline: 57,000,000 KRW
Target: 100,000,000 KRW
Remaining: 43,000,000 KRW
Progress: 57%
Early stop: enabled at target achievement
```

## Scope

- Account goal settings.
- Manual portfolio snapshot input.
- Position entry/editing.
- Goal progress calculation.
- Milestone mode calculation.
- Goal completion state.

## Milestone modes

```text
0%–50%     Growth Mode
50%–80%    Balanced Mode
80%–95%    Protection Mode
95%–100%   Completion Guard
>=100%     Challenge Complete
```

## Services

Create:

```text
finskillos/services/portfolio_service.py
finskillos/services/goal_service.py
```

## Core outputs

```json
{
  "current_value": 57000000,
  "target_value": 100000000,
  "progress_pct": 57.0,
  "remaining_value": 43000000,
  "goal_mode": "BALANCED",
  "early_stop_triggered": false
}
```

## UI page

Create a basic Goal Tracker page:

```text
finskillos/ui/pages/goal_tracker.py
```

Required sections:

- current value
- target value
- progress bar
- remaining value
- required return scenarios
- milestone journey
- early-stop explanation

## Acceptance criteria

- User can enter/update current portfolio value.
- Progress percentage is accurate.
- Goal mode changes as value crosses thresholds.
- At 100,000,000 KRW or above, status becomes `CHALLENGE_COMPLETE`.
- UI avoids direct investment instructions.

## Test cases

```text
57M / 100M => 57%, BALANCED
49M / 100M => 49%, GROWTH
85M / 100M => 85%, PROTECTION
96M / 100M => 96%, COMPLETION_GUARD
100M / 100M => 100%, CHALLENGE_COMPLETE
```

## Test commands

```bash
pytest tests/test_goal_service.py -q
```

## Completion placeholder

```text
Status: DONE (2026-05-17)

Implemented files:
- finskillos/goal/goal_tracker.py            (rewritten — OS-style phases GROWTH/BALANCED/PROTECTION/COMPLETION_GUARD/CHALLENGE_COMPLETE; thresholds 0.5/0.8/0.95/1.0; saturates progress_ratio/progress_pct at 1.0/100; returns GoalStatus with current_value/target_value/progress_ratio/progress_pct/remaining_value/goal_mode/early_stop_triggered)
- finskillos/services/portfolio_service.py   (kept load_portfolio_csv + PortfolioPositionInput, replaced legacy `symbol` shape with v2.1 `ticker`; new PortfolioService class wraps slice-02 PositionRepository + PortfolioRepository — import_snapshot upserts positions + creates a snapshot, upsert_position is idempotent on (account_id, ticker), get_portfolio_summary returns total_value/cash_value/position_count/largest weight/over_single_limit_tickers/sector_exposure, calculate_exposure returns sector-share map; SINGLE_POSITION_LIMIT_KRW = Decimal("10000000"))
- finskillos/services/goal_service.py        (new — GoalService.get_goal_status(account_id) reads Account.target_value + the latest portfolio_snapshots row via PortfolioRepository.latest, forwards to goal_tracker.calculate_goal_status; raises LookupError for unknown accounts; empty portfolio returns current=0 / GROWTH / no division-by-zero)

Test fixtures + tests added:
- tests/fixtures/portfolio/sample_portfolio_snapshot.csv     (v2.1 doc-format CSV: TSLA/NVDA/RKLB/PLTR rows with ticker/name/sector/theme/strategy_type/quantity/avg_price/market_value/pnl_pct/stop_loss/take_profit/thesis)
- tests/fixtures/portfolio/sample_positions_over_limit.csv   (TSLA market_value 11M to exercise the PORT-AC-003 single-position guard)
- tests/unit/test_goal_tracker.py            (rewritten — 9 tests: parametrized threshold table for 49M/57M/85M/96M/100M cases, remaining_value/progress_ratio at 57M, overshoot saturation at 137M, boundary checks at 0.5/0.8/0.95/1.0, invalid target rejection)
- tests/unit/test_goal_service.py            (new — 9 tests: 5 parametrized DB-backed mode cases, latest-snapshot wins, no-snapshot empty-portfolio path, GOAL-AC-002 completion + early_stop_triggered, unknown-account LookupError)
- tests/unit/test_portfolio_service.py       (new — 8 tests: import_snapshot creates rows, idempotent upserts, summary returns total + largest weight, single-position limit flag, sector exposure shares, empty-account no-divide-by-zero, sample CSV parse, legacy `symbol` column fallback)
- tests/integration/test_portfolio_import_flow.py  (new — 3 tests: full CSV→DB round trip on sample_portfolio_snapshot.csv, over-limit fixture flags TSLA, second import keeps positions deduped while appending new snapshot rows)

Screens:
- None. Per the user instruction "Do not implement Market Data, Regime Engine, Risk Guards, or UI pages yet", the Mission Control / Goal Tracker Streamlit page is intentionally deferred. PortfolioService/GoalService are UI-free so the same surface area can be reused by a later UI slice and by potential CLI/agent callers.

Notes:
- Phase-threshold table follows .devmd/03 exactly (50/80/95/100). It disagrees with docs/v2_1/09 GOAL-AC-001 only on the 57M case (doc 09 says GROWTH, .devmd/03 says BALANCED) — followed the slice doc since the slice prompt and its JSON example both place 57M in BALANCED.
- PortfolioService.import_snapshot does *not* delete positions for tickers missing from the new CSV. Live positions are owned by the user; removals should go through a future explicit "close" flow (slice 06 / Trade Memory).
- PortfolioSummary.over_single_limit_tickers is informational only — it does NOT generate buy/sell text. Slice 06 (Risk Firewall) will turn this signal into alerts.
- The slice-02 PortfolioRepository.list_for_account already orders by snapshot_date — GoalService.latest relies on that ordering.

Verification:
- python3 -m compileall app.py finskillos scripts                                  ✅ no errors
- python3 -m pytest tests -q                                                        ✅ 58 passed (29 prior + 9 goal_tracker + 9 goal_service + 8 portfolio_service + 3 portfolio import flow)
- python3 -m ruff check  (every slice-03 file)                                      ✅ All checks passed

Known issues:
- Streamlit Goal Tracker page (finskillos/ui/pages/goal_tracker.py) intentionally not yet implemented per the user prompt; will land alongside the slice that wires Control Room / Mission Control UIs.
- Cash bucket accuracy depends on the user passing `cash_value` to import_snapshot — when omitted it defaults to 0. A later slice may compute cash from a "Cash" sentinel ticker row instead.
- The legacy v1 helpers `PortfolioPositionInput.symbol` / `PortfolioSummary.largest_position_symbol` were renamed to ticker-based names; no external callers existed (only the service's own tests), so nothing else needed updating.
- Repository-wide ruff baseline noted in cleanup/00_cleanup.md is still pending; slice-03 files are ruff-clean.
```
