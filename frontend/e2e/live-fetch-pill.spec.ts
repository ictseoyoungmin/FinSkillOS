import { expect, test } from "@playwright/test";

/**
 * Slice 88/119 — when a product tab's live fetch fails, the page no longer silently
 * shows the fixture as if it were live. It renders the fixture *shape* plus an
 * explicit "live data unavailable" pill.
 */
const LIVE_FAILURE_TABS = [
  {
    name: "Control Room",
    route: "/",
    apiPattern: "**/api/control-room**",
    pageTestId: "control-room-grid",
    pillTestId: "control-room-live-failed",
  },
  {
    name: "Market Kernel",
    route: "/market-kernel",
    apiPattern: "**/api/market-kernel**",
    pageTestId: "market-kernel-page",
    pillTestId: "market-kernel-live-failed",
  },
  {
    name: "Analysis Workspace",
    route: "/analysis-workspace",
    apiPattern: "**/api/analysis-workspace**",
    pageTestId: "analysis-workspace-page",
    pillTestId: "analysis-workspace-live-failed",
  },
  {
    name: "Risk Firewall",
    route: "/risk-firewall",
    apiPattern: "**/api/risk-firewall**",
    pageTestId: "risk-firewall-page",
    pillTestId: "risk-firewall-live-failed",
  },
  {
    name: "Mission Control",
    route: "/mission-control",
    apiPattern: "**/api/mission-control**",
    pageTestId: "mission-control-page",
    pillTestId: "mission-control-live-failed",
  },
  {
    name: "News Intelligence",
    route: "/news-intel",
    apiPattern: "**/api/news-intelligence**",
    pageTestId: "news-intelligence-page",
    pillTestId: "news-intelligence-live-failed",
  },
  {
    name: "Catalyst Watch",
    route: "/catalyst-watch",
    apiPattern: "**/api/event-radar**",
    pageTestId: "catalyst-watch-page",
    pillTestId: "catalyst-watch-live-failed",
  },
  {
    name: "Trade Memory",
    route: "/trade-memory",
    apiPattern: "**/api/trade-memory",
    pageTestId: "trade-memory-page",
    pillTestId: "trade-memory-live-failed",
  },
  {
    name: "System Ops",
    route: "/system-ops",
    apiPattern: "**/api/system-ops",
    pageTestId: "system-ops-page",
    pillTestId: "system-ops-live-failed",
  },
] as const;

for (const tab of LIVE_FAILURE_TABS) {
  test(`${tab.name} shows a live-data-unavailable pill when its API fails`, async ({
    page,
  }) => {
    await page.route(tab.apiPattern, (route) => route.abort());

    await page.goto(tab.route);
    await expect(page.getByTestId(tab.pageTestId)).toBeVisible();

    const pill = page.getByTestId(tab.pillTestId);
    await expect(pill).toBeVisible();
    await expect(pill).toContainText("Live data unavailable");
    await expect(pill).toContainText("sample shape, not live data");
  });
}

for (const tab of LIVE_FAILURE_TABS) {
  test(`${tab.name} has no live-data-unavailable pill when the API responds`, async ({
    page,
  }) => {
    await page.goto(tab.route);
    await page.waitForSelector(`[data-testid="${tab.pageTestId}"]`);
    await expect(page.getByTestId(tab.pillTestId)).toHaveCount(0);
  });
}
