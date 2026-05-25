# Context Index

Use this index before implementing each slice.

DB foundation:

- `03_DB_Data_Model.md`
- `08_API_Data_Source_Design.md`

UI implementation:

- `05_UI_UX_Design.md`
- `07_UI_Prototype_And_Agent_Implementation_Guide.md`
- `prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html`
  - Latest static UI reference for the v4.2 Evidence-to-Judgment hierarchy.
- `frontend/src/`
  - Current product UI implementation: Vite React cockpit with 10 routed tabs.
- `frontend/e2e/visual/README.md`
  - Current visual QA source of truth: all-tabs screenshots, structural assertions,
    responsive smoke, and Docker-based baseline regeneration.
- `prototypes/ui/os_style_mockup/index.html`
  - Historical v3.3 OS-style mockup. Use only for design archaeology, not as the
    current implementation target.

Regime and Risk Guard:

- `06_Regime_RiskGuard_Rulebook.md`
- `09_Test_Acceptance_Criteria.md`

Deployment and operations:

- `10_Deployment_Operations.md`
- `11_Scheduler_Refresh_Policy.md`
  - Current manual-first, cron-compatible refresh policy for market bars,
    indicators, regime scans, risk guards, news/events, and visual QA.
- `12_Live_Adapter_Boundary.md`
  - Current fixture/live promotion boundary for v4.2 endpoints.
- `.devmd/14_Deployment_Operations.md`
  - Current deployment slice target. Treat this as the live operations workplan
    before editing the older design document.
- `.devmd/CURRENT_STATE.md`
  - Current architecture, validation baseline, and next useful slices.

Product and roadmap orientation:

- `01_Product_Plan.md`
- `02_System_Design.md`
- `04_Development_Roadmap.md`
