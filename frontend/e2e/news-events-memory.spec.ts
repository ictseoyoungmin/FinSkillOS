import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "./_helpers";

test.describe("Slice 13.9 — News Intelligence / Catalyst Watch / Trade Memory", () => {
  test("News Intelligence renders impact map + manual article entry", async ({
    page,
  }) => {
    await page.goto("/news-intel");
    await expect(page.getByTestId("news-intelligence-page")).toBeVisible();
    await expect(page.getByTestId("news-judgment-header")).toBeVisible();
    await expect(page.getByTestId("news-impact-map")).toBeVisible();
    await expect(page.getByTestId("news-impact-map-table")).toBeVisible();
    await expect(page.getByTestId("news-manual-article")).toBeVisible();
    await expect(
      page.getByTestId("news-manual-article-disclaimer"),
    ).toContainText("Short summaries only");
    await expect(
      page.getByTestId("news-intelligence-safety-caption"),
    ).toContainText("Descriptive");
  });

  test("Catalyst Watch renders date-status badges and manual event entry", async ({
    page,
  }) => {
    await page.goto("/catalyst-watch");
    await expect(page.getByTestId("catalyst-watch-page")).toBeVisible();
    await expect(page.getByTestId("event-judgment-header")).toBeVisible();
    await expect(page.getByTestId("event-upcoming")).toBeVisible();
    await expect(page.getByTestId("event-upcoming-table")).toBeVisible();
    await expect(page.getByTestId("event-manual-entry")).toBeVisible();
    // At least one date-status badge must render.
    await expect(
      page.locator(".fso-event-status-badge").first(),
    ).toBeVisible();
    // Safety caption must call out preparation / exposure framing.
    await expect(
      page.getByTestId("catalyst-watch-safety-caption"),
    ).toContainText("preparation");
  });

  test("Trade Memory renders weekly markdown textarea and mistake frequency", async ({
    page,
  }) => {
    await page.goto("/trade-memory");
    await expect(page.getByTestId("trade-memory-page")).toBeVisible();
    await expect(page.getByTestId("trade-judgment-header")).toBeVisible();
    await expect(
      page.getByTestId("trade-weekly-markdown-textarea"),
    ).toBeVisible();
    await expect(
      page.getByTestId("trade-mistake-frequency-table"),
    ).toBeVisible();
    await expect(page.getByTestId("trade-entry-form")).toBeVisible();
    await expect(
      page.getByTestId("trade-entry-form-disclaimer"),
    ).toContainText("Reflection");
  });

  test("Trade Memory side selector exposes Slice-12 vocabulary only", async ({
    page,
  }) => {
    await page.goto("/trade-memory");
    const select = page.getByTestId("trade-entry-form-side");
    const options = await select.locator("option").allTextContents();
    expect(options).toEqual([
      "LONG",
      "SHORT",
      "WATCH",
      "EXIT_REVIEW",
      "OTHER",
    ]);
  });

  test("Manual article entry rejects an over-cap summary", async ({
    page,
    request,
  }) => {
    await page.goto("/news-intel");
    const response = await request.post("/api/news-intelligence/manual-article", {
      data: {
        title: "Probe",
        source: "Probe",
        url: "https://example.com/probe",
        publishedAt: "2026-05-20T12:00:00+00:00",
        summary: "x".repeat(700),
        affectedTickers: [],
        theme: null,
        eventKey: null,
        sentiment: "UNKNOWN",
        riskLevel: "UNKNOWN",
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("REJECTED");
    expect(String(body.detail)).toContain("summary_too_long");
  });

  test("Manual event entry rejects CONFIRMED + manual_seed", async ({
    request,
  }) => {
    const response = await request.post("/api/event-radar/manual-event", {
      data: {
        title: "Should be rejected",
        eventType: "EARNINGS",
        dateStatus: "CONFIRMED",
        startDate: "2026-06-01",
        endDate: null,
        source: "manual_seed",
        sourceUrl: null,
        description: null,
        importanceScore: "1.0",
        ticker: null,
        sector: null,
        theme: null,
        eventKey: null,
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("REJECTED");
    expect(String(body.detail)).toContain("confirmed_requires_external_source");
  });

  test("Manual trade entry rejects forbidden wording", async ({ request }) => {
    const response = await request.post("/api/trade-memory/entries", {
      data: {
        tradeDate: "2026-05-19",
        ticker: "TSLA",
        side: "LONG",
        notes: "지금 사라",
        mistakeTags: [],
      },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("REJECTED");
  });

  test("Slice 13.9 routes never expose forbidden execution captions", async ({
    page,
  }) => {
    for (const path of ["/news-intel", "/catalyst-watch", "/trade-memory"]) {
      await page.goto(path);
      const body = await page.locator("body").innerText();
      for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
        expect(
          body,
          `${path} body should not include ${forbidden}`,
        ).not.toContain(forbidden);
      }
      // Descriptive market idiom "sell-the-news" remains allowed; the
      // forbidden-list check above only blocks bare execution labels.
    }
  });
});
