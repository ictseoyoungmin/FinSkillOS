# Phase 15 — Exchange Rate via Toss (v4)

**Goal:** source USD↔KRW FX from Toss when configured (replaces/supplements the
Yahoo fetcher from slice 210).

## Scope
- A Toss `exchange-rate` fetcher plugged into `finskillos/agent/fx.py`
  `usd_krw_rate(fetcher=…)`: prefer Toss when creds are set, else Yahoo, else the
  cached/default rate. Cache + offline-safe (injected transport).

## Tests
Toss exchange-rate fixture → rate; preference order (Toss > Yahoo > default);
failure falls back. Offline.
