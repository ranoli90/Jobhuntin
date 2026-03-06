import { test, expect, chromium, Browser, Page } from '@playwright/test';

const PRODUCTION_URL = 'https://sorce-web.onrender.com';
const API_URL = 'https://sorce-api.onrender.com';

async function testMagicLinkFlow() {
  console.log('Starting E2E Magic Link Flow Test...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Step 1: Go to Login page
    console.log('1. Loading Login page...');
    await page.goto(`${PRODUCTION_URL}/login`, { timeout: 30000 });
    await page.waitForLoadState('networkidle');
    console.log('   ✓ Login page loaded\n');

    // Step 2: Check for CSRF token (should be set by API)
    console.log('2. Checking CSRF token...');
    const cookies = await context.cookies();
    const csrfCookie = cookies.find(c => c.name === 'csrftoken');
    if (csrfCookie) {
      console.log('   ✓ CSRF token present\n');
    } else {
      console.log('   ⚠ CSRF token not found (may be set on first request)\n');
    }

    // Step 3: Fill in email and request magic link
    console.log('3. Requesting magic link...');
    const testEmail = `e2e-test-${Date.now()}@example.com`;
    
    // Listen for the API call
    let magicLinkRequest: any = null;
    await page.route(`${API_URL}/auth/magic-link`, async route => {
      magicLinkRequest = route.request().postDataJSON();
      await route.continue();
    });

    await page.fill('input[type="email"], input[placeholder*="email"]', testEmail);
    
    // Click the send button
    const sendButton = page.getByRole('button', { name: /send magic link|sign in|continue/i });
    if (await sendButton.isVisible()) {
      await sendButton.click();
    }
    
    // Wait a bit for the request
    await page.waitForTimeout(2000);
    
    if (magicLinkRequest) {
      console.log('   ✓ Magic link request sent');
      console.log(`   Email: ${magicLinkRequest.email}\n`);
    }

    // Step 4: Check for success message
    console.log('4. Checking for success message...');
    const successMessage = await page.getByText(/check your email|check your inbox|magic link sent/i).isVisible();
    if (successMessage) {
      console.log('   ✓ Success message displayed\n');
    } else {
      const pageContent = await page.content();
      console.log('   Current page content:', pageContent.substring(0, 500));
    }

    // Step 5: Check for errors
    const errorMessage = await page.getByText(/error|failed|something went wrong/i).isVisible();
    if (errorMessage) {
      console.log('   ⚠ Error message found');
      const errorText = await page.getByText(/error|failed|something went wrong/i).textContent();
      console.log(`   Error: ${errorText}\n`);
    }

    console.log('\n=== TEST SUMMARY ===');
    console.log('Login page loads: ✓');
    console.log('CSRF token: ' + (csrfCookie ? '✓' : '⚠'));
    console.log('Magic link API called: ' + (magicLinkRequest ? '✓' : '✗'));
    console.log('Success message: ' + (successMessage ? '✓' : '⚠'));

  } catch (error) {
    console.error('\n❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

testMagicLinkFlow();
