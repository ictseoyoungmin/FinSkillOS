import type { Page } from "@playwright/test";

export const MAIN_NAV_LABELS = [
  "Control Room",
  "Market Kernel",
  "Analysis Workspace",
  "Symbol Lab",
  "Risk Firewall",
  "Mission Control",
  "News Intel",
  "Catalyst Watch",
  "Trade Memory",
  "System Ops",
] as const;

export const FORBIDDEN_EXECUTION_LABELS = [
  "Buy",
  "Sell",
  "Execute",
  "Trade Now",
  "Order",
  "Place Order",
  "지금 사라",
  "지금 팔아라",
  "매수 버튼",
  "매도 버튼",
] as const;

const FIXTURE_SNAPSHOT_PATHS = new Set([
  "/api/control-room",
  "/api/market-kernel",
  "/api/analysis-workspace",
  "/api/symbol-lab",
  "/api/risk-firewall",
  "/api/mission-control",
  "/api/news-intelligence",
  "/api/event-radar",
  "/api/trade-memory",
  "/api/quant-lab",
  "/api/system-ops",
]);

export async function forceFixtureSnapshotApis(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === "GET" && FIXTURE_SNAPSHOT_PATHS.has(url.pathname)) {
      await route.continue({
        headers: {
          ...request.headers(),
          "X-FSO-Use-Fixture": "1",
        },
      });
      return;
    }

    await route.continue();
  });
}

export async function gotoControlRoom(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForSelector('[data-testid="control-room-grid"]');
}
