import { expect, test } from "@playwright/test";
import { gotoControlRoom } from "./_helpers";

test.describe("OS theme switching", () => {
  test("cycles material → cyber → light → material", async ({ page }) => {
    await gotoControlRoom(page);
    const root = page.locator("html");
    await expect(root).toHaveAttribute("data-theme", "material");

    const toggle = page.getByTestId("theme-toggle");
    await toggle.click();
    await expect(root).toHaveAttribute("data-theme", "cyber");

    await toggle.click();
    await expect(root).toHaveAttribute("data-theme", "light");

    await toggle.click();
    await expect(root).toHaveAttribute("data-theme", "material");
  });

  test("command palette opens via Ctrl+K and Cmd+K hotkeys", async ({ page }) => {
    await gotoControlRoom(page);

    await page.getByTestId("open-command-palette").click();
    const palette = page.getByTestId("command-palette");
    await expect(palette).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(palette).toBeHidden();

    await page.keyboard.press("Control+K");
    await expect(palette).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(palette).toBeHidden();

    await page.keyboard.press("Meta+K");
    await expect(palette).toBeVisible();
  });

  test("command palette navigates to Analysis Workspace", async ({ page }) => {
    await gotoControlRoom(page);
    await page.keyboard.press("Control+K");
    await page.getByTestId("command-palette-input").fill("Analysis");
    await page.getByTestId("command-item-analysis").click();
    await expect(page).toHaveURL(/\/analysis-workspace$/);
    await expect(page.getByTestId("analysis-workspace-page")).toBeVisible();
  });

  test("command palette never lists execution actions", async ({ page }) => {
    await gotoControlRoom(page);
    await page.keyboard.press("Control+K");
    const palette = page.getByTestId("command-palette");
    const text = await palette.innerText();
    for (const forbidden of [
      "Buy",
      "Sell",
      "Execute",
      "Trade Now",
      "Order",
      "Place Order",
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });
});
