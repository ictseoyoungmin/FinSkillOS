"""HTTP transport for the Toss client — v4 Phase 13.

A transport is ``(method, url, headers, body) -> (status_code, json_dict)``.
``body`` is a raw string (form-encoded for the token call, None for GETs). The
default uses stdlib urllib; tests inject a recorded/fixture transport so no live
network is hit.
"""

from __future__ import annotations

import json
from collections.abc import Callable

TossTransport = Callable[[str, str, dict, str | None], tuple[int, dict]]


def default_transport(
    method: str, url: str, headers: dict, body: str | None
) -> tuple[int, dict]:
    import urllib.error
    import urllib.request

    data = body.encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
            return response.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:  # 4xx/5xx still carry a JSON body
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {}
        except ValueError:
            payload = {"raw": raw}
        return exc.code, payload
