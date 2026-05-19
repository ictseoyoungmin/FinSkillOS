# 11_cleanup.md — Post-Slice-11 Event Radar Cleanup Before Slice 12

## Purpose

This cleanup task is a small hardening pass after `.devmd/11_Event_Radar.md` and before starting Slice 12 Trade Memory / Trade Journal.

Slice 11 is considered complete as **Event Radar v0**. Do **not** rework the Event Radar architecture, add live event feeds, implement a full calendar-grid UI, or start Trade Memory in this cleanup.

The goal is to close a few consistency and editability gaps found during review:

1. `EventRepository.update_event()` cannot clearly distinguish “field not provided” from “clear this nullable field to None”.
2. `EventService.list_for_event_key()` currently bypasses `EventLinkRepository`.
3. Event link ticker normalization is mostly enforced through `EventService`, but repository-level protection should prevent accidental `tsla` / `TSLA` duplication.
4. Event Radar v0 should remain explicit that its score is a preparation / exposure score, not a prediction.

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, event exposure, risk interpretation, constraints, watchpoints, and reflection support only.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/db/repositories/event_repo.py
finskillos/services/event_service.py
finskillos/services/event_risk_service.py
tests/test_event_radar.py
.devmd/11_Event_Radar.md
```

Optional, only if needed:

```text
finskillos/ui/view_models/event_radar_vm.py
finskillos/ui/pages/event_radar.py
tests/test_event_radar_ui.py
```

Do **not** implement:

```text
Slice 12 Trade Memory / Trade Journal
full calendar-grid UI
live external event feeds
Bloomberg / FactSet / exchange calendar integrations
BLS / Fed scraping
LLM event summarization
source-reliability scoring
brokerage / trade execution
direct buy/sell recommendation features
```

---

# Task 1 — Fix nullable event update semantics

## Problem

`EventRepository.update_event()` currently uses `None` to mean “do not update this field.”

That means nullable fields cannot be cleared through the normal update path:

```text
end_date
source
source_url
description
```

Example problem:

```text
A WINDOW event has end_date=2026-06-30.
User edits it into a single-date TENTATIVE event and sends end_date=None.
Repository interprets end_date=None as “leave unchanged”.
Old end_date remains.
```

This conflicts with Slice 11’s requirement that event dates should be editable.

## Required change

Update:

```text
finskillos/db/repositories/event_repo.py
```

Introduce an unset sentinel:

```python
_UNSET = object()
```

Update `EventRepository.update_event()` so nullable fields can be explicitly cleared.

Suggested signature:

```python
def update_event(
    self,
    event_id: uuid.UUID,
    *,
    title: str | None = None,
    event_type: str | None = None,
    date_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None | object = _UNSET,
    source: str | None | object = _UNSET,
    source_url: str | None | object = _UNSET,
    description: str | None | object = _UNSET,
    importance_score: Decimal | None = None,
) -> Event:
    ...
```

Then:

```python
if end_date is not _UNSET:
    event.end_date = end_date
if source is not _UNSET:
    event.source = source
if source_url is not _UNSET:
    event.source_url = source_url
if description is not _UNSET:
    event.description = description
```

Keep non-null fields as-is:

```text
title
event_type
date_status
start_date
importance_score
```

## Required service behavior

Update:

```text
finskillos/services/event_service.py
```

`EventService.update_event(event_id, event: EventInput)` should pass through nullable fields explicitly:

```python
end_date=event.end_date
source=event.source
source_url=event.source_url
description=event.description
```

Because this method receives a full `EventInput`, `None` should mean “clear the field”.

## Required tests

Update:

```text
tests/test_event_radar.py
```

Add:

```python
def test_update_event_can_clear_nullable_fields(db_session: Session) -> None:
    service = EventService(db_session)
    event = service.create_event(
        EventInput(
            title="Window event",
            event_type=EVENT_TYPE_PRODUCT_EVENT,
            date_status=DATE_STATUS_WINDOW,
            start_date=TODAY,
            end_date=TODAY,
            source="manual",
            source_url="https://example.com/source",
            description="old description",
            importance_score=Decimal("2.0"),
        )
    )

    updated = service.update_event(
        event.id,
        EventInput(
            title="Window event",
            event_type=EVENT_TYPE_PRODUCT_EVENT,
            date_status=DATE_STATUS_TENTATIVE,
            start_date=TODAY,
            end_date=None,
            source=None,
            source_url=None,
            description=None,
            importance_score=Decimal("2.0"),
        ),
    )

    assert updated.end_date is None
    assert updated.source is None
    assert updated.source_url is None
    assert updated.description is None
