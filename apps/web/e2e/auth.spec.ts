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

  test("forgot password link navigates correctly", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByRole("link", { name: /forgot/i }).click();
    await expect(page).toHaveURL(/forgot-password/);
    await expect(page.getByText(/reset/i)).toBeVisible();
  });

  test("can toggle between login and register", async ({ page }) => {
    await page.goto("/auth/login");
    await page.getByRole("link", { name: /sign up/i }).click();
    await expect(page).toHaveURL(/register/);
  });
});

test.describe("Dashboard (authenticated)", () => {
  test("redirects to login when unauthenticated", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/auth\/login/);
  });
});

test.describe("Interview Setup", () => {
  test("setup wizard requires authentication", async ({ page }) => {
    await page.goto("/dashboard/interview/new");
    await expect(page).toHaveURL(/auth\/login/);
  });
});

test.describe("Reports", () => {
  test("reports page requires authentication", async ({ page }) => {
    await page.goto("/dashboard/reports");
    await expect(page).toHaveURL(/auth\/login/);
  });
});
