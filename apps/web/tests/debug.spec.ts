import { test, expect } from '@playwright/test';

test('Debug Login Page', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.screenshot({ path: 'login-page.png' });
});
