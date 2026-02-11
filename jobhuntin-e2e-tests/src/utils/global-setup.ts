// src/utils/global-setup.ts
import { test as setup } from '@playwright/test';

setup('Global setup', async ({}) => {
  // Initialize test environment
  console.log('🚀 Starting E2E test suite for JobHuntin');
});
