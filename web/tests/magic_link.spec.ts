import { test, expect } from '@playwright/test';

test.describe('Magic Link Authentication', () => {
  
  test.beforeEach(async ({ page }) => {
    // Increase timeout for initial load
    await page.goto('/login', { timeout: 60000 });
  });

  test('should send magic link successfully', async ({ page }) => {
    const email = 'test-user@example.com';
    
    // Intercept Supabase request - broaden pattern to catch any auth request
    await page.route('**/auth/v1/**', async route => {
      console.log('Intercepted:', route.request().url());
      const request = route.request();
      
      if (request.method() === 'POST' && request.url().includes('otp')) {
        const postData = request.postDataJSON();
        // Verify payload
        expect(postData.email).toBe(email);
        expect(postData.options.emailRedirectTo).toContain('/login?returnTo=');
        
        // Mock success response
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ error: null, data: {} })
        });
        return;
      }
      
      // Pass through other requests
      await route.continue();
    });

    // Fill email and submit
    await page.getByPlaceholder('tech-wizard@example.com').fill(email);
    await page.getByRole('button', { name: 'Send Magic Link' }).click();

    // Verify success state
    await expect(page.getByText('Check your email')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(email)).toBeVisible();
    await expect(page.getByText('Start your JobHuntin run')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    const email = 'error-user@example.com';
    
    // Intercept Supabase request with error
    await page.route('**/auth/v1/**', async route => {
      const request = route.request();
      if (request.method() === 'POST' && request.url().includes('otp')) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ 
            error: 'invalid_request',
            message: 'Unable to send magic link' 
          }) 
        });
        return;
      }
      await route.continue();
    });

    // Fill email and submit
    await page.getByPlaceholder('tech-wizard@example.com').fill(email);
    await page.getByRole('button', { name: 'Send Magic Link' }).click();

    // Verify error message
    // Note: The app might show "Invalid API key" if it hits the real backend due to race condition or missing intercept.
    // We expect "Unable to send magic link" from our mock.
    await expect(page.getByRole('alert')).toContainText('Unable to send magic link');
  });

  test('should validate email format', async ({ page }) => {
    await page.getByPlaceholder('tech-wizard@example.com').fill('invalid-email');
    
    // Button should be disabled
    await expect(page.getByRole('button', { name: 'Send Magic Link' })).toBeDisabled();
  });
});
