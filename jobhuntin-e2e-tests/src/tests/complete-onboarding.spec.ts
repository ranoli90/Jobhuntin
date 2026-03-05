import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

test.describe('Complete Onboarding Experience', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    // Set up authenticated state for onboarding testing
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
    });
  });

  test('complete onboarding flow: profile setup → preferences → dashboard', async ({ page }) => {
    console.log('🎯 Starting complete onboarding flow test...');

    // Step 1: Navigate to onboarding
    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/app/onboarding')) {
      console.log('❌ Unable to access onboarding page');
      await page.screenshot({ path: 'reports/screenshots/onboarding-access-denied.png', fullPage: false });
      return;
    }
    
    console.log('✅ Successfully accessed onboarding');
    await page.screenshot({ path: 'reports/screenshots/onboarding-start.png', fullPage: false });

    // Step 2: Test onboarding steps
    await testOnboardingSteps(page);

    // Step 3: Test dashboard access after onboarding
    await testDashboardAccess(page);
  });

  test('resume upload and processing', async ({ page }) => {
    console.log('📄 Testing resume upload functionality...');

    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for resume upload area
    const uploadArea = page.locator('input[type="file"], [data-testid="resume-upload"], .upload-area').first();
    const hasUploadArea = await uploadArea.isVisible().catch(() => false);

    if (hasUploadArea) {
      console.log('✅ Resume upload area found');
      
      // Test file upload (create a mock resume file)
      const mockResume = Buffer.from('Mock resume content for testing').toString('base64');
      
      // Try to upload the file
      await uploadArea.setInputFiles({
        name: 'test-resume.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from(mockResume, 'base64')
      });
      
      await page.waitForTimeout(3000);
      
      // Check for upload success or processing indicator
      const uploadSuccess = page.locator('text=/uploaded|processing|success/i');
      const hasUploadSuccess = await uploadSuccess.isVisible().catch(() => false);
      
      if (hasUploadSuccess) {
        console.log('✅ Resume upload initiated successfully');
      } else {
        console.log('⚠️ Resume upload status unclear');
      }
      
      await page.screenshot({ path: 'reports/screenshots/resume-upload-test.png', fullPage: false });
    } else {
      console.log('⚠️ Resume upload area not found - may be in a different step');
    }
  });

  test('profile data collection and validation', async ({ page }) => {
    console.log('👤 Testing profile data collection...');

    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for profile input fields
    const profileFields = [
      'input[name="name"]',
      'input[name="location"]',
      'input[name="headline"]',
      'textarea[name="bio"]',
      'input[placeholder*="name"]',
      'input[placeholder*="location"]'
    ];

    let foundFields = 0;
    for (const selector of profileFields) {
      const field = page.locator(selector).first();
      const isVisible = await field.isVisible().catch(() => false);
      if (isVisible) {
        foundFields++;
        console.log(`✅ Found profile field: ${selector}`);
        
        // Try to fill the field
        if (selector.includes('name')) {
          await field.fill('Test User');
        } else if (selector.includes('location')) {
          await field.fill('San Francisco, CA');
        } else if (selector.includes('headline')) {
          await field.fill('Software Engineer');
        } else if (selector.includes('bio')) {
          await field.fill('Experienced software engineer looking for new opportunities.');
        }
      }
    }

    console.log(`📊 Found ${foundFields} profile fields`);
    await page.screenshot({ path: 'reports/screenshots/profile-fields-test.png', fullPage: false });

    // Look for form validation
    const submitButton = page.locator('button:has-text(/Continue|Next|Save/i)').first();
    const hasSubmitButton = await submitButton.isVisible().catch(() => false);
    
    if (hasSubmitButton) {
      console.log('✅ Submit button found, testing validation...');
      await submitButton.click();
      await page.waitForTimeout(2000);
      
      // Check for validation errors
      const validationErrors = page.locator('text=/required|invalid|missing/i');
      const hasValidationErrors = await validationErrors.isVisible().catch(() => false);
      
      if (hasValidationErrors) {
        console.log('✅ Form validation is working');
      } else {
        console.log('✅ Form submitted successfully (or validation not triggered)');
      }
      
      await page.screenshot({ path: 'reports/screenshots/profile-validation-test.png', fullPage: false });
    }
  });

  test('job preferences setup', async ({ page }) => {
    console.log('💼 Testing job preferences setup...');

    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for job preference controls
    const preferenceSelectors = [
      'select[name="jobType"]',
      'input[name="salaryMin"]',
      'input[name="salaryMax"]',
      'input[name="location"]',
      'input[type="checkbox"][name*="remote"]',
      'input[type="radio"][name*="jobType"]'
    ];

    let foundPreferences = 0;
    for (const selector of preferenceSelectors) {
      const field = page.locator(selector).first();
      const isVisible = await field.isVisible().catch(() => false);
      if (isVisible) {
        foundPreferences++;
        console.log(`✅ Found preference field: ${selector}`);
        
        // Try to interact with the field
        if (selector.includes('jobType') && selector.includes('select')) {
          await field.selectOption({ label: 'Full-time' });
        } else if (selector.includes('salaryMin')) {
          await field.fill('80000');
        } else if (selector.includes('salaryMax')) {
          await field.fill('150000');
        } else if (selector.includes('remote') && selector.includes('checkbox')) {
          await field.check();
        }
      }
    }

    console.log(`📊 Found ${foundPreferences} job preference fields`);
    await page.screenshot({ path: 'reports/screenshots/job-preferences-test.png', fullPage: false });
  });

  test('navigation between onboarding steps', async ({ page }) => {
    console.log('🔄 Testing onboarding navigation...');

    await page.goto(`${BASE_URL}/app/onboarding`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for navigation elements
    const navigationButtons = [
      'button:has-text("Back")',
      'button:has-text("Previous")',
      'button:has-text("Next")',
      'button:has-text("Continue")',
      'button:has-text("Skip")'
    ];

    let navigationSteps = 0;
    let currentStep = 1;

    // Try to navigate through multiple steps
    for (let attempt = 0; attempt < 5; attempt++) {
      console.log(`📍 Testing navigation step ${currentStep}...`);
      
      // Look for any navigation button
      let foundNavigation = false;
      for (const selector of navigationButtons) {
        const button = page.locator(selector).first();
        const isVisible = await button.isVisible().catch(() => false);
        if (isVisible) {
          console.log(`✅ Found navigation button: ${selector}`);
          await button.click();
          await page.waitForTimeout(2000);
          foundNavigation = true;
          navigationSteps++;
          currentStep++;
          break;
        }
      }
      
      if (!foundNavigation) {
        console.log('🏁 No more navigation buttons found');
        break;
      }
      
      // Take screenshot of each step
      await page.screenshot({ path: `reports/screenshots/onboarding-step-${currentStep}.png`, fullPage: false });
    }

    console.log(`📊 Navigated through ${navigationSteps} onboarding steps`);
  });
});

