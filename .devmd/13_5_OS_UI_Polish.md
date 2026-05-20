# 13.5 — OS UI Polish / Prototype Parity v0

## Goal

Lift the Streamlit app away from the default-dashboard look toward the
OS-style identity described by
`prototypes/ui/os_style_mockup/index.html`. This slice ships visual
polish only — no new feature surface, no new DB schema, no live API
dependency.

## Purpose

After Slices 02–13 the product is feature-complete at v0 but the
Streamlit shell still feels generic. The mockup defines:

```text
OS-style top tray + active-module label + status pills
Compact, themed navigation
Dark / Light / Material theme variables (cyan / amber / green / red accents)
Terminal-feel panels and badges
Scanline / noise treatment (decorative, optional)
```

We mirror those visual cues in Streamlit via a central CSS layer +
reusable component helpers, then run a light polish pass over every
main OS tab. Pixel-perfect parity with the HTML mockup is **not** a
requirement — readability + consistent identity are.

## Scope

Modify:

```text
.devmd/13_5_OS_UI_Polish.md        # this file (created in this slice)
finskillos/ui/theme.py             # central OS theme + CSS builder + header
finskillos/ui/components/os_components.py  # panel/metric/badge/empty-state helpers
finskillos/ui/app_shell.py         # apply theme, render OS header, theme selector
tests/test_os_ui_polish.py         # source-level UI polish tests
```

Optional, only if needed:

```text
finskillos/ui/pages/*.py           # light empty-state / section-header pass
finskillos/ui/components/cards.py  # cosmetic tweaks
```

Do **not** implement:

```text
.devmd/14_Deployment_Operations.md
deployment hardening, docker images, CI pipelines
brokerage / trade execution
order entry
direct buy/sell wording or buttons
new DB schema or migrations
live external API adapters
LLM-based UI copy generation
pixel-perfect HTML parity
mobile responsive layout
```

FinSkillOS remains an interpretation-first personal trading operating
system. All copy must continue to describe market state / risk
interpretation / portfolio constraints / watchpoints / reflection
support only.

## Required behaviour

1. **Central OS theme module** — `finskillos/ui/theme.py` exports:
   - `THEME_DARK`, `THEME_LIGHT`, `THEME_MATERIAL` plus an
     `ALL_THEMES: tuple[str, ...]`.
   - `THEME_TOKENS: dict[str, dict[str, str]]` — full token table per
     theme (bg / panel / border / text / muted / cyan / amber / green
     / red, plus their `--fso-*` variable names).
   - `build_os_css(theme: str) -> str` — pure function returning the
     CSS string. Importable without Streamlit (tests inspect tokens).
   - `apply_os_theme(theme: str | None = None) -> None` — injects the
     CSS via `st.markdown(..., unsafe_allow_html=True)`. Streamlit
     imported lazily inside the function.
   - `render_os_header(active_label: str | None = None) -> None` —
     OS-style top tray (product mark, active module, status pills).
   - `render_status_strip(badges: Sequence[tuple[str, str]]) -> None`
     — optional sub-header strip.
   - `render_theme_selector(default: str = THEME_DARK) -> str` — side
     control bound to `st.session_state["finskillos_theme"]`.

2. **Reusable visual components** —
   `finskillos/ui/components/os_components.py`:
   - `os_panel(title, subtitle=None, status=None) -> None`
   - `os_metric(label, value, delta=None, tone="neutral") -> None`
   - `os_badge_html(text, tone="neutral") -> str`
   - `os_section_header(title, eyebrow=None) -> None`
   - `os_empty_state(title, message) -> None`
   - Tone vocabulary: `neutral / info / success / warning / danger /
     cyan / amber / green / red / purple`.

3. **App shell** — `finskillos/ui/app_shell.py`:
   - After `set_page_config`, call `apply_os_theme()` so every page
     receives the same CSS layer.
   - Replace / extend `_render_header` with `render_os_header(active)`
     so the active OS module name is visible in the tray.
   - Add the theme selector in the sidebar above the nav radio (or
     as a sidebar `selectbox`). Persist choice via session state.
   - Preserve `_session_scope`, `_can_dispatch`, and the existing
     `_dispatch` route table. **All ten main OS routes remain wired**
     (Control Room / Market Kernel / Risk Firewall / Mission Control
     / Analysis Workspace / Symbol Lab / News Intelligence /
     Catalyst Watch → Event Radar / Trade Memory → Trade Journal /
     System Ops).
   - The disclaimer line at the sidebar bottom stays in place.

