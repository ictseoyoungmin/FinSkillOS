# 10_cleanup.md — Post-Slice-10 News Intelligence Cleanup Before Slice 11

## Purpose

This cleanup task is a small hardening pass after `.devmd/10_News_Intelligence.md` and before starting Slice 11 Event Radar / Catalyst Watch.

Slice 10 is considered complete as **News Intelligence v0**. Do **not** rework the News Intelligence architecture, add live news APIs, implement LLM summarization, or start Event Radar in this cleanup.

The goal is to fix one important data-consistency issue:

> Re-ingesting an existing article URL can leave stale `news_impacts` rows when the updated title/summary produces a different classifier result.

Example:

```text
First ingest:
- URL: https://example.com/story
- title/summary mentions TSLA
- classifier creates TSLA impact

Second ingest with the same URL:
- title/summary now mentions Fed / CPI instead
- classifier creates macro event impact
- old TSLA impact may remain even though it is no longer valid
```

This can pollute:

```text
Symbol Lab ticker-relevant news
News Intelligence holdings-relevant news
Future Event Radar / Catalyst Watch
```

The cleanup should make article re-ingestion deterministic and idempotent.

---

## Scope

Modify only the files needed for this cleanup:

```text
finskillos/db/repositories/news_repo.py
finskillos/services/news_service.py
tests/test_news_intelligence.py
.devmd/10_News_Intelligence.md
```

Optional, only if needed:

```text
tests/test_news_intelligence_ui.py
finskillos/ui/view_models/news_intelligence_vm.py
finskillos/ui/view_models/symbol_lab_vm.py
```

Do **not** implement:

```text
Slice 11 Event Radar / Catalyst Watch
live news API adapters
RSS fetching
paid news providers
LLM summarization
source-reliability scoring
full-text article storage
browser/screenshot tests
brokerage / trade execution
direct buy/sell recommendation features
```

FinSkillOS must remain an interpretation-first personal trading operating system that outputs market state, risk interpretation, constraints, watchpoints, and reflection support only.

---

# Task 1 — Add impact synchronization for re-ingested articles

## Problem

`NewsService.ingest_article()` currently:

1. upserts article by URL
2. builds `impact_inputs` from `extra_impacts` and classifier output
3. calls `NewsImpactRepository.add_or_update_impact(...)`

This updates existing matching impact rows and inserts new ones, but it does not remove old impact rows that are no longer present in the new classifier/manual impact result.

## Required behavior

When the same article URL is ingested again, the set of impacts for that article should be synchronized to the new desired set by default.

Suggested behavior:

```text
- Compute desired impact keys from current extra_impacts + classifier output.
- Existing rows whose keys are not in desired keys should be deleted.
- Existing rows whose keys remain should be updated.
- New keys should be inserted.
```

Use this impact key:

```python
(article_id, ticker, sector, theme, event_key)
```

For comparison, `article_id` is fixed after article upsert, so helper keys can be:

```python
(ticker, sector, theme, event_key)
```

Normalize ticker to uppercase when building keys.

## Recommended API

Update `NewsService.ingest_article()`:

```python
def ingest_article(
    self,
    article: NewsArticleInput,
    *,
    extra_impacts: Sequence[NewsImpactInput] = (),
    auto_classify: bool = True,
    replace_impacts: bool = True,
) -> IngestedArticle:
    ...
```

Default should be:

```python
replace_impacts=True
```

because deterministic re-ingestion should not accumulate stale classifier output.

If a future caller wants append-only behavior, it can pass:

```python
replace_impacts=False
```

## Required repository additions

Update:

```text
finskillos/db/repositories/news_repo.py
```

`list_for_article()` already exists; reuse it.

Add a simple delete helper:

```python
def delete(self, impact: NewsImpact) -> None:
    self.session.delete(impact)
    self.session.flush()
```

## Required service helper

In `finskillos/services/news_service.py`, add helpers similar to:

```python
def _impact_key(
    impact: NewsImpactInput | NewsImpact,
) -> tuple[str | None, str | None, str | None, str | None]:
    ticker = impact.ticker.upper() if impact.ticker else None
    return (ticker, impact.sector, impact.theme, impact.event_key)
```

Then inside `ingest_article()`:

