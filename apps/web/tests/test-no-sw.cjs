const { chromium } = require('playwright');

const WEB_URL = 'https://sorce-web.onrender.com';

async function testWithoutSW() {
  console.log('Testing without Service Worker...\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    serviceWorkers: 'block'  // Block service workers
  });
  const page = await context.newPage();

  // Listen for console
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.type() === 'log') {
      console.log(`[${msg.type()}]`, msg.text());
    }
  });

  console.log('Loading /login without SW...');
  // Add timestamp to bypass any caching
  await page.goto(`${WEB_URL}/login?t=${Date.now()}`, { 
    waitUntil: 'networkidle',
    timeout: 30000 
  });
  
  await page.waitForTimeout(3000);
  
  const text = await page.textContent('body');
  console.log('\nPage content:', text.substring(0, 300));

  await browser.close();
}

testWithoutSW();
