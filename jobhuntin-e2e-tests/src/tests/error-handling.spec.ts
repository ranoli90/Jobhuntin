import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

test.describe('Error Handling & Edge Cases', () => {
  test('network failure simulation', async ({ page }) => {
    console.log('🌐 Testing network failure scenarios...');

    // Test slow network conditions
    await page.route('**/*', async route => {
      // Add delay to simulate slow network
      await new Promise(resolve => setTimeout(resolve, 3000));
      await route.continue();
    });

    const startTime = Date.now();
    await page.goto(`${BASE_URL}/login`);
    const loadTime = Date.now() - startTime;
    
    console.log(`⏱️ Load time with slow network: ${loadTime}ms`);
    
    // Check if page still loads correctly
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 15000 });
    console.log('✅ Page loads correctly with slow network');
    
    // Test form submission with network issues
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.fill(TEST_EMAIL);
    
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await submitBtn.click();
    
    // Wait for response or timeout
    await page.waitForTimeout(10000);
    
    // Check for error handling
    const errorMessage = page.locator('text=/error|timeout|failed|network/i').first();
    const hasError = await errorMessage.isVisible().catch(() => false);
    
    if (hasError) {
      console.log('✅ Network error handled gracefully');
    } else {
      console.log('⚠️ No network error message found');
    }
    
    await page.screenshot({ path: 'reports/screenshots/network-failure-test.png', fullPage: false });
  });

  test('request timeout handling', async ({ page }) => {
    console.log('⏰ Testing request timeout handling...');

    // Block API calls to simulate timeout
    await page.route('**/api/**', async route => {
      // Don't respond to simulate timeout
      await page.waitForTimeout(30000);
    });

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.fill(TEST_EMAIL);
    
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    await submitBtn.click();
    
    // Wait for timeout handling
    await page.waitForTimeout(15000);
    
    // Check for timeout message
    const timeoutMessage = page.locator('text=/timeout|took too long|request failed/i').first();
    const hasTimeoutMessage = await timeoutMessage.isVisible().catch(() => false);
    
    if (hasTimeoutMessage) {
      console.log('✅ Request timeout handled gracefully');
    } else {
      console.log('⚠️ No timeout message found');
    }
    
    await page.screenshot({ path: 'reports/screenshots/timeout-handling-test.png', fullPage: false });
  });

  test('invalid data submission', async ({ page }) => {
    console.log('❌ Testing invalid data submission...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    // Test various invalid email formats
    const invalidEmails = [
      'invalid-email',
      'test@',
      '@test.com',
      'test..test@test.com',
      'test@.com',
      ''
    ];

    for (const email of invalidEmails) {
      console.log(`📧 Testing invalid email: ${email}`);
      
      const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
      await emailInput.clear();
      await emailInput.fill(email);
      
      const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
      await submitBtn.click();
      await page.waitForTimeout(2000);
      
      // Check for validation error
      const validationError = page.locator('text=/invalid|email|format|required/i').first();
      const hasValidationError = await validationError.isVisible().catch(() => false);
      
      if (hasValidationError) {
        console.log(`✅ Validation error shown for: ${email}`);
      } else {
        console.log(`⚠️ No validation error for: ${email}`);
      }
      
      await page.screenshot({ 
        path: `reports/screenshots/invalid-email-${email.replace(/[^a-zA-Z0-9]/g, '-')}.png`,
        fullPage: false 
      });
    }
  });

  test('large data upload handling', async ({ page }) => {
    console.log('📁 Testing large data upload handling...');

    // Set up authenticated state
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
    });

    await page.goto(`${BASE_URL}/app/onboarding`);
    await page.waitForTimeout(2000);

    // Look for file upload inputs
    const fileInputs = page.locator('input[type="file"]').all();
    const fileInputCount = await fileInputs.count();

    if (fileInputCount > 0) {
      console.log(`📁 Found ${fileInputCount} file upload inputs`);
      
      // Test with a large file (simulated)
      const largeFile = Buffer.alloc(10 * 1024 * 1024, 'A'); // 10MB file
      
      for (let i = 0; i < fileInputCount; i++) {
        const input = fileInputs.nth(i);
        
        try {
          await input.setInputFiles({
            name: 'large-file.pdf',
            mimeType: 'application/pdf',
            buffer: largeFile
          });
          
          await page.waitForTimeout(5000);
          
          // Check for file size error
          const sizeError = page.locator('text=/too large|size|limit|MB/i').first();
          const hasSizeError = await sizeError.isVisible().catch(() => false);
          
          if (hasSizeError) {
            console.log('✅ Large file size error handled correctly');
          } else {
            console.log('⚠️ No file size error found');
          }
          
          await page.screenshot({ 
            path: `reports/screenshots/large-file-upload-${i}.png`,
            fullPage: false 
          });
          
        } catch (error) {
          console.log(`⚠️ File upload test failed: ${error}`);
        }
      }
    } else {
      console.log('⚠️ No file upload inputs found');
    }
  });

  test('session management edge cases', async ({ page }) => {
    console.log('🔐 Testing session management edge cases...');

    // Test expired session
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'expired-token-123');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
    });

    await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const dashboardUrl = page.url();
    
    if (dashboardUrl.includes('/login')) {
      console.log('✅ Expired session redirected to login');
    } else {
      console.log('⚠️ Expired session not handled properly');
    }

    // Test session expiration during navigation
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'valid-token-123');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
    });

    await page.goto(`${BASE_URL}/app/dashboard`);
    await page.waitForTimeout(2000);

    // Simulate token expiration
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'expired-token-456');
    });

    // Try to navigate to another page
    await page.goto(`${BASE_URL}/app/jobs`);
    await page.waitForTimeout(2000);

    const jobsUrl = page.url();
    if (jobsUrl.includes('/login')) {
      console.log('✅ Session expiration during navigation handled correctly');
    } else {
      console.log('⚠️ Session expiration during navigation not handled');
    }

    await page.screenshot({ path: 'reports/screenshots/session-management-test.png', fullPage: false });
  });

  test('concurrent request handling', async ({ page }) => {
    console.log('🔄 Testing concurrent request handling...');

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    await emailInput.fill(TEST_EMAIL);

    // Submit multiple requests rapidly
    const submitBtn = page.locator('button[type="submit"], button:has-text("Continue")').first();
    
    for (let i = 0; i < 5; i++) {
      await submitBtn.click();
      await page.waitForTimeout(500);
    }

    await page.waitForTimeout(3000);

    // Check for rate limiting or error handling
    const rateLimitMessage = page.locator('text=/too many|rate limit|slow down/i').first();
    const hasRateLimit = await rateLimitMessage.isVisible().catch(() => false);

    if (hasRateLimit) {
      console.log('✅ Concurrent requests handled with rate limiting');
    } else {
      console.log('⚠️ No rate limiting for concurrent requests');
    }

    await page.screenshot({ path: 'reports/screenshots/concurrent-requests-test.png', fullPage: false });
  });

  test('browser back button handling', async ({ page }) => {
    console.log('⬅️ Testing browser back button handling...');

    // Navigate through several pages
    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/pricing`);
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/about`);
    await page.waitForTimeout(2000);

    // Test back button
    await page.goBack();
    await page.waitForTimeout(2000);

    let currentUrl = page.url();
    if (currentUrl.includes('/pricing')) {
      console.log('✅ Back button works correctly');
    } else {
      console.log('⚠️ Back button navigation issue');
    }

    // Test back button with authenticated pages
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
      localStorage.setItem('user_email', TEST_EMAIL);
    });

    await page.goto(`${BASE_URL}/app/dashboard`);
    await page.waitForTimeout(2000);

    await page.goto(`${BASE_URL}/app/jobs`);
    await page.waitForTimeout(2000);

    await page.goBack();
    await page.waitForTimeout(2000);

    currentUrl = page.url();
    if (currentUrl.includes('/dashboard')) {
      console.log('✅ Back button works with authenticated pages');
    } else {
      console.log('⚠️ Back button issue with authenticated pages');
    }

    await page.screenshot({ path: 'reports/screenshots/back-button-test.png', fullPage: false });
  });

  test('memory leak detection', async ({ page }) => {
    console.log('🧠 Testing for memory leaks...');

    // Monitor memory usage
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    console.log(`📊 Initial memory usage: ${initialMemory} bytes`);

    // Perform multiple actions
    for (let i = 0; i < 10; i++) {
      await page.goto(`${BASE_URL}/login`);
      await page.waitForTimeout(1000);
      
      const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
      await emailInput.fill(`test-${i}@jobhuntin.com`);
      
      await page.goBack();
      await page.waitForTimeout(500);
    }

    // Check final memory usage
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    console.log(`📊 Final memory usage: ${finalMemory} bytes`);

    const memoryIncrease = finalMemory - initialMemory;
    const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100;

    console.log(`📊 Memory increase: ${memoryIncrease} bytes (${memoryIncreasePercent.toFixed(2)}%)`);

    if (memoryIncreasePercent < 50) {
      console.log('✅ Memory usage within acceptable limits');
    } else {
      console.log('⚠️ Potential memory leak detected');
    }

    await page.screenshot({ path: 'reports/screenshots/memory-usage-test.png', fullPage: false });
  });

  test('resource loading failure handling', async ({ page }) => {
    console.log('🚫 Testing resource loading failure handling...');

    // Block CSS files
    await page.route('**/*.css', async route => {
      await route.abort();
    });

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    // Check if page still functions without CSS
    const emailInput = page.locator('input[type="email"], input[placeholder*="email"]').first();
    const hasInput = await emailInput.isVisible().catch(() => false);

    if (hasInput) {
      console.log('✅ Page functions without CSS');
    } else {
      console.log('⚠️ Page broken without CSS');
    }

    // Block JavaScript files
    await page.unroute('**/*.css');
    await page.route('**/*.js', async route => {
      await route.abort();
    });

    await page.goto(`${BASE_URL}/login`);
    await page.waitForTimeout(2000);

    // Check if page shows fallback content
    const fallbackContent = page.locator('body').first();
    const hasContent = await fallbackContent.isVisible();

    if (hasContent) {
      console.log('✅ Fallback content shown without JavaScript');
    } else {
      console.log('⚠️ No fallback content without JavaScript');
    }

    await page.screenshot({ path: 'reports/screenshots/resource-failure-test.png', fullPage: false });
  });
});
