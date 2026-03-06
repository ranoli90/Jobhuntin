import { defineConfig, devices } from '@playwright/test';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(process.cwd(), '.env') });

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

export default defineConfig({
  testDir: './src/tests',
  timeout: 120_000, // Increased timeout for comprehensive tests
  expect: {
    timeout: 15_000, // Increased timeout for assertions
    toHaveScreenshot: {
      maxDiffPixels: 2000, // More lenient for production testing
      animations: 'disabled', // Disable animations for consistent screenshots
    },
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 3 : 2, // More retries for flaky production tests
  workers: process.env.CI ? 2 : undefined, // Fewer workers to avoid overwhelming production
  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/results.json' }],
    ['junit', { outputFile: 'reports/junit.xml' }],
    ['line'], // Show progress line by line
  ],
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure', // Keep traces for failures
    video: 'retain-on-failure', // Keep videos for failures
    screenshot: 'only-on-failure', // Screenshots on failure only
    actionTimeout: 20_000, // Longer timeout for production
    navigationTimeout: 30_000, // Longer navigation timeout
    viewport: { width: 1280, height: 720 },
    // Slow down for production stability
    launchOptions: {
      slowMo: process.env.CI ? 0 : 100, // Slow down in local testing
    },
  },
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/complete-auth-flow.spec.ts',
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      testMatch: '**/complete-onboarding.spec.ts',
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testMatch: '**/core-features.spec.ts',
    },
    
    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: '**/cross-browser-mobile.spec.ts',
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
      testMatch: '**/cross-browser-mobile.spec.ts',
    },
    
    // Tablet testing
    {
      name: 'tablet',
      use: { ...devices['iPad (gen 7)'], viewport: { width: 1024, height: 1366 } },
      testMatch: '**/cross-browser-mobile.spec.ts',
    },
    
    // Error handling and edge cases
    {
      name: 'error-handling',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/error-handling.spec.ts',
    },
    
    // Performance and accessibility
    {
      name: 'performance-accessibility',
      use: { ...devices['Desktop Chrome'] },
      testMatch: '**/performance-accessibility.spec.ts',
    },
  ],
  outputDir: 'test-results',
  metadata: {
    target: BASE_URL,
    env: process.env.NODE_ENV || 'production',
    testEmail: TEST_EMAIL,
    testType: 'production-readiness-validation',
  },
  // Global setup and teardown
  globalSetup: './src/global-setup.ts',
  globalTeardown: './src/global-teardown.ts',
});
