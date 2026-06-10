# v4 — Toss Securities API Integration (read-only)

The v4 arc connects FinSkillOS to a **real brokerage** — Toss Securities Open API —
for **read-only data**. It turns the manual portfolio paste (v3 Phase 11) into a
one-click sync from the user's actual account, and sources FX + market data from
Toss. **Order placement (buy/sell/modify/cancel) is intentionally excluded** — the
descriptive-only boundary holds, and the user's directive is "매수/매도 제외".

This is the concrete implementation of the `BrokerageReadAdapter` extension point
reserved in v3 Phase 12 (slice 200).

## Documents
- [`ROADMAP.md`](ROADMAP.md) — phases 13–18 + sequencing.
- [`TOSS_INTEGRATION_SPEC.md`](TOSS_INTEGRATION_SPEC.md) — auth, endpoints, the
  read-only surface we use, the excluded surface, adapter mapping, boundaries.
- `PHASE_13..18_*.md` — per-phase scope.
- `toss_finance_api_docs/` — the upstream Toss Open API reference (source of truth
  for shapes; `openapi_out_6400_line.json` is the machine spec).

## Non-negotiable boundaries (carry over from v2.1 / v3)
1. **Descriptive only.** No buy/sell advice, price predictions, guaranteed
   returns. The agent output guard is unchanged.
2. **No order placement.** The Toss client never exposes / calls
   `POST /orders`, `/orders/{id}/modify`, `/orders/{id}/cancel`. Read endpoints
   only. (Mirrors the no-execution agent tool contract.)
3. **Confirm-gated writes.** A Toss sync proposes an import the user confirms
   (reusing v3 Phase 11) — it does not silently overwrite the DB.
4. **Offline-safe tests.** The Toss client takes an injectable transport; no live
   network in the suite. Secrets live in `.env` (gitignored).
5. **Each slice = one Docker-verified commit on `main`.**
