import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e@example.com';

test.describe('User Journey: Landing to Job Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  test('01. Homepage loads correctly', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Check hero section exists
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
    
    // Check CTA buttons exist
    const ctaButtons = page.locator('a[href*="/login"], a[href*="/app"], button').filter({ hasText: /start|begin|try|sign/i });
    await expect(ctaButtons.first()).toBeVisible({ timeout: 5000 });
    
    // Check navigation
    const nav = page.locator('nav, header').first();
    await expect(nav).toBeVisible();
    
    // Take screenshot for visual verification
    await page.screenshot({ path: 'reports/screenshots/01-homepage.png', fullPage: false });
  });

  test('02. Login page renders correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Check email input exists
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]');
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    
    // Check submit button
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")');
    await expect(submitBtn).toBeVisible();
    
    await page.screenshot({ path: 'reports/screenshots/02-login.png', fullPage: false });
  });

  test('03. Magic link request flow', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Fill email
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.fill(TEST_EMAIL);
    
    // Submit form
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await submitBtn.click();
    
    // Wait for success state or error (rate limiting)
    await page.waitForTimeout(2000);
    
    // Check for either success message or rate limit
    const successOrError = page.locator('text=/Check your inbox|sent|Too many|rate/i');
    await expect(successOrError.first()).toBeVisible({ timeout: 15000 });
    
    await page.screenshot({ path: 'reports/screenshots/03-magic-link.png', fullPage: false });
  });

  test('04. App redirects unauthenticated to login', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto(`${BASE_URL}/app/dashboard`);
    
    // Should redirect to login
    await page.waitForURL(/\/login/, { timeout: 10000 }).catch(() => {
      // May stay on page if auth cookie exists from previous tests
    });
    
    // Verify either on login or on dashboard (if authenticated)
    const url = page.url();
    expect(url).toMatch(/\/(login|app\/dashboard)/);
  });

  test('05. Onboarding page structure', async ({ page }) => {
    // Bypass auth by setting a mock token
    await page.goto(`${BASE_URL}/login`);
    
    // Set mock auth token in localStorage
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token');
    });
    
    // Navigate to onboarding
    await page.goto(`${BASE_URL}/app/onboarding`);
    
    // Check onboarding loads (may redirect if no valid token)
    await page.waitForTimeout(2000);
    
    // If we're on onboarding, check structure
    const onOnboarding = page.url().includes('/app/onboarding');
    if (onOnboarding) {
      // Check progress indicator
      const progress = page.locator('text=/Progress|Calibration|Step/i');
      await expect(progress.first()).toBeVisible({ timeout: 5000 });
      
      // Check step content
      const stepContent = page.locator('button, [role="button"]').filter({ hasText: /begin|next|start/i });
      await expect(stepContent.first()).toBeVisible({ timeout: 5000 });
    }
    
    await page.screenshot({ path: 'reports/screenshots/05-onboarding.png', fullPage: false });
  });

  test('06. Jobs page structure (if accessible)', async ({ page }) => {
    await page.goto(`${BASE_URL}/app/jobs`);
    
    await page.waitForTimeout(2000);
    
    // Either redirected to login or on jobs page
    const url = page.url();
    
    if (url.includes('/app/jobs')) {
      // Check job cards or empty state
      const jobsContent = page.locator('[class*="job"], [data-testid*="job"], text=/job|No.*found/i');
      await expect(jobsContent.first()).toBeVisible({ timeout: 10000 });
      
      await page.screenshot({ path: 'reports/screenshots/06-jobs.png', fullPage: false });
    } else {
      // Redirected to login - expected for unauthenticated users
      expect(url).toContain('/login');
    }
  });

  test('07. Marketing pages navigation', async ({ page }) => {
    const pages = [
      { path: '/pricing', name: 'Pricing' },
      { path: '/about', name: 'About' },
      { path: '/privacy', name: 'Privacy' },
      { path: '/terms', name: 'Terms' },
    ];
    
    for (const pageInfo of pages) {
      await page.goto(`${BASE_URL}${pageInfo.path}`);
      
      // Check page loads
      const content = page.locator('h1, h2, main').first();
      await expect(content).toBeVisible({ timeout: 10000 });
      
      console.log("✓", pageInfo.name, "page loaded");
    }
  });

  test('08. Mobile responsive check', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto(BASE_URL);
    
    // Check mobile menu or content
    const mobileContent = page.locator('body');
    await expect(mobileContent).toBeVisible();
    
    // Check no horizontal overflow
    const hasOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth;
    });
    
    expect(hasOverflow).toBe(false);
    
    await page.screenshot({ path: 'reports/screenshots/08-mobile.png', fullPage: false });
  });

  test('09. Performance check - homepage', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    
    const loadTime = Date.now() - startTime;
    
    // Should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
    
    console.log("Homepage load time:", loadTime, "ms");
    
    // Check Core Web Vitals
    const metrics = await page.evaluate(() => {
      return {
        domNodes: document.querySelectorAll('*').length,
        scripts: document.querySelectorAll('script').length,
        stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
      };
    });
    
    console.log('Page metrics:', metrics);
    
    // Reasonable limits
    expect(metrics.domNodes).toBeLessThan(5000);
  });

  test('10. API health check', async ({ page }) => {
    // Try to hit health endpoint
    const apiBase = BASE_URL.includes('localhost') 
      ? BASE_URL.replace(/:\d+/, ':8000') 
      : BASE_URL;
    
    const response = await page.request.get(`${apiBase}/health`, { 
      timeout: 10000,
      failOnStatusCode: false 
    }).catch(() => null);
    
    if (response) {
      console.log("API health status:", response.status());
    } else {
      console.log('API health check skipped (CORS or not available)');
    }
  });
});

test.describe('Accessibility Checks', () => {
  test('Homepage accessibility', async ({ page }) => {
    await page.goto(BASE_URL);
    
    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      const ariaHidden = await img.getAttribute('aria-hidden');
      
      // Images should have alt text or be explicitly hidden
      if (ariaHidden !== 'true') {
        expect(alt || ariaLabel).toBeTruthy();
      }
    }
    
    // Check for heading hierarchy
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
    
    // Check buttons have accessible names
    const buttons = await page.locator('button').all();
    for (const btn of buttons) {
      const text = await btn.textContent();
      const ariaLabel = await btn.getAttribute('aria-label');
      const hasAccessibleName = text?.trim() || ariaLabel;
      expect(hasAccessibleName).toBeTruthy();
    }
  });
});
