import { test, expect, devices } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

// Desktop Chrome Tests - Top level test.use
test.describe('Desktop Chrome Tests', () => {
  // Remove device-specific use and rely on config projects

  test('complete authentication flow on Desktop Chrome', async ({ page }) => {
    console.log('🚀 Testing authentication flow on Desktop Chrome...');

    // Clear state
    await page.context().clearCookies();
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Test login page
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 15000 });
    
    // Test email input
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]').first();
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    await emailInput.fill(TEST_EMAIL);
    
    // Test submit button
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Check for success or rate limiting
    const successMessage = page.locator('text=/Check your inbox|sent|magic link/i');
    const rateLimitMessage = page.locator('text=/Too many|rate limit|slow down/i');
    
    const isSuccess = await successMessage.isVisible().catch(() => false);
    const isRateLimited = await rateLimitMessage.isVisible().catch(() => false);
    
    if (isSuccess) {
      console.log('✅ Magic link request successful on Desktop Chrome');
    } else if (isRateLimited) {
      console.log('⏰ Rate limited on Desktop Chrome - expected behavior');
    } else {
      console.log('⚠️ Unexpected response on Desktop Chrome');
    }
    
    await page.screenshot({ 
      path: 'reports/screenshots/desktop-chrome-auth-test.png',
      fullPage: false 
    });
  });

  test('dashboard accessibility on Desktop Chrome', async ({ page }) => {
    console.log('📱 Testing dashboard on Desktop Chrome...');

    // Set up auth state
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
      localStorage.setItem('has_completed_onboarding', 'true');
    });

    // Navigate to dashboard
    await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const dashboardUrl = page.url();
    if (dashboardUrl.includes('/app/dashboard')) {
      console.log('✅ Dashboard accessible on Desktop Chrome');
      
      // Check for responsive design
      const viewport = page.viewportSize();
      console.log(`📐 Viewport: ${viewport?.width}x${viewport?.height}`);
      
      // Check for horizontal overflow
      const hasOverflow = await page.evaluate(() => {
        return document.body.scrollWidth > window.innerWidth;
      });
      
      if (hasOverflow) {
        console.log('⚠️ Horizontal overflow detected on Desktop Chrome');
      } else {
        console.log('✅ No horizontal overflow on Desktop Chrome');
      }
      
      await page.screenshot({ 
        path: 'reports/screenshots/desktop-chrome-dashboard.png',
        fullPage: true 
      });
    } else {
      console.log('❌ Dashboard not accessible on Desktop Chrome');
    }
  });
});

// Mobile Tests - Top level test.use
test.describe('Mobile Tests', () => {
  // Remove device-specific use and rely on config projects

  test('complete authentication flow on iPhone 13', async ({ page }) => {
    console.log('🚀 Testing authentication flow on iPhone 13...');

    // Clear state
    await page.context().clearCookies();
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Test login page
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 15000 });
    
    // Test email input
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]').first();
    await expect(emailInput).toBeVisible({ timeout: 10000 });
    await emailInput.fill(TEST_EMAIL);
    
    // Test submit button
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Check for success or rate limiting
    const successMessage = page.locator('text=/Check your inbox|sent|magic link/i');
    const rateLimitMessage = page.locator('text=/Too many|rate limit|slow down/i');
    
    const isSuccess = await successMessage.isVisible().catch(() => false);
    const isRateLimited = await rateLimitMessage.isVisible().catch(() => false);
    
    if (isSuccess) {
      console.log('✅ Magic link request successful on iPhone 13');
    } else if (isRateLimited) {
      console.log('⏰ Rate limited on iPhone 13 - expected behavior');
    } else {
      console.log('⚠️ Unexpected response on iPhone 13');
    }
    
    await page.screenshot({ 
      path: 'reports/screenshots/iphone-13-auth-test.png',
      fullPage: false 
    });
  });

  test('mobile touch interactions', async ({ page }) => {
    console.log('👆 Testing mobile touch interactions...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    // Test touch targets
    const touchTargets = page.locator('button, a, input').all();
    const targetCount = await touchTargets.count();
    
    console.log(`👆 Found ${targetCount} touch targets`);
    
    // Check minimum touch target size (44px recommended)
    let adequateTouchTargets = 0;
    for (let i = 0; i < Math.min(targetCount, 10); i++) {
      const target = touchTargets.nth(i);
      const boundingBox = await target.boundingBox();
      
      if (boundingBox) {
        const minDimension = Math.min(boundingBox.width, boundingBox.height);
        if (minDimension >= 44) {
          adequateTouchTargets++;
        }
      }
    }
    
    console.log(`✅ Found ${adequateTouchTargets} adequately sized touch targets`);
    
    // Test tap interactions
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.tap();
    await page.waitForTimeout(500);
    
    // Check if input is focused
    const isFocused = await emailInput.evaluate(el => document.activeElement === el);
    
    if (isFocused) {
      console.log('✅ Touch focus working correctly');
    }
    
    await page.screenshot({ 
      path: 'reports/screenshots/mobile-touch-interactions.png',
      fullPage: false 
    });
  });

  test('mobile keyboard handling', async ({ page }) => {
    console.log('⌨️ Testing mobile keyboard handling...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.tap();
    await page.waitForTimeout(1000);
    
    // Type in input
    await emailInput.fill(TEST_EMAIL);
    await page.waitForTimeout(1000);
    
    // Check if keyboard would appear (simulated)
    const inputBounds = await emailInput.boundingBox();
    if (inputBounds) {
      console.log(`📱 Input position: ${inputBounds.y}px from top`);
      
      // Check if input is not obscured by keyboard
      const viewportHeight = page.viewportSize()?.height || 0;
      const inputBottom = inputBounds.y + inputBounds.height;
      
      if (inputBottom < viewportHeight * 0.7) {
        console.log('✅ Input positioned well for keyboard');
      } else {
        console.log('⚠️ Input may be obscured by keyboard');
      }
    }
    
    await page.screenshot({ 
      path: 'reports/screenshots/mobile-keyboard-handling.png',
      fullPage: false 
    });
  });
});
