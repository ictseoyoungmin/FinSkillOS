"""Toss OAuth2 token manager — v4 Phase 13.

Client-credentials grant. Caches the token + expiry, reissues ~30s before expiry
or on demand (the client invalidates on a 401). One valid token per client. No
refresh token — reissue at the same endpoint. Offline-safe via an injectable
transport.
"""

from __future__ import annotations

import time
from urllib.parse import urlencode

from finskillos.brokerage.toss.config import TossConfig
from finskillos.brokerage.toss.transport import TossTransport, default_transport

_EXPIRY_SKEW_SECONDS = 30


class TossTokenManager:
    def __init__(
        self,
        config: TossConfig,
        *,
        transport: TossTransport | None = None,
        clock=time.time,
    ) -> None:
        self._config = config
        self._transport = transport or default_transport
        self._clock = clock
        self._token: str | None = None
        self._expires_at: float = 0.0

    def token(self) -> str | None:
        """A valid access token, issuing/reissuing as needed; None if unconfigured."""

        if not self._config.configured:
            return None
        if self._token and self._clock() < self._expires_at - _EXPIRY_SKEW_SECONDS:
            return self._token
        return self._issue()

    def invalidate(self) -> None:
        self._token = None
        self._expires_at = 0.0

    def _issue(self) -> str | None:
        body = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self._config.client_id or "",
                "client_secret": self._config.client_secret or "",
            }
        )
        status, data = self._transport(
            "POST",
            f"{self._config.base_url}/oauth2/token",
            {"Content-Type": "application/x-www-form-urlencoded"},
            body,
        )
        token = data.get("access_token") if isinstance(data, dict) else None
        if status == 200 and token:
            self._token = token
            self._expires_at = self._clock() + int(data.get("expires_in", 0) or 0)
            return token
        self.invalidate()
        return None
