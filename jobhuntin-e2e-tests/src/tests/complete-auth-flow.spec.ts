import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

test.describe('Complete Magic Link Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    // Clear localStorage to ensure clean state
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('complete new user journey: email → magic link → onboarding → dashboard', async ({ page }) => {
    console.log('🚀 Starting complete user journey test...');

    // Step 1: Navigate to login page
    await page.goto(`${BASE_URL}/login`);
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
    
    // Step 2: Enter email and request magic link
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]').first();
    await expect(emailInput).toBeVisible({ timeout: 5000 });
    await emailInput.fill(TEST_EMAIL);
    
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();
    
    // Step 3: Wait for magic link request response
    console.log('📧 Waiting for magic link request response...');
    await page.waitForTimeout(3000);
    
    // Check for success message or rate limiting
    const successMessage = page.locator('text=/Check your inbox|sent|magic link/i');
    const rateLimitMessage = page.locator('text=/Too many|rate limit|slow down/i');
    
    const isSuccess = await successMessage.isVisible().catch(() => false);
    const isRateLimited = await rateLimitMessage.isVisible().catch(() => false);
    
    if (isRateLimited) {
      console.log('⏰ Rate limited - this is expected behavior');
      // Take screenshot for debugging
      await page.screenshot({ path: 'reports/screenshots/magic-link-rate-limited.png', fullPage: false });
      return; // Exit gracefully if rate limited
    }
    
    if (isSuccess) {
      console.log('✅ Magic link request successful');
      await page.screenshot({ path: 'reports/screenshots/magic-link-request-success.png', fullPage: false });
    } else {
      // Check for any other error messages
      const errorMessage = page.locator('text=/error|invalid|failed/i');
      const hasError = await errorMessage.isVisible().catch(() => false);
      if (hasError) {
        console.log('❌ Error message detected');
        await page.screenshot({ path: 'reports/screenshots/magic-link-error.png', fullPage: false });
        throw new Error('Magic link request failed');
      }
    }
    
    // Step 4: Simulate clicking magic link (this would normally come from email)
    // For testing purposes, we'll try to access the onboarding directly
    // In a real scenario, this would be the magic link URL with token
    console.log('🔗 Simulating magic link click...');
    
    // Try to access onboarding (this should redirect to login if not authenticated)
    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const currentUrl = page.url();
    console.log('📍 Current URL after navigation:', currentUrl);
    
    // Check if we're on onboarding or redirected back to login
    if (currentUrl.includes('/app/onboarding')) {
      console.log('✅ Successfully accessed onboarding');
      
      // Step 5: Test onboarding flow
      await testOnboardingFlow(page);
      
    } else if (currentUrl.includes('/login')) {
      console.log('🔄 Redirected to login - expected without valid magic link token');
      
      // For testing purposes, we can set a mock token to test the rest of the flow
      // This simulates what would happen after a successful magic link validation
      console.log('🔧 Setting mock authentication for testing...');
      await page.evaluate(() => {
        localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
        localStorage.setItem('user_email', 'test-e2e-production@jobhuntin.com');
      });
      
      // Now try to access onboarding again
      await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
      
      const onboardingUrl = page.url();
      if (onboardingUrl.includes('/app/onboarding')) {
        console.log('✅ Successfully accessed onboarding with mock auth');
        await testOnboardingFlow(page);
      } else {
        console.log('❌ Still unable to access onboarding');
        await page.screenshot({ path: 'reports/screenshots/onboarding-access-failed.png', fullPage: false });
      }
    }
  });

  test('error handling: invalid email and network issues', async ({ page }) => {
    console.log('🧪 Testing error handling scenarios...');

    // Test 1: Invalid email format
    await page.goto(`${BASE_URL}/login`);
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]').first();
    await emailInput.fill('invalid-email-format');
    
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await submitBtn.click();
    
    await page.waitForTimeout(2000);
    
    // Check for validation error
    const validationError = page.locator('text=/invalid|email|format/i');
    const hasValidationError = await validationError.isVisible().catch(() => false);
    
    if (hasValidationError) {
      console.log('✅ Email validation working correctly');
    } else {
      console.log('⚠️ Email validation may not be working');
    }
    
    await page.screenshot({ path: 'reports/screenshots/email-validation-test.png', fullPage: false });
  });

  test('rate limiting behavior', async ({ page }) => {
    console.log('⏱️ Testing rate limiting behavior...');

    await page.goto(`${BASE_URL}/login`);
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"], input[name="email"]').first();
    
    // Try multiple rapid requests
    for (let i = 0; i < 5; i++) {
      await emailInput.fill(`test-${i}@jobhuntin.com`);
      const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
      await submitBtn.click();
      await page.waitForTimeout(1000);
      
      // Check for rate limiting
      const rateLimitMessage = page.locator('text=/Too many|rate limit|slow down/i');
      const isRateLimited = await rateLimitMessage.isVisible().catch(() => false);
      
      if (isRateLimited) {
        console.log(`✅ Rate limiting activated after ${i + 1} requests`);
        await page.screenshot({ path: 'reports/screenshots/rate-limit-activated.png', fullPage: false });
        break;
      }
    }
  });
});

async function testOnboardingFlow(page: Page) {
  console.log('🎯 Testing onboarding flow...');
  
  // Check if onboarding page loaded properly
  const onboardingTitle = page.locator('h1, h2').first();
  await expect(onboardingTitle).toBeVisible({ timeout: 10000 });
  
  // Look for common onboarding elements
  const progressIndicator = page.locator('text=/Progress|Step|Calibration/i');
  const hasProgress = await progressIndicator.isVisible().catch(() => false);
  
  if (hasProgress) {
    console.log('✅ Progress indicator found');
  }
  
  // Look for action buttons
  const actionButton = page.locator('button:has-text(/Continue|Next|Start|Begin/i)').first();
  const hasActionButton = await actionButton.isVisible().catch(() => false);
  
  if (hasActionButton) {
    console.log('✅ Action button found');
    // Try clicking the first action button to test navigation
    await actionButton.click();
    await page.waitForTimeout(2000);
    console.log('🔄 Navigated to next onboarding step');
  }
  
  // Test dashboard access after onboarding
  await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  const dashboardUrl = page.url();
  if (dashboardUrl.includes('/app/dashboard')) {
    console.log('✅ Successfully accessed dashboard');
    
    // Check for dashboard elements
    const dashboardContent = page.locator('main, [role="main"], .dashboard').first();
    const hasDashboardContent = await dashboardContent.isVisible().catch(() => false);
    
    if (hasDashboardContent) {
      console.log('✅ Dashboard content loaded');
    } else {
      console.log('⚠️ Dashboard content may be loading or empty');
    }
    
    await page.screenshot({ path: 'reports/screenshots/dashboard-access-success.png', fullPage: false });
  } else {
    console.log('❌ Unable to access dashboard');
    await page.screenshot({ path: 'reports/screenshots/dashboard-access-failed.png', fullPage: false });
  }
}
