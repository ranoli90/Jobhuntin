const { chromium } = require('playwright');

const API_URL = 'https://sorce-api.onrender.com';
const WEB_URL = 'https://sorce-web.onrender.com';

async function testCORS() {
  console.log('Testing CORS with network interception...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Intercept requests
  page.on('request', request => {
    if (request.url().includes('api.onrender')) {
      console.log('Request:', request.method(), request.url());
      console.log('  Headers:', JSON.stringify(request.headers()));
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('api.onrender')) {
      console.log('Response:', response.status(), response.url());
      const headers = response.headers();
      console.log('  CORS origin:', headers['access-control-allow-origin']);
      console.log('  All CORS headers:', Object.keys(headers).filter(k => k.includes('access')));
    }
  });

  // First navigate to the web page
  console.log('1. Navigating to web page...');
  await page.goto(WEB_URL, { waitUntil: 'networkidle' });
  console.log('   Page loaded\n');
  
  // Now try to call the API
  console.log('2. Calling API...');
  await page.goto(WEB_URL);
  
  await page.evaluate(async () => {
    try {
      await fetch('https://sorce-api.onrender.com/csrf/prepare', {
        method: 'GET',
        credentials: 'include'
      });
    } catch(e) {}
  });
  
  await page.waitForTimeout(2000);

  await browser.close();
}

testCORS();