```python
impact_inputs = _dedupe_impact_inputs(impact_inputs)

if replace_impacts:
    desired_keys = {_impact_key(i) for i in impact_inputs}
    for existing in self.impacts.list_for_article(row.id):
        if _impact_key(existing) not in desired_keys:
            self.impacts.delete(existing)
```

Then upsert the desired impacts.

## Edge cases

If `impact_inputs` is empty and `replace_impacts=True`:

```text
Delete all existing impacts for that article.
```

This is correct. It means the new article content no longer maps to any known impact.

If `replace_impacts=False`:

```text
Keep old impacts and upsert new ones.
```

This preserves backward-compatible append behavior.

## Acceptance criteria

- Re-ingesting the same URL with a different classifier result removes stale old impact rows.
- Re-ingesting the same URL with no classifier result removes old impacts if `replace_impacts=True`.
- Passing `replace_impacts=False` preserves old impacts while adding/updating new impacts.
- Existing `duplicate URL updates existing article` behavior remains unchanged.
- Existing `re-ingest does not multiply impact rows` behavior remains unchanged.

---

# Task 2 — Normalize impact keys consistently

## Problem

Ticker matching is case-sensitive in some persistence paths unless callers manually pass uppercase. The classifier emits uppercase tickers, but manual input may pass lowercase.

## Required behavior

Normalize ticker to uppercase before impact persistence.

In `NewsService.ingest_article()` or a helper:

```python
def _normalize_impact_input(impact: NewsImpactInput) -> NewsImpactInput:
    return NewsImpactInput(
        ticker=impact.ticker.upper() if impact.ticker else None,
        sector=impact.sector,
        theme=impact.theme,
        event_key=impact.event_key,
        impact_score=impact.impact_score,
        sentiment_label=impact.sentiment_label,
        risk_level=impact.risk_level,
        risk_note=impact.risk_note,
        volatility_note=impact.volatility_note,
        is_event_linked=impact.is_event_linked,
    )
```

Also trim empty strings:

```text
ticker="" -> None
sector="" -> None
theme="" -> None
event_key="" -> None
```

Do not over-normalize sector/theme casing unless existing code already does so.

## Acceptance criteria

- Manual `NewsImpactInput(ticker="tsla")` is persisted as `TSLA`.
- Impact key comparison treats `tsla` and `TSLA` as the same key.
- Duplicate manual lowercase/uppercase impacts do not create duplicate rows.

---

# Task 3 — Add regression tests

Update:

```text
tests/test_news_intelligence.py
```

Add tests for stale impact cleanup.

## Test 1 — re-ingest removes stale classifier impact

Suggested test:

```python
def test_reingest_replaces_stale_classifier_impacts(db_session: Session) -> None:
    service = NewsService(db_session)

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url="https://example.com/reclass",
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )

    service.ingest_article(
        NewsArticleInput(
            title="Fed signals rate pause",
            source="manual",
            url="https://example.com/reclass",
            published_at=NOW,
            summary="The Fed kept rates unchanged.",
        )
    )

    article = NewsArticleRepository(db_session).get_by_url("https://example.com/reclass")
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)

    tickers = {i.ticker for i in impacts if i.ticker}
    event_keys = {i.event_key for i in impacts if i.event_key}

    assert "TSLA" not in tickers
    assert "FED_DECISION" in event_keys
```

## Test 2 — re-ingest with no classifier hit clears impacts

```python
def test_reingest_with_no_impact_clears_existing_impacts(db_session: Session) -> None:
    service = NewsService(db_session)
    url = "https://example.com/no-impact-reclass"

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url=url,
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )
    service.ingest_article(
        NewsArticleInput(
            title="Company posts neutral blog update",
            source="manual",
            url=url,
            published_at=NOW,
            summary="No tracked ticker or sector keyword appears.",
        )
    )

    article = NewsArticleRepository(db_session).get_by_url(url)
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)
    assert impacts == []
```

## Test 3 — replace_impacts_false preserves old impacts

```python
def test_reingest_can_preserve_old_impacts_when_replace_disabled(
    db_session: Session,
) -> None:
    service = NewsService(db_session)
    url = "https://example.com/append-reclass"

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url=url,
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )
    service.ingest_article(
        NewsArticleInput(
            title="Fed signals rate pause",
            source="manual",
            url=url,
            published_at=NOW,
            summary="The Fed kept rates unchanged.",
        ),
        replace_impacts=False,
    )

    article = NewsArticleRepository(db_session).get_by_url(url)
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)
    tickers = {i.ticker for i in impacts if i.ticker}
    event_keys = {i.event_key for i in impacts if i.event_key}

    assert "TSLA" in tickers
    assert "FED_DECISION" in event_keys
```

