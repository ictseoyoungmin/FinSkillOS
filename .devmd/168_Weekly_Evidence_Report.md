# 168 — Weekly Evidence Report (Phase 4)

**Status:** Done. Read-only. **Closes Phase 4 (interpretation engine).**

The capstone: one descriptive markdown report assembling the cross-tab evidence
for the week — market regime, portfolio state, upcoming catalysts, and the
trade-process review (the Slice-161 weekly review). Pure aggregation of the live
read models; the assembled text is re-scanned with the Slice-06 forbidden-wording
guard before it leaves the seam.

## Implemented

### API
- `api/weekly_report.py` — `build_weekly_evidence_markdown(session, today)`
  assembles four sections from the existing services:
  - **Market Regime** — `MarketRegimeRepository.latest` (regime, confidence,
    top supporting/risk factor).
  - **Portfolio** — `PortfolioService.get_portfolio_summary` (total, cash %,
    largest position, over single-position-limit tickers).
  - **Upcoming Catalysts** — `build_event_radar_view_model` (high-risk +
    holdings-linked counts, top high-risk events).
  - **Trade Process Review** — `ReflectionService.weekly_review` +
    `render_weekly_review_markdown`.
  No account → an explicit "seed an account" placeholder. Runs
  `assert_no_forbidden_wording` on the full report.
- `GET /api/trade-memory/weekly-evidence-report?as_of=` →
  `WeeklyEvidenceReport {generatedAt, markdown, source}`. Fixture / offline /
  live-error return explicit descriptive placeholders (never substituted fixture
  content in live-error).

### Frontend
- `WeeklyEvidenceReportPanel` on Trade Memory (live only): "Build report" loads
  the markdown on demand, with Copy + Download .md. Live-gated → fixture render
  unchanged, Trade Memory visual baseline intact.

## Tests (`tests/test_api_trade_memory.py`, +2)
- fixture mode returns a `# Weekly Evidence Report` placeholder;
- live mode (account + imported trades) assembles all four section headings and
  contains no forbidden execution wording.

## Verification
- Offline: trade-memory + v42 + safety-language pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt images): api pytest + ruff + web build.

## Notes
- No migration. Aggregates existing services; live-gated UI → no Playwright regen.
- **Phase 4 complete (163–168):** risk-guard attribution · regime explanation v2 ·
  event/news/position linkage · portfolio constraint summary v2 · cross-tab
  evidence graph · weekly evidence report. Next per ROADMAP: Phase 5 (packaging).
