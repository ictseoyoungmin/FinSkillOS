"""Toss read-only REST client — v4 Phase 13.

Exposes only the **read** endpoints FinSkillOS uses (accounts, holdings, FX,
market data, open orders). There is deliberately **no order-create / modify /
cancel method** — FinSkillOS never places orders (v3 Phase-12 boundary, user's
"매수/매도 제외"). Handles Bearer auth, the ``X-Tossinvest-Account`` header,
one token-reissue on 401, and one backoff on 429. Offline-safe via the injected
transport.
"""

from __future__ import annotations

import time
from urllib.parse import urlencode

from finskillos.brokerage.toss.auth import TossTokenManager
from finskillos.brokerage.toss.config import TossConfig, load_toss_config
from finskillos.brokerage.toss.transport import TossTransport, default_transport

__all__ = ["TossClient", "TossNotConfigured", "TossApiError"]


class TossNotConfigured(RuntimeError):
    """Toss credentials / account are not configured."""


class TossApiError(RuntimeError):
    def __init__(self, status: int, payload: dict) -> None:
        super().__init__(f"Toss API error {status}: {payload}")
        self.status = status
        self.payload = payload


class TossClient:
    def __init__(
        self,
        config: TossConfig | None = None,
        *,
        transport: TossTransport | None = None,
        token_manager: TossTokenManager | None = None,
        sleep=time.sleep,
    ) -> None:
        self._config = config or load_toss_config()
        self._transport = transport or default_transport
        self._tokens = token_manager or TossTokenManager(
            self._config, transport=self._transport
        )
        self._sleep = sleep

    def available(self) -> bool:
        return self._config.configured

    # --- read endpoints (no order-write methods exist) ---------------------

    def accounts(self) -> dict:
        return self._get("/api/v1/accounts")

    def holdings(self) -> dict:
        return self._get("/api/v1/holdings", account=True)

    def exchange_rate(self) -> dict:
        return self._get("/api/v1/exchange-rate")

    def stocks(self, symbols: list[str]) -> dict:
        return self._get("/api/v1/stocks", params={"symbols": ",".join(symbols)})

    def prices(self, symbols: list[str]) -> dict:
        return self._get("/api/v1/prices", params={"symbols": ",".join(symbols)})

    def candles(self, symbol: str, *, interval: str = "1d") -> dict:
        return self._get(
            "/api/v1/candles", params={"symbol": symbol, "interval": interval}
        )

    def orders(
        self,
        *,
        status: str = "OPEN",
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> dict:
        """Order-history list (read). ``status=OPEN`` returns pending orders;
        ``status=CLOSED`` returns closed/executed orders (FILLED/CANCELED/REJECTED
        with full ``execution`` detail) by ``orderedAt`` ``from``/``to`` with
        ``cursor``/``limit`` pagination. Errors (incl. the documented
        ``closed-not-supported`` code) surface as ``TossApiError`` like any 4xx.
        """
        params: dict = {"status": status}
        if symbol:
            params["symbol"] = symbol
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)
        return self._get("/api/v1/orders", params=params, account=True)

    def order(self, order_id: str) -> dict:
        """Single order detail (any status — FILLED/CANCELED/REJECTED included)."""
        return self._get(f"/api/v1/orders/{order_id}", account=True)

    # --- plumbing ----------------------------------------------------------

    def _get(self, path: str, *, params: dict | None = None, account: bool = False) -> dict:
        token = self._tokens.token()
        if token is None:
            raise TossNotConfigured("Toss client id / secret are not configured.")
        url = f"{self._config.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"

        def call() -> tuple[int, dict]:
            headers = {"Authorization": f"Bearer {self._tokens.token()}"}
            if account:
                if not self._config.account_seq:
                    raise TossNotConfigured(
                        "FINSKILLOS_TOSS_ACCOUNT_SEQ is required for this call."
                    )
                headers["X-Tossinvest-Account"] = self._config.account_seq
            return self._transport("GET", url, headers, None)

        status, data = call()
        if status == 401:  # token expired → reissue once
            self._tokens.invalidate()
            status, data = call()
        if status == 429:  # rate limited → back off once
            self._sleep(1.0)
            status, data = call()
        if status >= 400:
            raise TossApiError(status, data if isinstance(data, dict) else {})
        # Toss wraps success payloads in a `result` envelope (except OAuth).
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        return data
