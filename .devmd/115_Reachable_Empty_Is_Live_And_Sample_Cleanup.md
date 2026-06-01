# 115 — Reachable-Empty → Live(-empty), Sample Data Cleanup

Date: 2026-06-01

## Goal

Resolve the "fixture-state data shows as analysis" confusion: no tab should
present the fixture sample as real when the DB is reachable, and the dashboard
should show MISSING where there is no **real** data.

## Audit result (code already compliant)

Every product route already follows the state contract: `X-FSO-Use-Fixture`
header → fixture (opt-in); `session is None` → `mark_db_unavailable(...)` (the
db-unavailable banner); reachable session → live / live-empty / live-error.
**No route substitutes fixture content on a reachable session.** Locked with a
regression guard:

- `tests/test_reachable_empty_is_live.py` — parametrized over all 9 tabs
  (control-room, market-kernel, analysis-workspace, symbol-lab, mission-control,
  risk-firewall, news-intelligence, event-radar, trade-memory): a reachable but
  **empty** sqlite DB returns `source="live"` and a non-fixture `generatedAt`,
  never the deterministic fixture sample.

## Data cleanup (authorized)

The real "fixture confusion" was **seeded sample rows** in the live DB (real
rows, source=live, but demo data) being analyzed. With the market/news data now
real (worker), the sample portfolio + events were removed so the dashboard shows
MISSING until real portfolio/events exist:

- Deleted: 1 sample account ("Main Trading Account"), 5 "Seeded sample" positions,
  1 portfolio snapshot, 14 demo trades, 15 alerts, 12 `manual_seed` /
  `calendar_mock` events, 13 event links.
- Kept (real): 16 087 market bars, 16 054 indicator snapshots, 608 news articles.

Result (live re-check): control-room `mission=MISSING`, event-radar `0`
catalysts, while market-kernel NVDA = 255 real bars (211.14) and news-intel is
live. The sample data is re-creatable any time via the System Ops
`seed-sample-account` / `seed-sample-events` protocols.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed (incl. the
  new 9-tab guard).
- Live `/api/*` re-checked: real market/news, MISSING mission/catalyst.

## Known issues

- None. Completes the P0 arc (111–115). Spec updated in
  `docs/WORKER_QUEUE_AND_API_SPEC.md`.
