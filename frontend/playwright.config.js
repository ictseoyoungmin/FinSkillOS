import { defineConfig, devices } from "@playwright/test";
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173";
const useExternalServer = !!process.env.PLAYWRIGHT_BASE_URL;
export default defineConfig({
    testDir: "./e2e",
    // `_debug/` holds one-off screenshot specs used while iterating on
    // layout bugs (Slice 13.7 right-column clipping fix). They depend on
    // a live Docker stack and a specific viewport so they should never
    // run as part of the regular structural / visual suite.
    testIgnore: ["**/_debug/**"],
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    reporter: [["list"], ["html", { open: "never" }]],
    use: {
        baseURL,
        trace: "retain-on-failure",
        screenshot: "only-on-failure",
    },
    expect: {
        toHaveScreenshot: {
            maxDiffPixelRatio: 0.03,
            animations: "disabled",
        },
    },
    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
        },
    ],
    webServer: useExternalServer
        ? undefined
        : {
            command: "npm run dev",
            url: baseURL,
            reuseExistingServer: !process.env.CI,
            stdout: "pipe",
            stderr: "pipe",
            timeout: 120_000,
        },
});
