import { test, expect } from '@playwright/test';

const APP_URL = 'https://sorce-web.onrender.com';
const API_URL = 'https://sorce-api.onrender.com';

test.describe('Production Verification', () => {
  test('Frontend is live and loads homepage', async ({ page }) => {
    await page.goto(APP_URL);
    
    // Check for a key marketing element (updated for Skedaddle/Sorce branding)
    await expect(page.locator('text=Ready to skedaddle?')).toBeVisible();
    
    // Check for "Start applying free" button
    const ctaBtn = page.locator('button:has-text("Start free — 10 applications on us")');
    await expect(ctaBtn).toBeVisible();
  });

  test('Backend health check', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  test('API documentation is accessible', async ({ page }) => {
    await page.goto(`${API_URL}/docs`);
    // Updated for specific title found in logs
    await expect(page.locator('.title')).toContainText('Sorce API');
  });
});