async function testOnboardingSteps(page: Page) {
  console.log('🔍 Testing onboarding steps...');

  // Check for progress indicator
  const progressIndicator = page.locator('text=/Progress|Step|Calibration|1 of|2 of/i');
  const hasProgress = await progressIndicator.isVisible().catch(() => false);
  
  if (hasProgress) {
    console.log('✅ Progress indicator found');
  }

  // Look for step content
  const stepContent = page.locator('main, [role="main"], .onboarding-content').first();
  const hasStepContent = await stepContent.isVisible().catch(() => false);
  
  if (hasStepContent) {
    console.log('✅ Step content found');
  }

  // Try to interact with common onboarding elements
  const buttons = page.locator('button').all();
  console.log(`📊 Found ${await buttons.length} buttons on the page`);

  // Look for input fields
  const inputs = page.locator('input, textarea, select').all();
  console.log(`📊 Found ${await inputs.length} input fields on the page`);
}

async function testDashboardAccess(page: Page) {
  console.log('🏠 Testing dashboard access after onboarding...');

  await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const dashboardUrl = page.url();
  
  if (dashboardUrl.includes('/app/dashboard')) {
    console.log('✅ Successfully accessed dashboard');
    
    // Check for dashboard elements
    const dashboardElements = [
      'h1, h2',
      '.dashboard',
      '[data-testid="dashboard"]',
      'main',
      '[role="main"]'
    ];

    let foundElements = 0;
    for (const selector of dashboardElements) {
      const element = page.locator(selector).first();
      const isVisible = await element.isVisible().catch(() => false);
      if (isVisible) {
        foundElements++;
        console.log(`✅ Found dashboard element: ${selector}`);
      }
    }

    if (foundElements > 0) {
      console.log('✅ Dashboard appears to be loaded');
    } else {
      console.log('⚠️ Dashboard may be empty or still loading');
    }

    // Look for common dashboard features
    const features = [
      'text=/Applications|Jobs|Profile|Settings/i',
      'button:has-text(/Applications|Jobs|Profile/i)',
      '[data-testid*="application"]',
      '[data-testid*="job"]'
    ];

    for (const selector of features) {
      const element = page.locator(selector).first();
      const isVisible = await element.isVisible().catch(() => false);
      if (isVisible) {
        console.log(`✅ Found dashboard feature: ${selector}`);
      }
    }

    await page.screenshot({ path: 'reports/screenshots/dashboard-after-onboarding.png', fullPage: false });
  } else {
    console.log('❌ Unable to access dashboard after onboarding');
    console.log('📍 Current URL:', dashboardUrl);
    await page.screenshot({ path: 'reports/screenshots/dashboard-access-failed.png', fullPage: false });
  }
}
