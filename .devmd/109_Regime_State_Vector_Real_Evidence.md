# 109 — RegimeStateVector Honest Values (real evidence)

Date: 2026-06-01

## Problem (P3b)

The Control Room "State Vector" panel (`RegimeStateVector`) fabricated its
content: `derive()` returned hard-coded `Bullish / Elevated / Compressed /
Neutral / Cluster` for fixed `Trend / RSI / Vol / Macro / Events` dimensions
regardless of the actual state — a placeholder presenting invented market
readings as evidence. (The user dislikes placeholders.)

## Implemented

Replace the fabricated vector with **real regime evidence** the API already
holds (`ControlRoomViewModel.regime` → live `MarketRegime` row).

- `api/schemas/control_room.py`: new `StateVectorCell {label, value, tone}` and
  `OperatingState.state_vector: list[StateVectorCell]` (default `[]`).
- `api/routes/control_room.py::_state_vector(regime, score)` builds cells from
  the classification: Decision Mode, Confidence (`{score}%`, tone banded
  ≥66 success / ≥40 neutral / else warning), then up to two rule-derived
  `positive_factors` (Strength, success) and two `risk_factors` (Risk Factor,
  warning). The no-regime branch leaves `state_vector=[]`.
- `api/fixtures/control_room.py`: deterministic 4-cell vector for fixture/visual.
- Frontend `features/regime/types.ts`: `StateVectorCell` + `stateVector` on
  `OperatingState`. `RegimeStateVector.tsx` renders the API cells (tone → colour)
  and shows an honest empty state when no regime is classified; the hard-coded
  `VECTOR_DEFS` / `derive()` are gone. `controlRoom.fixture.ts` updated.

## Tests

- `tests/test_api_control_room.py` (3 new): `_state_vector` maps decision mode +
  confidence + the first two positive/risk factors (3rd dropped) to real cells;
  confidence tone bands (80→success / 50→neutral / 20→warning); the fixture
  payload exposes a camelCase `stateVector` led by "Decision Mode".

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_control_room.py -q`
  ✅ (21 passed); full suite ✅; `ruff check` ✅.
- `web npm run build && npm run lint` ✅ (0 errors).
- Served bundle confirmed to carry the new component ("Regime evidence" badge).
- control-room structural test ✅ (panel still renders). The State Vector sits
  below the screenshot fold, so the visual baseline is byte-identical (regen
  produced no change).

## Known issues

- None. Descriptive only; no execution wording. The panel now states honestly
  when there is no regime to vector.
