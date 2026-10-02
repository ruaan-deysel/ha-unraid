import { expect, test } from "@playwright/test";

test.describe("Unraid Lovelace Dashboard Cards Browser Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/browser/fixture.html");
    await page.waitForFunction(
      () => (window as unknown as { fixtureReady?: boolean }).fixtureReady === true
    );
  });

  test("defines all custom card elements without template corruption", async ({ page }) => {
    const defined = await page.evaluate(() => {
      const tags = [
        "unraid-server-card",
        "unraid-storage-card",
        "unraid-shares-card",
        "unraid-docker-card",
        "unraid-ups-card",
        "unraid-vm-card",
        "unraid-network-card",
        "unraid-dashboard-card",
      ];
      return tags.every((t) => Boolean(customElements.get(t)));
    });
    expect(defined).toBe(true);

    // Verify NO raw Lit placeholder markers or leaked attribute syntax exist in DOM
    const rawLitMarkers = await page.evaluate(() => {
      const allText = document.body.innerText;
      return allText.includes("lit$") || allText.includes("@click=") || allText.includes(".style=");
    });
    expect(rawLitMarkers).toBe(false);
  });

  test("renders Server Card with system metrics", async ({ page }) => {
    const serverCard = page.locator("#server-card");
    await expect(serverCard).toBeVisible();

    await expect(serverCard.getByText("Cube")).toBeVisible();
    await expect(serverCard.getByText("CPU Load")).toBeVisible();
    await expect(serverCard.getByText("15%")).toBeVisible();
    await expect(serverCard.getByText("Memory")).toBeVisible();
    await expect(serverCard.getByText("System Uptime")).toBeVisible();
    await expect(serverCard.getByText("Primary Network")).toBeVisible();
    await expect(serverCard.getByText("Boot Device")).toBeVisible();
    await expect(serverCard.getByText(/Flash/)).toBeVisible();
  });

  test("renders Storage Card with clean disk names and Healthy status badges", async ({ page }) => {
    const storageCard = page.locator("#storage-card");
    await expect(storageCard).toBeVisible();

    await expect(storageCard.getByText("Storage Array & Disks")).toBeVisible();
    await expect(storageCard.getByText("Parity", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Disk 1", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Cache", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Flash (Boot)", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Healthy").first()).toBeVisible();
    await expect(storageCard.getByText("--").first()).toBeVisible();
    await expect(storageCard.getByText("29°C")).toBeVisible();
  });

  test("renders Shares Card with user shares and protection states", async ({ page }) => {
    const sharesCard = page.locator("#shares-card");
    await expect(sharesCard).toBeVisible();

    await expect(sharesCard.getByText("User Shares")).toBeVisible();
    await expect(sharesCard.getByText("appdata")).toBeVisible();
    await expect(sharesCard.getByText("media")).toBeVisible();
    await expect(sharesCard.getByText("Protected").first()).toBeVisible();
    await expect(sharesCard.getByText("Unprotected").first()).toBeVisible();
    await expect(sharesCard.getByText("46.6 GB / 480.6 GB")).toBeVisible();
    await expect(sharesCard.getByText("1.4 TB / 39.1 TB")).toBeVisible();
  });

  test("renders Network Card with interfaces and link metrics", async ({ page }) => {
    const networkCard = page.locator("#network-card");
    await expect(networkCard).toBeVisible();

    await expect(networkCard.getByText("Cube Network")).toBeVisible();
    await expect(networkCard.getByText("ETH0")).toBeVisible();
    await expect(networkCard.getByText("192.168.20.21", { exact: true }).first()).toBeVisible();
    await expect(networkCard.getByText("1 Gbps")).toBeVisible();
    await expect(networkCard.getByText("12.40 MB/s")).toBeVisible();
    await expect(networkCard.getByText("5.80 MB/s")).toBeVisible();
  });

  test("renders Dashboard Card and allows tab navigation", async ({ page }) => {
    const dashboardCard = page.locator("unraid-dashboard-card");
    await expect(dashboardCard).toBeVisible();

    // Default overview tab
    await expect(dashboardCard.locator("unraid-server-card")).toBeVisible();

    // Click Shares tab
    await dashboardCard.locator(".tab-btn:has-text('Shares')").click();
    await expect(dashboardCard.locator("unraid-shares-card")).toBeVisible();

    // Click Network tab
    await dashboardCard.locator(".tab-btn:has-text('Network')").click();
    await expect(dashboardCard.locator("unraid-network-card")).toBeVisible();

    // Click Storage tab
    await dashboardCard.locator(".tab-btn:has-text('Storage & Disks')").click();
    await expect(dashboardCard.locator("unraid-storage-card")).toBeVisible();
  });
});
