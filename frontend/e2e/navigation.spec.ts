import { expect, test } from "@playwright/test";
import {
  FORBIDDEN_EXECUTION_LABELS,
  MAIN_NAV_LABELS,
  gotoControlRoom,
} from "./_helpers";

test.describe("OS shell navigation", () => {
  test("Control Room is the default route", async ({ page }) => {
    await gotoControlRoom(page);
    await expect(page.getByTestId("control-room-grid")).toBeVisible();
    await expect(page.getByTestId("os-tray")).toBeVisible();
    await expect(page.getByTestId("ticker-strip")).toBeVisible();
  });

  test("Control Room renders the three required columns", async ({ page }) => {
    await gotoControlRoom(page);
    await expect(page.getByTestId("control-room-left")).toBeVisible();
    await expect(page.getByTestId("control-room-center")).toBeVisible();
    await expect(page.getByTestId("control-room-right")).toBeVisible();
    await expect(page.getByTestId("operating-state-hero")).toBeVisible();
    await expect(page.getByTestId("risk-firewall-summary")).toBeVisible();
    await expect(page.getByTestId("catalyst-watch-summary")).toBeVisible();
    await expect(page.getByTestId("watchlist-card")).toBeVisible();
  });

  test("OS top tray exposes every product module", async ({ page }) => {
    await gotoControlRoom(page);
    const nav = page.getByTestId("os-nav");
    for (const label of MAIN_NAV_LABELS) {
      await expect(nav.getByText(label, { exact: true })).toBeVisible();
    }
  });

  test("Analysis Workspace route resolves to its own page", async ({ page }) => {
    await page.goto("/analysis-workspace");
    await expect(page.getByTestId("analysis-workspace-page")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Analysis Workspace" })).toBeVisible();
  });

  test("unknown routes redirect to Control Room", async ({ page }) => {
    await page.goto("/does-not-exist");
    await expect(page.getByTestId("control-room-grid")).toBeVisible();
  });

  test("no forbidden execution control captions are present", async ({ page }) => {
    await gotoControlRoom(page);
    const body = await page.locator("body").innerText();
    for (const forbidden of FORBIDDEN_EXECUTION_LABELS) {
      expect(body).not.toContain(forbidden);
    }
  });
});
