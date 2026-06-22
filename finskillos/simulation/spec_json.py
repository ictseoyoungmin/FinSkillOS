"""Parse + validate a free-form StrategySpec from JSON (Phase 21.8).

The agent (or an API client) describes an arbitrary entry/exit hypothesis as a
small JSON condition tree; this module turns it into a validated
:class:`StrategySpec` the engine can run. Validation is strict — only known
features / operators / a bounded shape — so an authored spec can never reference
data the engine doesn't compute or blow up the replay.

Condition grammar (JSON):
    {"compare": [feature, op, value]}        # op: < <= > >= ==
    {"cross":   [feature, "above"|"below", reference]}
    {"all":     [cond, ...]}
    {"any":     [cond, ...]}
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from finskillos.simulation.conditions import All, Any, Compare, Condition, Cross
from finskillos.simulation.engine import StrategySpec

# Features the engine/service can supply per bar (build_features + the service's
# external indicator/regime merge). ``sma_<n>`` / ``ema_<n>`` are matched by regex.
_SCALAR_FEATURES = {"close", "ret", "drawdown_pct", "rsi_14"}
_CATEGORICAL_FEATURES = {"trend", "regime"}
_MA_RE = re.compile(r"^(?:sma|ema)_\d+$")

_COMPARE_OPS = {"<", "<=", ">", ">=", "=="}
_CROSS_DIRS = {"above", "below"}

_MAX_DEPTH = 4
_MAX_TERMS = 8


class SpecParseError(ValueError):
    """A free-form spec was malformed or referenced unknown features/operators."""


def _is_feature(name: object) -> bool:
    return isinstance(name, str) and (
        name in _SCALAR_FEATURES
        or name in _CATEGORICAL_FEATURES
        or bool(_MA_RE.match(name))
    )


def _require_feature(name: object, where: str) -> str:
    if not _is_feature(name):
        raise SpecParseError(
            f"{where}: unknown feature {name!r} "
            "(allowed: close, ret, drawdown_pct, rsi_14, trend, regime, sma_N, ema_N)"
        )
    return name  # type: ignore[return-value]


def condition_from_json(obj: object, *, depth: int = 0) -> Condition:
    if depth > _MAX_DEPTH:
        raise SpecParseError("condition nesting too deep")
    if not isinstance(obj, Mapping) or len(obj) != 1:
        raise SpecParseError(
            "each condition must be a single-key object "
            "(compare / cross / all / any)"
        )
    (kind, payload), = obj.items()

    if kind == "compare":
        if not isinstance(payload, Sequence) or len(payload) != 3:
            raise SpecParseError("compare expects [feature, op, value]")
        feature, op, value = payload
        _require_feature(feature, "compare")
        if op not in _COMPARE_OPS:
            raise SpecParseError(f"compare: bad operator {op!r}")
        if not isinstance(value, (int, float, str)) or isinstance(value, bool):
            raise SpecParseError("compare: value must be a number or string")
        if op != "==" and not isinstance(value, (int, float)):
            raise SpecParseError(f"compare: {op} needs a numeric value")
        return Compare(feature, op, value)

    if kind == "cross":
        if not isinstance(payload, Sequence) or len(payload) != 3:
            raise SpecParseError("cross expects [feature, direction, reference]")
        feature, direction, reference = payload
        _require_feature(feature, "cross")
        _require_feature(reference, "cross reference")
        if direction not in _CROSS_DIRS:
            raise SpecParseError("cross: direction must be 'above' or 'below'")
        return Cross(feature, direction, reference)

    if kind in ("all", "any"):
        if not isinstance(payload, Sequence) or not (1 <= len(payload) <= _MAX_TERMS):
            raise SpecParseError(f"{kind} expects 1..{_MAX_TERMS} sub-conditions")
        terms = tuple(condition_from_json(t, depth=depth + 1) for t in payload)
        return All(terms) if kind == "all" else Any(terms)

    raise SpecParseError(f"unknown condition kind {kind!r}")


def strategy_spec_from_json(obj: object) -> StrategySpec:
    """Validate a ``{"name", "ticker", "entry", "exit"}`` object into a spec."""

    if not isinstance(obj, Mapping):
        raise SpecParseError("strategy spec must be an object")
    ticker = obj.get("ticker")
    if not isinstance(ticker, str) or not ticker.strip():
        raise SpecParseError("strategy spec needs a 'ticker'")
    if "entry" not in obj or "exit" not in obj:
        raise SpecParseError("strategy spec needs 'entry' and 'exit' conditions")
    name = obj.get("name")
    name = name.strip() if isinstance(name, str) and name.strip() else "사용자 전략"
    return StrategySpec(
        strategy_id="CUSTOM",
        name=name[:80],
        description=str(obj.get("description") or "agent가 설계한 자유형 전략")[:280],
        universe=(ticker.strip().upper(),),
        entry=condition_from_json(obj["entry"]),
        exit=condition_from_json(obj["exit"]),
    )
