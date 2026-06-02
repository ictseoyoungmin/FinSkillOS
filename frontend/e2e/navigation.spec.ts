import { expect, test } from "@playwright/test";
import { FORBIDDEN_EXECUTION_LABELS, gotoControlRoom } from "./_helpers";

const TOP_TRAY_NAV_ITEMS = [
  { key: "control", label: "Control Room", icon: "◉" },
  { key: "kernel", label: "Market Kernel", icon: "⌁" },
  { key: "analysis", label: "Analysis Workspace", icon: "⌬" },
  { key: "symbol", label: "Symbol Lab", icon: "⌕" },
  { key: "firewall", label: "Risk Firewall", icon: "▣" },
  { key: "mission", label: "Mission Control", icon: "★" },
  { key: "news", label: "News Intel", icon: "✎" },
  { key: "catalyst", label: "Catalyst Watch", icon: "⌖" },
  { key: "memory", label: "Trade Memory", icon: "◇" },
  { key: "ops", label: "System Ops", icon: "⚙" },
] as const;

test.describe("OS shell navigation", () => {
  test("Control Room is the default route", async ({ page }) => {
    await gotoControlRoom(page);
    await expect(page.getByTestId("control-room-grid")).toBeVisible();
    await expect(page.getByTestId("control-room-state-band")).toContainText(
      /Overview Source/i,
    );
    await expect(page.getByTestId("control-room-state-band")).toContainText(
      /Rail Freshness/i,
    );
    await expect(page.getByTestId("control-room-state-band")).toContainText(
      /FRESH|STALE|MISSING/i,
    );
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

  test("Control Room shows the Portfolio / Market Tape panel", async ({
    page,
  }) => {
    await gotoControlRoom(page);
    const tape = page.getByTestId("portfolio-market-tape");
    await expect(tape).toBeVisible();
    await expect(page.getByTestId("portfolio-market-tape-legend")).toBeVisible();
    // Safety caption must remain present so users never read the panel
    // as a price prediction.
    await expect(
      page.getByTestId("portfolio-market-tape-caption"),
    ).toContainText("not prediction");
  });

  test("Slice 13.9 promoted routes render their dedicated pages", async ({
    page,
  }) => {
    // Slice 13.7 promoted Market Kernel / Analysis Workspace / Symbol
    // Lab. Slice 13.8 promoted Risk Firewall / Mission Control /
    // System Ops. Slice 13.9 promoted News Intel / Catalyst Watch /
    // Trade Memory. No placeholder shells remain at the top-level OS
    // nav after Slice 13.9.
    const promotedRoutes = [
      { path: "/news-intel", testId: "news-intelligence-page" },
      { path: "/catalyst-watch", testId: "catalyst-watch-page" },
      { path: "/trade-memory", testId: "trade-memory-page" },
    ];
    for (const route of promotedRoutes) {
      await page.goto(route.path);
      const shell = page.getByTestId(route.testId);
      await expect(shell).toBeVisible();
    }
    await page.goto("/trade-memory");
    await expect(page.getByTestId("trade-memory-source-state")).toContainText(
      /Live DB|Deterministic fixture/,
    );
  });

  test("OS top tray exposes every product module with module-specific icons", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await gotoControlRoom(page);
    const nav = page.getByTestId("os-nav");
    for (const item of TOP_TRAY_NAV_ITEMS) {
      await expect(page.getByTestId(`os-nav-${item.key}`)).toHaveAttribute(
        "aria-label",
        item.label,
      );
      await expect(page.getByTestId(`os-nav-icon-${item.key}`)).toHaveText(
        item.icon,
      );
    }

    const navFitsTray = await nav.evaluate((element) => {
      const tray = element.closest("[data-testid='os-tray']");
      if (!tray) {
        return false;
      }
      return tray.scrollWidth <= tray.clientWidth + 1;
    });
    expect(navFitsTray).toBe(true);
  });

  test("global status bar labels source, DB, freshness, and read mode", async ({
    page,
  }) => {
    await gotoControlRoom(page);
    const statusBar = page.getByTestId("os-status-bar");
    await expect(statusBar).toBeVisible();
    await expect(page.getByTestId("snapshot-source-status")).toContainText(
      /FIXTURE|LIVE/,
    );
    await expect(page.getByTestId("db-status")).toContainText(/LIVE|MISSING/);
    await expect(page.getByTestId("freshness-status")).toContainText(
      /OK|stale/,
    );
    await expect(page.getByTestId("completeness-status")).toContainText(
      /COMPLETE|PARTIAL|MISSING/,
    );
    await expect(statusBar).toContainText("No execution controls");
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
