"""Event calendar adapter — Slice 93.

Mirrors the ``BaseNewsAdapter`` / ``BaseMarketDataAdapter`` provider boundary.
A concrete calendar provider returns a sequence of ``SeededEvent`` (event +
links); ``EventService.refresh_events`` ingests them idempotently. This
decouples Catalyst Watch ingestion from the hard-coded Slice-11 seed catalog so
a real external calendar provider can replace the offline mock without touching
the read models (event radar, event-risk guard).

The offline-safe ``MockEventCalendarAdapter`` emits a deterministic, rolling
earnings + macro window. Like the seed catalog it uses only uncertain date
statuses (WINDOW / TENTATIVE) — never CONFIRMED — so no uncertain future date is
stored as a fact.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from finskillos.db.models.event import (
    DATE_STATUS_TENTATIVE,
    DATE_STATUS_WINDOW,
    EVENT_TYPE_CENTRAL_BANK,
    EVENT_TYPE_EARNINGS,
    EVENT_TYPE_INFLATION,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    SeededEvent,
)

_CALENDAR_MOCK_SOURCE = "calendar_mock"
_CALENDAR_CSV_SOURCE = "calendar_csv"
_CALENDAR_HTTP_SOURCE = "calendar_http"


class EventCalendarFetchError(RuntimeError):
    """Raised when an event calendar adapter cannot fetch or parse data."""


@runtime_checkable
class BaseEventCalendarAdapter(Protocol):
    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]: ...


class MockEventCalendarAdapter:
    """Deterministic, offline event calendar provider."""

    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]:
        return (
            SeededEvent(
                event=EventInput(
                    title="NVDA quarterly earnings window",
                    event_type=EVENT_TYPE_EARNINGS,
                    date_status=DATE_STATUS_TENTATIVE,
                    start_date=today + timedelta(days=6),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Tentative earnings date from the offline calendar mock."
                    ),
                    importance_score=Decimal("3.0"),
                ),
                links=(EventLinkInput(ticker="NVDA", theme="AI"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="AAPL quarterly earnings window",
                    event_type=EVENT_TYPE_EARNINGS,
                    date_status=DATE_STATUS_TENTATIVE,
                    start_date=today + timedelta(days=13),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Tentative earnings date from the offline calendar mock."
                    ),
                    importance_score=Decimal("2.5"),
                ),
                links=(EventLinkInput(ticker="AAPL", theme="Mega Cap Tech"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="CPI inflation print window",
                    event_type=EVENT_TYPE_INFLATION,
                    date_status=DATE_STATUS_WINDOW,
                    start_date=today + timedelta(days=9),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Scheduled inflation print from the offline calendar mock."
                    ),
                    importance_score=Decimal("3.5"),
                ),
                links=(EventLinkInput(event_key="CPI"),),
            ),
            SeededEvent(
                event=EventInput(
                    title="FOMC rate decision window",
                    event_type=EVENT_TYPE_CENTRAL_BANK,
                    date_status=DATE_STATUS_WINDOW,
                    start_date=today + timedelta(days=20),
                    source=_CALENDAR_MOCK_SOURCE,
                    description=(
                        "Scheduled policy window from the offline calendar mock."
                    ),
                    importance_score=Decimal("4.0"),
                ),
                links=(EventLinkInput(event_key="FOMC"),),
            ),
        )


class CsvEventCalendarAdapter:
    """Read a curated event calendar from an operator-supplied CSV file.

    Offline-safe, no network. Columns (header row required):
    ``title,event_type,date_status,start_date`` plus optional
    ``end_date,source,importance_score,ticker,sector,theme,event_key``.
    Dates are ISO ``YYYY-MM-DD``. One link per row (the ticker / sector / theme /
    event_key columns, when any are present). A missing file raises
    ``EventCalendarFetchError``; row values are validated downstream by
    ``EventService.create_event``.
    """

    source_name = _CALENDAR_CSV_SOURCE

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]:
        # Calendar rows carry absolute dates; ``today`` is part of the protocol
        # but unused here (the read model filters upcoming events).
        del today
        if not self.path.exists():
            raise EventCalendarFetchError(
                f"event calendar CSV not found: {self.path}"
            )
        items: list[SeededEvent] = []
        with self.path.open(newline="", encoding="utf-8") as fh:
            for raw in csv.DictReader(fh):
                title = (raw.get("title") or "").strip()
                if not title:
                    continue
                end_raw = (raw.get("end_date") or "").strip()
                importance_raw = (raw.get("importance_score") or "").strip()
                source = (raw.get("source") or "").strip() or self.source_name
                event = EventInput(
                    title=title,
                    event_type=(raw.get("event_type") or "").strip(),
                    date_status=(raw.get("date_status") or "").strip(),
                    start_date=date.fromisoformat(
                        (raw.get("start_date") or "").strip()
                    ),
                    end_date=date.fromisoformat(end_raw) if end_raw else None,
                    source=source,
                    importance_score=(
                        Decimal(importance_raw)
                        if importance_raw
                        else Decimal("1.0")
                    ),
                )
                items.append(SeededEvent(event=event, links=_links_from_row(raw)))
        return items


class HttpEventCalendarAdapter:
    """Fetch a vendor event calendar over HTTP and map it to ``SeededEvent``.

    Vendor-agnostic JSON contract. The endpoint returns either a JSON array of
    event objects or an object with an ``"events"`` array. Each object:

    ``{"title", "event_type", "date_status", "start_date" (ISO),
       "end_date"?, "source"?, "source_url"?, "description"?,
       "importance_score"?, "links": [{"ticker"?, "sector"?, "theme"?,
       "event_key"?}, ...]}``

    Top-level ``ticker`` / ``sector`` / ``theme`` / ``event_key`` are accepted as
    a single link when no ``links`` array is present. ``event_type`` and
    ``date_status`` are validated downstream by ``EventService.create_event``
    (so a vendor ``CONFIRMED`` row must cite its non-seed ``source``). Network /
    decode / shape problems raise ``EventCalendarFetchError`` so a refresh fails
    loudly rather than silently ingesting junk.

    Offline-safe by injection: pass ``transport=callable(url) -> str`` (the raw
    response body) in tests; the default transport lazily uses ``httpx`` and is
    never exercised offline.
    """

    source_name = _CALENDAR_HTTP_SOURCE

    def __init__(
        self,
        *,
        url: str,
        transport: Callable[[str], str] | None = None,
        timeout: float = 10.0,
        default_importance: Decimal = Decimal("2.0"),
    ) -> None:
        if not url:
            raise EventCalendarFetchError(
                "HTTP event calendar adapter requires a URL"
            )
        self.url = url
        self._transport = transport
        self.timeout = timeout
        self.default_importance = default_importance

    def fetch_events(self, *, today: date) -> Sequence[SeededEvent]:
        # Vendor rows carry absolute dates; ``today`` is part of the protocol
        # but unused here (the read model filters upcoming events).
        del today
        raw = self._fetch_raw()
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise EventCalendarFetchError(
                f"event calendar response was not valid JSON: {exc}"
            ) from exc
        if isinstance(payload, dict):
            records = payload.get("events", [])
        else:
            records = payload
        if not isinstance(records, list):
            raise EventCalendarFetchError(
                "event calendar JSON must be a list or an object with an "
                "'events' list"
            )
        items: list[SeededEvent] = []
        for record in records:
            seeded = self._parse_record(record)
            if seeded is not None:
                items.append(seeded)
        return items

    def _fetch_raw(self) -> str:
        if self._transport is not None:
            return self._transport(self.url)
        return self._http_get(self.url)

    def _http_get(self, url: str) -> str:  # pragma: no cover - network path
        try:
            import httpx
        except ImportError as exc:
            raise EventCalendarFetchError(
                "httpx is required for the HTTP event calendar adapter"
            ) from exc
        try:
            response = httpx.get(
                url, timeout=self.timeout, headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as exc:
            raise EventCalendarFetchError(
                f"event calendar request failed: {exc}"
            ) from exc

    def _parse_record(self, raw: Any) -> SeededEvent | None:
        if not isinstance(raw, dict):
            raise EventCalendarFetchError(
                "each event calendar record must be a JSON object"
            )
        title = str(raw.get("title") or "").strip()
        if not title:
            return None
        start_date = _parse_iso_date(raw.get("start_date"), field="start_date", title=title)
        end_date = (
            _parse_iso_date(raw.get("end_date"), field="end_date", title=title)
            if str(raw.get("end_date") or "").strip()
            else None
        )
        event = EventInput(
            title=title,
            event_type=str(raw.get("event_type") or "").strip(),
            date_status=str(raw.get("date_status") or "").strip(),
            start_date=start_date,
            end_date=end_date,
            source=str(raw.get("source") or "").strip() or self.source_name,
            source_url=str(raw.get("source_url") or "").strip() or None,
            description=str(raw.get("description") or "").strip() or None,
            importance_score=self._coerce_importance(raw.get("importance_score")),
        )
        return SeededEvent(event=event, links=self._links(raw))

    def _coerce_importance(self, value: Any) -> Decimal:
        if value in (None, ""):
            return self.default_importance
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return self.default_importance

    def _links(self, raw: dict[str, Any]) -> tuple[EventLinkInput, ...]:
        raw_links = raw.get("links")
        if isinstance(raw_links, list):
            links = [
                link
                for item in raw_links
                if isinstance(item, dict)
                and (link := _link_from_mapping(item)) is not None
            ]
            if links:
                return tuple(links)
        return _links_from_row(
            {key: str(raw.get(key) or "") for key in ("ticker", "sector", "theme", "event_key")}
        )


def _parse_iso_date(value: Any, *, field: str, title: str) -> date:
    try:
        return date.fromisoformat(str(value or "").strip())
    except ValueError as exc:
        raise EventCalendarFetchError(
            f"event {title!r} has an invalid {field} {value!r}"
        ) from exc


def _link_from_mapping(item: dict[str, Any]) -> EventLinkInput | None:
    fields = {
        key: (str(item.get(key) or "").strip() or None)
        for key in ("ticker", "sector", "theme", "event_key")
    }
    if not any(fields.values()):
        return None
    return EventLinkInput(**fields)


def _links_from_row(raw: dict[str, str]) -> tuple[EventLinkInput, ...]:
    ticker = (raw.get("ticker") or "").strip() or None
    sector = (raw.get("sector") or "").strip() or None
    theme = (raw.get("theme") or "").strip() or None
    event_key = (raw.get("event_key") or "").strip() or None
    if not any((ticker, sector, theme, event_key)):
        return ()
    return (
        EventLinkInput(
            ticker=ticker, sector=sector, theme=theme, event_key=event_key
        ),
    )


__all__ = [
    "BaseEventCalendarAdapter",
    "CsvEventCalendarAdapter",
    "EventCalendarFetchError",
    "HttpEventCalendarAdapter",
    "MockEventCalendarAdapter",
]
