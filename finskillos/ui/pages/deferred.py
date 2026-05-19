"""Placeholder pages for tabs scheduled in later slices.

History note (no live placeholders remain):

* Analysis Workspace placeholder was removed in Slice 08
  (wired to ``finskillos.ui.pages.analysis_workspace``).
* Symbol Lab placeholder was removed in Slice 09.
* News Intelligence placeholder was removed in Slice 10.
* Catalyst Watch placeholder was removed in Slice 11
  (wired to ``finskillos.ui.pages.event_radar``).
* Trade Memory placeholder was removed in Slice 12
  (wired to ``finskillos.ui.pages.trade_journal``).

The module is intentionally kept so existing imports (and the
``render_*`` smoke tests) keep working — once a future slice
introduces a brand-new deferred tab it can add a stub here without
re-creating the file.
"""

from __future__ import annotations
