const { chromium } = require('playwright');

const PRODUCTION_URL = 'https://sorce-web.onrender.com';

async function testDirectLogin() {
  console.log('Testing direct /login load...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture all console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    console.log(`[${msg.type()}]`, text);
  });

  // Capture page errors
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push(error.message);
  });

  // Navigate to /login
  console.log('Loading /login...');
  const response = await page.goto(`${PRODUCTION_URL}/login`, { 
    timeout: 30000,
    waitUntil: 'networkidle'
  });
  
  console.log('Response status:', response.status());
  
  // Wait for React to render
  await page.waitForTimeout(5000);

  // Get page content
  const content = await page.content();
  
  // Check for error states
  const hasError = content.includes('Something went wrong') || content.includes('Page Error');
  console.log('Has error state:', hasError);
  
  // Print console errors
  console.log('\nConsole errors:');
  consoleMessages.filter(m => m.type === 'error').forEach(m => console.log('  -', m.text));
  
  // Print page errors
  if (pageErrors.length > 0) {
    console.log('\nPage errors:');
    pageErrors.forEach(e => console.log('  -', e));
  }
  
  // Check what's actually rendered
  const bodyText = await page.textContent('body');
  console.log('\nPage text (first 500 chars):');
  console.log(bodyText.substring(0, 500));

  await browser.close();
}

testDirectLogin();