## Test 4 — manual lowercase ticker normalizes

```python
def test_manual_impact_ticker_is_normalized_to_uppercase(
    db_session: Session,
) -> None:
    service = NewsService(db_session)
    ingested = service.ingest_article(
        NewsArticleInput(
            title="manual mapping",
            source="manual",
            url="https://example.com/lowercase-ticker",
            published_at=NOW,
            summary="manual summary",
        ),
        auto_classify=False,
        extra_impacts=(NewsImpactInput(ticker="tsla"),),
    )

    assert ingested.impacts[0].ticker == "TSLA"
```

## Test 5 — lowercase/uppercase manual duplicate does not multiply rows

```python
def test_manual_impact_key_dedupes_lowercase_and_uppercase_ticker(
    db_session: Session,
) -> None:
    service = NewsService(db_session)
    ingested = service.ingest_article(
        NewsArticleInput(
            title="manual mapping",
            source="manual",
            url="https://example.com/dedupe-case",
            published_at=NOW,
            summary="manual summary",
        ),
        auto_classify=False,
        extra_impacts=(
            NewsImpactInput(ticker="tsla"),
            NewsImpactInput(ticker="TSLA"),
        ),
    )

    impacts = NewsImpactRepository(db_session).list_for_article(ingested.article.id)
    assert len([i for i in impacts if i.ticker == "TSLA"]) == 1
```

## Existing tests that must still pass

```text
test_duplicate_url_updates_existing_article
test_re_ingest_does_not_multiply_impact_rows
test_holdings_relevant_uses_current_positions
test_symbol_lab_view_model_surfaces_ticker_news
```

---

# Task 4 — Update docs / completion note

Update:

```text
.devmd/10_News_Intelligence.md
```

Append a post-cleanup block below the existing completion section:

```text
Post-Slice-10 Cleanup Status: DONE (YYYY-MM-DD)

Changed files:
- finskillos/db/repositories/news_repo.py
- finskillos/services/news_service.py
- tests/test_news_intelligence.py
- .devmd/10_News_Intelligence.md

Behavior change:
- Re-ingesting an existing article URL now synchronizes news_impacts by default.
- Stale classifier/manual impact rows are removed when replace_impacts=True.
- replace_impacts=False preserves append/update behavior for callers that need it.
- Manual ticker impacts are normalized to uppercase.
- Lowercase/uppercase duplicate ticker impacts dedupe to one impact key.

Verification:
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_news_intelligence.py -q
- python3 -m pytest tests/test_news_intelligence_ui.py -q
- python3 -m pytest tests/test_symbol_lab_view_model.py tests/test_symbol_lab_ui.py -q
- python3 -m pytest tests -q
- python3 -m ruff check finskillos/db finskillos/services tests/test_news_intelligence.py

Known issues:
- Live / paid news adapters remain out of scope.
- LLM-based article summarization remains out of scope.
- Full Event Radar integration remains deferred to Slice 11.
- Source reliability scoring remains deferred.
```

## Acceptance criteria

- `.devmd/10` clearly records the cleanup behavior.
- Future Event Radar implementation can rely on stale impacts being removed during article re-ingest.

---

# Verification commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos scripts

python3 -m pytest \
  tests/test_news_intelligence.py \
  tests/test_news_intelligence_ui.py \
  -q

python3 -m pytest \
  tests/test_symbol_lab_view_model.py \
  tests/test_symbol_lab_ui.py \
  -q

python3 -m pytest tests -q

python3 -m ruff check \
  finskillos/db \
  finskillos/services \
  tests/test_news_intelligence.py
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
- News Intelligence still renders.
- Manual article entry still works.
- Re-entering the same URL updates the article instead of duplicating it.
- Holdings-relevant news does not show stale ticker mappings after article update.
- Symbol Lab ticker news reflects the updated impact mapping.
```

---

## Stop condition

Stop after this cleanup is complete.

Do **not** begin Slice 11 until the user explicitly asks to proceed.
