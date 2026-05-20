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

export async function gotoControlRoom(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForSelector('[data-testid="control-room-grid"]');
}
