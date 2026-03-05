import { FullConfig } from '@playwright/test';
import fs from 'fs-extra';

async function globalTeardown(config: FullConfig) {
  console.log('🏁 Starting global teardown...');
  
  try {
    // Generate test summary
    const summary = {
      timestamp: new Date().toISOString(),
      testType: 'production-readiness-validation',
      baseUrl: process.env.BASE_URL || 'https://jobhuntin.com',
      environment: process.env.NODE_ENV || 'production',
      ciMode: !!process.env.CI,
    };

    // Save summary
    await fs.writeJson('reports/test-summary.json', summary, { spaces: 2 });
    
    console.log('📊 Test summary saved to reports/test-summary.json');
    
    // Check if test results exist
    const resultsExist = await fs.pathExists('reports/results.json');
    if (resultsExist) {
      const results = await fs.readJson('reports/results.json');
      const totalTests = results.suites?.reduce((acc: number, suite: any) => 
        acc + (suite.specs?.length || 0), 0) || 0;
      
      console.log(`📈 Test Results Summary:`);
      console.log(`   - Total tests: ${totalTests}`);
      console.log(`   - Passed: ${results.passed || 0}`);
      console.log(`   - Failed: ${results.failed || 0}`);
      console.log(`   - Flaky: ${results.flaky || 0}`);
      console.log(`   - Skipped: ${results.skipped || 0}`);
    }

    console.log('✅ Global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
  }
}

export default globalTeardown;
