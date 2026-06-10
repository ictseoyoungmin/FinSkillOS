# Phase 18 — Order / Execution Boundary (excluded) (v4)

**Goal:** make the exclusion explicit and permanent, the way v3 Phase 12 did for
the brokerage seam.

## Scope (documentation + a guard test)
- Affirm: the Toss client exposes **no** order-create/modify/cancel method;
  `POST /api/v1/orders*` is never called anywhere in the codebase. order-history
  `CLOSED` is upstream-unsupported and not used.
- A test asserts the Toss client / adapter surface has no order-write methods
  (no `place_order`/`create_order`/`modify`/`cancel`/`submit`) and that the repo
  contains no call to `/orders` POST.
- If execution is ever revisited it is a separate, conservative, paper-first,
  default-off, explicitly-authorized contract (not part of v4).

User directive: "agent를 사용하여 거래는 하지 않을 것 … 매수/매도 제외."
