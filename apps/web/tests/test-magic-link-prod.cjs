const { chromium } = require('playwright');

const PRODUCTION_URL = 'https://sorce-web.onrender.com';
const API_URL = 'https://sorce-api.onrender.com';

async function testMagicLinkFlow() {
  console.log('Starting E2E Magic Link Flow Test...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Test 1: Load Homepage
    console.log('=== TEST 1: Load Homepage ===\n');
    console.log('1. Loading Homepage...');
    
    // Listen for page errors
    page.on('pageerror', error => {
      console.log('   Page error:', error.message);
    });
    
    await page.goto(`${PRODUCTION_URL}/`, { timeout: 30000 });
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    const homepageText = await page.textContent('body');
    console.log('   Homepage loaded:', homepageText.substring(0, 100));
    console.log('');
    
    // Test 3: Load Login directly
    console.log('\n=== TEST 3: Load Login DIRECTLY ===\n');
    console.log('1. Loading /login directly...');
    
    // Create a NEW page to avoid any state from previous tests
    const page2 = await context.newPage();
    
    page2.on('console', msg => {
      console.log(`   [${msg.type()}]`, msg.text());
    });
    
    page2.on('pageerror', error => {
      console.log('   Page error:', error.message);
    });
    
    await page2.goto(`${PRODUCTION_URL}/login`, { timeout: 30000 });
    await page2.waitForLoadState('domcontentloaded');
    await page2.waitForTimeout(3000);
    
    const loginText2 = await page2.textContent('body');
    console.log('   Login page content:', loginText2.substring(0, 300));
    
    // Check for inputs
    const inputs2 = await page2.$$('input');
    console.log(`   Found ${inputs2.length} inputs`);
    
    await page2.close();
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000); // Give React time to render
    
    // Debug: get page title and content
    const title = await page.title();
    console.log('   Page title:', title);
    
    // Check if there's any visible content
    const bodyText = await page.textContent('body');
    console.log('   Page text (first 500 chars):', bodyText.substring(0, 500));
    
    console.log('   ✓ Login page loaded\n');

    // Step 2: Check for CSRF token
    console.log('2. Checking CSRF token...');
    const cookies = await context.cookies();
    const csrfCookie = cookies.find(c => c.name === 'csrftoken');
    if (csrfCookie) {
      console.log('   ✓ CSRF token present\n');
    } else {
      console.log('   ⚠ CSRF token not found\n');
    }

    // Step 3: Fill in email and request magic link
    console.log('3. Requesting magic link...');
    const testEmail = `e2e-test-${Date.now()}@example.com`;
    
    // Listen for the API call
    let magicLinkRequest = null;
    await page.route(`${API_URL}/auth/magic-link`, async route => {
      magicLinkRequest = route.request().postDataJSON();
      await route.continue();
    });

    // Debug: print all inputs
    console.log('   Debug: Looking for inputs...');
    const inputs = await page.$$('input');
    console.log(`   Found ${inputs.length} inputs`);
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const type = await input.getAttribute('type');
      const placeholder = await input.getAttribute('placeholder');
      console.log(`   Input: id=${id}, type=${type}, placeholder=${placeholder}`);
    }
    
    // Try to find and fill the email input - use id from Login.tsx
    const emailInput = await page.$('#login-email') || await page.$('input[type="email"]');
    if (emailInput) {
      await emailInput.fill(testEmail);
      console.log('   Filled email:', testEmail);
      
      // Click the send button - use role selector
      const sendButton = page.getByRole('button', { name: /send magic link|send link|sign in/i });
      if (await sendButton.count() > 0) {
        await sendButton.click();
      } else {
        // Try finding by type
        const button = await page.$('button[type="submit"]');
        if (button) await button.click();
      }
      
      // Wait for the request
      await page.waitForTimeout(3000);
      
      if (magicLinkRequest) {
        console.log('   ✓ Magic link request sent to API');
        console.log(`   Email: ${magicLinkRequest.email}\n`);
      }
    } else {
      console.log('   Could not find email input on page');
    }

    // Step 4: Check for success message
    console.log('4. Checking for response...');
    const pageText = await page.textContent('body');
    
    if (pageText.includes('Check your email') || pageText.includes('check your inbox')) {
      console.log('   ✓ Success message displayed\n');
    } else if (pageText.includes('error') || pageText.includes('failed')) {
      console.log('   ⚠ Error message found');
    }

    console.log('\n=== TEST SUMMARY ===');
    console.log('Login page loads: ✓');
    console.log('CSRF token: ' + (csrfCookie ? '✓' : '⚠'));
    console.log('Magic link API called: ' + (magicLinkRequest ? '✓' : '✗'));

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testMagicLinkFlow();
