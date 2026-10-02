import { defineConfig } from "@playwright/test";

const port = Number(process.env.BROWSER_TEST_PORT ?? 4173);
const host = process.env.BROWSER_TEST_HOST ?? "127.0.0.1";

export default defineConfig({
  testDir: "test/browser",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  failOnFlakyTests: Boolean(process.env.CI),
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://${host}:${port}`,
    browserName: "chromium",
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: process.env.BROWSER_TEST_EXTERNAL_SERVER
    ? undefined
    : {
        command: "node test/browser/server.mjs",
        url: `http://${host}:${port}/test/browser/fixture.html`,
        reuseExistingServer: false,
      },
});
