"""Toss order/execution boundary — v4 Phase 18.

Affirms the permanent exclusion: the Toss integration is read-only and contains no
order-placement surface. FinSkillOS never places, modifies, or cancels an order.
"""

from __future__ import annotations

import pathlib

from finskillos.brokerage.toss.adapter import TossBrokerageAdapter
from finskillos.brokerage.toss.client import TossClient
from finskillos.brokerage.toss.config import TossConfig

_TOSS_PKG = pathlib.Path(__file__).resolve().parents[1] / "finskillos" / "brokerage" / "toss"
_FORBIDDEN_METHODS = (
    "create_order", "place_order", "submit_order", "modify_order",
    "cancel_order", "buy", "sell", "execute", "place", "submit",
)


def _cfg() -> TossConfig:
    return TossConfig("c", "s", "1", "https://x")


def test_client_and_adapter_have_no_order_write_methods() -> None:
    for obj in (TossClient(_cfg()), TossBrokerageAdapter(TossClient(_cfg()))):
        for method in _FORBIDDEN_METHODS:
            assert not hasattr(obj, method), method


def test_api_client_issues_only_reads() -> None:
    # The REST client (client.py) makes only GET requests — the single POST in the
    # integration is the OAuth token call (auth.py), never an order.
    src = (_TOSS_PKG / "client.py").read_text()
    assert '"POST"' not in src


def test_toss_source_has_no_order_mutation_endpoints() -> None:
    text = "".join(p.read_text() for p in _TOSS_PKG.glob("*.py"))
    for fragment in ("/cancel", "/modify", "createOrder", "OrderCreateRequest"):
        assert fragment not in text, fragment
