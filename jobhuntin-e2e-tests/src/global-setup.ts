import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup for production readiness tests...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Test basic connectivity to the target site
    const baseUrl = process.env.BASE_URL || 'https://jobhuntin.com';
    console.log(`🌐 Testing connectivity to: ${baseUrl}`);
    
    const response = await page.goto(baseUrl, { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    if (response && response.status() === 200) {
      console.log('✅ Basic connectivity successful');
    } else {
      console.log(`❌ Connectivity failed with status: ${response?.status()}`);
      throw new Error(`Cannot reach ${baseUrl}`);
    }

    // Test API health if available
    const apiBaseUrl = process.env.API_URL || baseUrl.replace(/:\d+/, ':8000');
    try {
      const apiResponse = await page.request.get(`${apiBaseUrl}/health`, {
        timeout: 10000
      });
      
      if (apiResponse.status() === 200) {
        console.log('✅ API health check successful');
      } else {
        console.log(`⚠️ API health check returned: ${apiResponse.status()}`);
      }
    } catch (error) {
      console.log('⚠️ API health check failed (may not be available)');
    }

    // Create reports directory
    const fs = await import('fs-extra');
    await fs.ensureDir('reports/screenshots');
    await fs.ensureDir('reports/html');
    await fs.ensureDir('test-results');

    // Log test configuration
    console.log('📊 Test Configuration:');
    console.log(`   - Base URL: ${baseUrl}`);
    console.log(`   - Test Email: ${process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com'}`);
    console.log(`   - Environment: ${process.env.NODE_ENV || 'production'}`);
    console.log(`   - CI Mode: ${!!process.env.CI}`);

    console.log('✅ Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