```

## Acceptance criteria

- `end_date` can be cleared.
- `source` can be cleared.
- `source_url` can be cleared.
- `description` can be cleared.
- Existing update tests still pass.

---

# Task 2 — Move event_key lookup into EventLinkRepository

## Problem

`EventService.list_for_event_key()` currently queries `EventLink` directly through the session.

This bypasses the repository pattern used elsewhere and makes future event-key matching harder to reuse.

## Required change

Update:

```text
finskillos/db/repositories/event_repo.py
```

Add:

```python
def list_for_event_key(self, event_key: str) -> list[EventLink]:
    if not event_key:
        return []
    stmt = (
        select(EventLink)
        .where(EventLink.event_key == event_key)
        .order_by(EventLink.created_at)
    )
    return list(self.session.scalars(stmt))
```

Update:

```text
finskillos/services/event_service.py
```

Change `list_for_event_key()` to use:

```python
links = self.links.list_for_event_key(event_key)
```

Do not query `self.session.query(EventLink)` directly.

## Required tests

Existing event_key behavior should continue to pass. Add a direct repository-level test if not already covered:

```python
def test_event_link_repository_lists_by_event_key(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(
        service,
        links=(EventLinkInput(theme="Macro", event_key="FED_DECISION"),),
    )

    links = EventLinkRepository(db_session).list_for_event_key("FED_DECISION")
    assert len(links) == 1
    assert links[0].event_id == event.id
```

## Acceptance criteria

- `EventService.list_for_event_key()` no longer bypasses repository.
- Event-key lookup remains deterministic.
- Event-linked news and future Catalyst Watch logic can reuse repository method.

---

# Task 3 — Normalize event link keys consistently

## Problem

`EventService._attach_link()` uppercases ticker, but `EventLinkRepository.add_or_update_link()` itself accepts raw ticker.

If future tests or services call the repository directly with `ticker="tsla"` and then `ticker="TSLA"`, duplicate links can be created.

## Required change

Update repository-level normalization.

Preferred helpers:

```python
def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None

def _normalize_ticker(ticker: str | None) -> str | None:
    cleaned = _empty_to_none(ticker)
    return cleaned.upper() if cleaned else None
```

Then inside `EventLinkRepository.add_or_update_link()`:

```python
ticker = _normalize_ticker(ticker)
sector = _empty_to_none(sector)
theme = _empty_to_none(theme)
event_key = _empty_to_none(event_key)
```

Also use the normalized values in `_find_existing()`.

## Required tests

Add:

```python
def test_event_link_repository_normalizes_ticker_case(db_session: Session) -> None:
    service = EventService(db_session)
    event = _create_event(service)

    links = EventLinkRepository(db_session)
    links.add_or_update_link(event_id=event.id, ticker="tsla")
    links.add_or_update_link(event_id=event.id, ticker="TSLA")

    rows = links.list_for_event(event.id)
    assert len(rows) == 1
    assert rows[0].ticker == "TSLA"
```

Add:

```python
def test_event_link_repository_collapses_empty_dimension_strings(
    db_session: Session,
) -> None:
    service = EventService(db_session)
    event = _create_event(service)

    links = EventLinkRepository(db_session)
    links.add_or_update_link(
        event_id=event.id,
        ticker=" ",
        sector=" ",
        theme=" ",
        event_key=" ",
    )

    row = links.list_for_event(event.id)[0]
    assert row.ticker is None
    assert row.sector is None
    assert row.theme is None
    assert row.event_key is None
```

## Acceptance criteria

- Lowercase and uppercase ticker links dedupe to one row.
- Empty string dimension values collapse to `None`.
- Existing `EventService._attach_link()` behavior remains compatible.
- Existing event link idempotency tests still pass.

---

# Task 4 — Make event risk score wording explicit

## Problem

The implementation already treats `event_risk_score` as a preparation / exposure score. The UI and docs should keep this explicit because otherwise users may mistake it for a prediction.

## Required change

Check:

```text
finskillos/ui/view_models/event_radar_vm.py
finskillos/ui/pages/event_radar.py
.devmd/11_Event_Radar.md
```

Ensure visible text or doc notes say:

```text
event_risk_score is an exposure / preparation score, not a prediction.
```

If the page does not currently say this clearly, add a caption near the top:

```text
이 점수는 가격 예측이 아니라 이벤트 접근성, 포트폴리오 노출, 시장 상태를 반영한 준비 / 노출 점수입니다.
```

Do not add deterministic market prediction wording.

## Required tests

If page copy is updated, add or adjust a source-level UI test in:

```text
tests/test_event_radar_ui.py
```

Example:

```python
def test_event_radar_page_describes_score_as_not_prediction() -> None:
    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    assert "가격 예측이 아니라" in source or "not a prediction" in source
```

## Acceptance criteria

- Event risk score is explicitly described as non-predictive.
- Safety scan still passes.
- No direct buy/sell wording is added.

---

# Task 5 — Update completion note

Update:

```text
.devmd/11_Event_Radar.md
```

Append a post-cleanup block below the existing Slice 11 completion section:

```text
Post-Slice-11 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/db/repositories/event_repo.py
- finskillos/services/event_service.py
- finskillos/ui/pages/event_radar.py
- tests/test_event_radar.py
- tests/test_event_radar_ui.py
- .devmd/11_Event_Radar.md

Behavior change:
- EventRepository.update_event can now clear nullable fields such as end_date, source, source_url, and description.
- EventService.update_event passes full EventInput nullable values through intentionally.
- EventLinkRepository now owns event_key lookup through list_for_event_key().
- EventLinkRepository normalizes ticker case and collapses empty dimension strings before link upsert.
- Event risk score is explicitly described as an exposure / preparation score, not a prediction.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_event_radar.py tests/test_event_radar_ui.py -q
- python3 -m pytest tests/test_news_intelligence.py tests/test_news_intelligence_ui.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/db finskillos/services finskillos/ui tests/test_event_radar.py tests/test_event_radar_ui.py

Known issues:
- Full calendar-grid UI remains deferred.
- Live external event feeds remain out of scope.
- Source reliability scoring remains deferred.
- Trade Memory remains deferred to Slice 12.
- Brokerage / execution remains out of scope.
```

---

# Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_event_radar.py \
  tests/test_event_radar_ui.py \
  -q

python3 -m pytest \
  tests/test_news_intelligence.py \
  tests/test_news_intelligence_ui.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/db \
  finskillos/services \
  finskillos/ui \
  tests/test_event_radar.py \
  tests/test_event_radar_ui.py
```

Optional migration smoke:

```bash
python3 -m pytest tests/integration/test_db_migrations.py -q
```

Optional Docker smoke:

```bash
docker compose down -v
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
docker compose --profile app up --build
```

Manual smoke:

```text
- Catalyst Watch opens Event Radar.
- Sample event seed remains idempotent.
- Manual event entry still works.
- Window event can be edited to clear end_date through the service path.
- Event-linked news still appears.
- Event risk score is clearly described as non-predictive.
- No direct buy/sell wording appears.
```

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin Slice 12 until the user explicitly asks to proceed.
