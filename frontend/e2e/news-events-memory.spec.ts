import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "./_helpers";

test.describe("Slice 13.9 — News Intelligence / Catalyst Watch / Trade Memory", () => {
  test("News Intelligence renders impact map and source coverage", async ({
    page,
  }) => {
    await page.goto("/news-intel");
    await expect(page.getByTestId("news-intelligence-page")).toBeVisible();
    await expect(page.getByTestId("news-judgment-header")).toBeVisible();
    await expect(page.getByTestId("news-source-coverage")).toBeVisible();
    await expect(page.getByTestId("news-source-coverage")).toContainText(
      /Providers/i,
    );
    await expect(page.getByTestId("news-impact-map")).toBeVisible();
    await expect(page.getByTestId("news-impact-map-table")).toBeVisible();
    await expect(
      page.getByTestId("news-intelligence-safety-caption"),
    ).toContainText("Descriptive");
  });

  test("Catalyst Watch renders date-status badges and event catalog evidence", async ({
    page,
  }) => {
    await page.goto("/catalyst-watch");
    await expect(page.getByTestId("catalyst-watch-page")).toBeVisible();
    await expect(page.getByTestId("event-judgment-header")).toBeVisible();
    await expect(page.getByTestId("catalyst-data-state")).toBeVisible();
    await expect(page.getByTestId("catalyst-data-state")).toContainText(
      /Calendar source/i,
    );
    await expect(page.getByTestId("catalyst-data-state")).toContainText(
      /Date confidence/i,
    );
    await expect(page.getByTestId("event-upcoming")).toBeVisible();
    await expect(page.getByTestId("event-upcoming-table")).toBeVisible();
    await expect(page.getByTestId("event-catalog-evidence")).toBeVisible();
    await expect(page.getByTestId("event-catalog-evidence")).toContainText(
      /Calendar rows/i,
    );
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

  test("Trade Memory form stores an entry and refreshes the read model", async ({
    page,
    request,
  }) => {
    await request.post("/api/system-ops/seed-sample-account");
    await page.goto("/trade-memory");
    const form = page.getByTestId("trade-entry-form");

    await expect(page.getByTestId("trade-entry-form-state")).toContainText(
      /Required\s*missing/i,
    );
    await form.getByLabel("Trade date").fill("2026-05-28");
    await form.getByLabel("Ticker").fill("AMD");
    await expect(page.getByTestId("trade-entry-form-state")).toContainText(
      /Required\s*ready/i,
    );
    await form.getByTestId("trade-entry-form-side").selectOption("WATCH");
    await form.getByLabel("Strategy").fill("review");
    await form.getByRole("textbox", { name: "Regime" }).fill("HEALTHY_BULL");
    await form
      .getByRole("textbox", { name: "Thesis" })
      .fill("Process review entry.");
    await form
      .getByRole("textbox", { name: "Reason" })
      .fill("Checklist practice remained calm.");
    await form
      .getByRole("textbox", { name: "Notes" })
      .fill("Reflection-only journal smoke.");
    await page.getByTestId("trade-entry-form-submit").click();

    await expect(page.getByTestId("trade-entry-form-result")).toContainText("OK");
    await expect(page.getByTestId("trade-memory-source-state")).toContainText(
      /Source\s*LIVE/,
    );
    await expect(page.getByTestId("recent-entries")).toContainText("AMD");
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
