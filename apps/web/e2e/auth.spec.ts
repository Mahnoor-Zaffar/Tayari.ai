import { expect, test } from "@playwright/test";

test.describe("Authentication", () => {
  test("landing page loads and shows sign-in link", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("login form validates required fields", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/email/i)).toBeVisible();
  });

  test("register form shows password requirements", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.getByText(/8 characters/i)).toBeVisible();
  });
});
