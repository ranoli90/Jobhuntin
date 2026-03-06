const { chromium } = require('playwright');

const WEB_URL = 'https://sorce-web.onrender.com';

async function testSimplePage() {
  console.log('Testing simple page load...\n');

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Listen for ALL console messages from the start
  page.on('console', msg => {
    console.log(`[${msg.type()}]`, msg.text());
  });
  
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
    console.log('STACK:', error.stack);
  });

  console.log('Loading homepage (should work)...');
  await page.goto(WEB_URL, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Homepage loaded\n');
  
  // Now go to login
  console.log('Going to /login...');
  await page.goto(`${WEB_URL}/login`, { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Login page loaded');
  
  await browser.close();
}

testSimplePage();