4. **Page-level polish (light touch)** — pages may optionally adopt
   `os_section_header` / `os_empty_state` for top-of-page section
   markers and empty-state copy. Do **not** rewrite any business
   logic. If a page is left untouched it still inherits the new
   theme via the global CSS layer.

5. **Safety wording**:
   - Do not put raw forbidden phrases (BUY / SELL / 매수 / 매도 / 보장
     / will rise / 오늘 팔아 / 무조건 / 반드시) into view-model
     strings or markdown that flows through `assert_no_forbidden_wording`.
   - Existing static page captions that contain `매수 / 매도` as part
     of a disclaimer ("매수 / 매도 지시가 아닌") may stay because the
     scanner does not see them (they live in the page module, not in
     view-model fields).

## Acceptance criteria

- `import finskillos.ui.theme` succeeds without importing Streamlit.
- `build_os_css(theme)` returns a string containing the core OS
  tokens for every supported theme:
  - `--fso-bg`
  - `--fso-panel`
  - `--fso-cyan`
  - `--fso-amber`
  - `--fso-red`
- `apply_os_theme` is referenced by `finskillos.ui.app_shell`.
- App shell sidebar source contains a theme selector (`selectbox`
  or `radio` against `THEME_*`).
- All main OS nav labels still resolve to real page modules; no
  main route dispatches to `deferred.*`.
- Every page module still exposes `render()` and imports without
  Streamlit at import time.
- Page source does not introduce direct-execution button captions
  (`"Buy"` / `"Sell"` / `"Execute"` / `"Trade Now"` / 지금 사라 /
  지금 팔아라 / 매수 버튼 / 매도 버튼).
- `pytest tests -q` stays green (current baseline 468 cases).
- `ruff check finskillos/ui tests/test_os_ui_polish.py` passes.

## Verification commands

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_os_ui_polish.py \
  tests/test_acceptance_fin_skill_os.py \
  tests/test_acceptance_safety_language.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/ui \
  tests/test_os_ui_polish.py
```

Optional manual smoke:

```bash
streamlit run app.py
# Dark / Light / Material 사이를 전환했을 때 색상 / 카드 / 보더가
# 즉시 바뀌어야 하고, 모든 OS 탭이 정상 동작해야 합니다.
```

## Completion placeholder

```text
Status: DONE_AS_OS_UI_POLISH_V0 (2026-05-20)

Implemented:
- Central OS theme module (finskillos/ui/theme.py).
  - Token tables for Dark OS / Light OS / Material Reference,
    mirroring the prototype variable palette (cyan / amber / green
    / red accents + bg / panel / border / text / muted layers).
  - Pure `build_os_css(theme)` builder (Streamlit-free) emitting
    `--fso-*` CSS variables plus styled blocks for `.stApp`,
    `section[data-testid="stSidebar"]`, `div[data-testid="stMetric"]`,
    `div[data-testid="stDataFrame"]`, `.stButton`, `.stExpander`,
    `.stAlert`, plus custom `.fso-tray / .fso-pill / .fso-panel /
    .fso-section-* / .fso-empty` classes.
  - `apply_os_theme()` — reads session-state, injects CSS via
    `st.markdown(unsafe_allow_html=True)`.
  - `render_os_header(active_label)` — OS-style top tray with
    product mark, active module name, READ-MODE / LOCAL-DB pills
    and UTC timestamp.
  - `render_status_strip(badges)` — optional secondary header strip.
  - `render_theme_selector(default)` — sidebar selectbox that
    persists choice on `st.session_state["finskillos_theme"]`.
  - Tone vocabulary (`neutral / info / success / warning / danger /
    cyan / amber / green / red / purple`) + `tone_to_token` mapper
    shared with os_components.
