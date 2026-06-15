import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS } from "./_helpers";

test.describe("Slice 13.7 — Market Kernel / Analysis Workspace / Symbol Lab", () => {
  test("Market Kernel renders symbol rail and chart panel", async ({ page }) => {
    await page.goto("/market-kernel");
    await expect(page.getByTestId("market-kernel-page")).toBeVisible();
    await expect(page.getByTestId("symbol-universe-rail")).toBeVisible();
    await expect(page.getByTestId("market-kernel-chart-panel")).toBeVisible();
    // Market Kernel now shares the candlestick chart with Symbol Lab.
    await expect(page.getByTestId("chart-panel")).toBeVisible();
    await expect(page.getByTestId("symbol-candle-svg")).toBeVisible();
    await expect(page.getByTestId("market-kernel-data-state")).toBeVisible();
    await expect(page.getByTestId("market-kernel-data-state")).toContainText(
      /Coverage/i,
    );
    await expect(page.getByTestId("ticker-search")).toBeVisible();
    await expect(
      page.getByTestId("market-kernel-safety-caption"),
    ).toContainText("Stored data only");
  });

  test("Market Kernel ticker query param swaps the selected symbol", async ({
    page,
  }) => {
    await page.goto("/market-kernel?ticker=TSLA");
    const header = page.getByTestId("market-kernel-header");
    await expect(header).toContainText("TSLA");
  });

  test("Market Kernel uses the shared candlestick chart with timeframe buttons", async ({
    page,
  }) => {
    await page.goto("/market-kernel");
    const chart = page.getByTestId("chart-panel");
    await expect(chart).toBeVisible();
    const svg = page.getByTestId("symbol-candle-svg");
    await expect(svg).toBeVisible();
    // The chart provides its own 1d / 1w / 1mo buttons; switching keeps it rendered.
    await chart.getByRole("button", { name: "1w", exact: true }).click();
    await expect(svg).toBeVisible();
  });

  test("Analysis Workspace renders Index Lab table + strongest entries", async ({
    page,
  }) => {
    await page.goto("/analysis-workspace");
    await expect(page.getByTestId("analysis-workspace-page")).toBeVisible();
    await expect(
      page.getByTestId("analysis-workspace-universe-table"),
    ).toBeVisible();
    await expect(page.getByTestId("analysis-workspace-data-state")).toBeVisible();
    await expect(page.getByTestId("analysis-workspace-data-state")).toContainText(
      /Coverage/i,
    );
    await expect(page.getByTestId("analysis-workspace-strongest")).toBeVisible();
    await expect(page.getByTestId("analysis-workspace-weakest")).toBeVisible();
    await expect(page.getByTestId("analysis-workspace-regime")).toBeVisible();
    // At least one ranked row must be rendered (Strongest panel).
    const strongest = page.getByTestId("analysis-workspace-strongest-list");
    await expect(strongest).toBeVisible();
    await expect(strongest.locator("li")).toHaveCount(3);
    await expect(
      page.getByTestId("analysis-workspace-safety-caption"),
    ).toContainText("Stored data only");
  });

  test("Symbol Lab default ticker shows data state and position panel", async ({
    page,
  }) => {
    await page.goto("/symbol-lab");
    await expect(page.getByTestId("symbol-lab-page")).toBeVisible();
    await expect(page.getByTestId("ticker-search")).toBeVisible();
    await expect(page.locator(".fso-ticker-search-option").first()).toBeVisible();
    await expect(page.getByTestId("symbol-data-state")).toBeVisible();
    await expect(page.getByTestId("symbol-data-state")).toContainText(/Coverage/i);
    await expect(page.getByTestId("symbol-technical-snapshot")).toBeVisible();
    await expect(page.getByTestId("symbol-recent-bars")).toBeVisible();
    const position = page.getByTestId("symbol-position-context");
    await expect(position).toBeVisible();
    await expect(position).toContainText("Position Context");
    await expect(
      page.getByTestId("symbol-watchpoints-safety-caption"),
    ).toContainText("Stored data only");
  });

  test("Symbol Lab non-held ticker shows the empty-state position card", async ({
    page,
  }) => {
    await page.goto("/symbol-lab?ticker=NVDA");
    const position = page.getByTestId("symbol-position-context");
    await expect(position).toBeVisible();
    await expect(position).toContainText("No current holding");
  });

  test("Symbol Lab search accepts stored universe symbols", async ({
    page,
  }) => {
    await page.goto("/symbol-lab");
    await page.locator("#ticker-search-input").fill("smh");
    await page.getByTestId("ticker-search-submit").click();
    await expect(page).toHaveURL(/ticker=SMH/);
    await expect(page.getByTestId("judgment-header")).toContainText("SMH");
    await expect(page.getByTestId("symbol-data-state")).toContainText(/Coverage/i);
  });

  test("Symbol Lab accepts arbitrary ticker input", async ({ page }) => {
    await page.goto("/symbol-lab");
    await page.locator("#ticker-search-input").fill("adbe");
    await page.getByTestId("ticker-search-submit").click();
    await expect(page).toHaveURL(/ticker=ADBE/);
    await expect(page.getByTestId("judgment-header")).toContainText("ADBE");
    await expect(page.getByTestId("symbol-data-state")).toContainText(/Coverage/i);
  });

  test("Symbol Lab macro proxies remain searchable through free text", async ({
    page,
  }) => {
    await page.goto("/symbol-lab");
    await expect(
      page.locator(".fso-ticker-search-option", { hasText: "US10Y" }),
    ).toHaveCount(0);
    await page.locator("#ticker-search-input").fill("us10y");
    await page.getByTestId("ticker-search-submit").click();
    await expect(page).toHaveURL(/ticker=US10Y/);
    await expect(page.getByTestId("judgment-header")).toContainText("US10Y");
    await expect(page.getByTestId("symbol-data-state")).toContainText(/Coverage/i);
  });

  test("Slice 13.7 routes never expose forbidden execution captions", async ({
    page,
  }) => {
    for (const path of [
      "/market-kernel",
      "/analysis-workspace",
      "/symbol-lab",
    ]) {
      await page.goto(path);
      const body = await page.locator("body").innerText();
      for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
        expect(body, `${path} body should not include ${forbidden}`).not.toContain(
          forbidden,
        );
      }
    }
  });
});
