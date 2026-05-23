import { expect, test } from "@playwright/test";

test.describe("Slice 13.11 — shared JudgmentHeader", () => {
  test("renders eyebrow, accent text, and numeric confidence", async ({ page }) => {
    await page.goto("/");

    const header = page.getByTestId("judgment-header");
    await expect(header).toBeVisible();
    await expect(header).toContainText("GLOBAL OPERATING VERDICT");
    await expect(header).toContainText("Extended");
    await expect(header).toContainText("72%");
  });

  test("carries resolved symbol vocabulary on Symbol Lab", async ({ page }) => {
    await page.goto("/symbol-lab?ticker=TSLA");

    const header = page.getByTestId("judgment-header");
    await expect(header).toContainText("SYMBOL JUDGMENT · TSLA");
    await expect(header).toContainText("Constrained");
  });
});