- Reusable OS component helpers
  (finskillos/ui/components/os_components.py):
  - `os_panel(title, subtitle, status, status_tone)` titled card.
  - `os_section_header(title, eyebrow)` uppercase section marker.
  - `os_empty_state(title, message)` standardised empty-state block.
  - `os_metric(label, value, delta, tone)` Streamlit-metric tile
    with tone-aware delta colouring.
  - `os_badge_html(text, tone)` + `os_badge(...)` pill helpers.
  - Streamlit imports stay lazy inside each function.
- App shell wiring (finskillos/ui/app_shell.py):
  - `apply_os_theme()` invoked after `set_page_config()`, before any
    page render — so every tab receives the same CSS layer.
  - Sidebar gains a theme `selectbox` above the nav radio; the
    Korean safety disclaimer stays in place at the sidebar bottom.
  - `render_os_header(active_label=...)` replaces the previous
    static markdown header; the active module label is shown in
    the tray.
  - `_render_sidebar()` now returns `(nav_key, active_label)`; the
    `_dispatch` table, `_session_scope`, `_can_dispatch`, and the
    Slice-07 `_NullSession` fallback are unchanged. All ten OS
    routes still resolve to real page modules.

Files changed:
- finskillos/ui/theme.py                                   (new)
- finskillos/ui/components/os_components.py                (new)
- finskillos/ui/app_shell.py                               (theme + header
                                                            + selector
                                                            wiring)
- tests/test_os_ui_polish.py                               (new, 35 cases)
- .devmd/13_5_OS_UI_Polish.md                              (this file)

Notes:
- Page modules were left functionally untouched. They inherit the
  new OS look automatically through CSS targeting Streamlit's own
  data-testid attributes (`stMetric`, `stDataFrame`, `stSidebar`,
  `stAlert`, `stExpander`). Future polish slices can layer
  `os_panel` / `os_section_header` / `os_empty_state` over
  individual pages without re-routing dispatch.
- Safety scanner contract was preserved: no forbidden phrase was
  added to view-model strings. The existing 매수 / 매도 disclaimer
  in static page captions stays because it lives in page modules
  (not in scanned view-model fields).
- Streamlit dedupes `<style id="fso-os-theme">` blocks across reruns,
  so `apply_os_theme()` is safe to call once per `run_app`.

Verification (all green on 2026-05-20):
- python3 -m compileall app.py finskillos scripts                                        ✅ no errors
- python3 -m pytest tests/test_os_ui_polish.py
                    tests/test_acceptance_fin_skill_os.py
                    tests/test_acceptance_safety_language.py -q                          ✅ 85 passed
- python3 -m pytest tests -q                                                             ✅ 503 passed
- python3 -m ruff check finskillos tests                                                 ✅ All checks passed
- python3 -m ruff check finskillos/ui tests/test_os_ui_polish.py                         ✅ All checks passed

Manual smoke (recommended):
- streamlit run app.py
  - Sidebar shows Theme selector (Dark OS / Light OS / Material Reference).
  - Switching themes immediately repaints background / cards / borders /
    accent colour. Streamlit deduplicates the injected style block by
    `id="fso-os-theme"`.
  - OS top tray shows the active module name in amber + READ-MODE pill in
    cyan + LOCAL-DB pill in muted + UTC timestamp.
  - All ten main OS tabs render (Control Room / Market Kernel / Risk
    Firewall / Mission Control / Analysis Workspace / Symbol Lab / News
    Intelligence / Catalyst Watch / Trade Memory / System Ops); no main
    tab routes to a placeholder.
  - No direct buy / sell / execute / trade-now button exists.

Known issues:
- Pixel-perfect HTML-prototype parity is intentionally out of scope —
  the CSS targets Streamlit primitives so polish stays maintainable
  rather than fragile.
- Per-page `os_panel` / `os_section_header` adoption is deferred. The
  helpers exist and tests cover them; pages can opt in incrementally.
- Light theme uses a neutral cyan-only scanline (alpha 0) so the OS
  identity stays subtle on bright backgrounds — the dark-only neon
  scanline / noise treatment from the HTML prototype is not yet ported.
- Full responsive / mobile layout remains deferred.
- Deployment / Operations remains deferred to
  `.devmd/14_Deployment_Operations.md`.
- Brokerage / execution / LLM coaching remain out of scope.
```
