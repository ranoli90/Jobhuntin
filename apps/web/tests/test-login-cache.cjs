const { chromium } = require('playwright');

const WEB_URL = 'https://sorce-web.onrender.com';

async function testWithCacheBypass() {
  console.log('Testing with cache bypass...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    serviceWorker: 'none'  // Disable service workers
  });
  const page = await context.newPage();

  // Set cache control headers to bypass cache
  await page.route('**/*', async route => {
    await route.continue({
      headers: {
        ...route.request().headers(),
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
  });

  // Listen for console
  page.on('console', msg => {
    console.log(`[${msg.type()}]`, msg.text());
  });
  
  // Listen for network
  page.on('request', request => {
    if (request.url().includes('profile')) {
      console.log('REQUEST profile:', request.url());
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('profile')) {
      console.log('RESPONSE profile:', response.status());
    }
  });

  console.log('Loading /login with cache bypass...');
  await page.goto(`${WEB_URL}/login?t=${Date.now()}`, { 
    waitUntil: 'networkidle',
    timeout: 30000 
  });
  
  await page.waitForTimeout(5000);
  
  const text = await page.textContent('body');
  console.log('\nPage has login form:', text.includes('email') || text.includes('Email'));

  await browser.close();
}

testWithCacheBypass();
