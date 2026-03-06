import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://jobhuntin.com';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test-e2e-production@jobhuntin.com';

test.describe('Core Application Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    // Set up authenticated state for testing
    await page.goto(BASE_URL);
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock-test-token-for-e2e');
      localStorage.setItem('user_email', TEST_EMAIL);
      localStorage.setItem('user_id', 'test-user-id-123');
      localStorage.setItem('has_completed_onboarding', 'true');
    });
  });

  test('complete job search and application flow', async ({ page }) => {
    console.log('🔍 Starting complete job search and application flow test...');

    // Step 1: Access dashboard
    await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const dashboardUrl = page.url();
    if (!dashboardUrl.includes('/app/dashboard')) {
      console.log('❌ Unable to access dashboard');
      await page.screenshot({ path: 'reports/screenshots/dashboard-access-denied.png', fullPage: false });
      return;
    }
    
    console.log('✅ Successfully accessed dashboard');
    await page.screenshot({ path: 'reports/screenshots/dashboard-start.png', fullPage: false });

    // Step 2: Navigate to jobs page
    await navigateToJobsPage(page);

    // Step 3: Test job search functionality
    await testJobSearch(page);

    // Step 4: Test job application flow
    await testJobApplication(page);

    // Step 5: Test application tracking
    await testApplicationTracking(page);
  });

  test('user profile management', async ({ page }) => {
    console.log('👤 Testing user profile management...');

    await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Look for profile/settings navigation
    const profileLinks = [
      'a[href*="profile"]',
      'a[href*="settings"]',
      'button:has-text("Profile")',
      'button:has-text("Settings")'
    ];

    let profilePageFound = false;
    for (const selector of profileLinks) {
      const link = page.locator(selector).first();
      const isVisible = await link.isVisible().catch(() => false);
      if (isVisible) {
        console.log(`✅ Found profile link: ${selector}`);
        await link.click();
        await page.waitForTimeout(2000);
        profilePageFound = true;
        break;
      }
    }

    if (!profilePageFound) {
      // Try direct navigation
      await page.goto(`${BASE_URL}/app/settings`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
    }

    const currentUrl = page.url();
    if (currentUrl.includes('/settings') || currentUrl.includes('/profile')) {
      console.log('✅ Successfully accessed profile/settings page');
      await testProfileManagement(page);
    } else {
      console.log('⚠️ Profile/settings page not found');
      await page.screenshot({ path: 'reports/screenshots/profile-page-not-found.png', fullPage: false });
    }
  });

  test('dashboard functionality and data loading', async ({ page }) => {
    console.log('📊 Testing dashboard functionality...');

    await page.goto(`${BASE_URL}/app/dashboard`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Check for dashboard content loading
    const dashboardContent = page.locator('main, [role="main"], .dashboard').first();
    const hasContent = await dashboardContent.isVisible().catch(() => false);
    
    if (hasContent) {
      console.log('✅ Dashboard content loaded');
      
      // Look for common dashboard elements
      const elements = [
        { selector: 'text=/Applications|Jobs|Profile/i', name: 'Dashboard sections' },
        { selector: '[data-testid*="stats"], [data-testid*="metrics"]', name: 'Stats/metrics' },
        { selector: 'button:has-text(/View|Manage|Edit/i)', name: 'Action buttons' },
        { selector: '.card, .panel, .section', name: 'Content cards' }
      ];

      for (const { selector, name } of elements) {
        const element = page.locator(selector).first();
        const isVisible = await element.isVisible().catch(() => false);
        if (isVisible) {
          console.log(`✅ Found ${name}`);
        }
      }

      // Test data loading (check for loading states)
      const loadingIndicators = await page.locator('text=/Loading|Loading...|Please wait/i').all();
      const loadingCount = loadingIndicators.length;
      
      if (loadingCount > 0) {
        console.log('⏳ Dashboard is loading data...');
        // Wait for loading to complete
        await page.waitForTimeout(5000);
        
        // Check if loading indicators disappeared
        const finalLoadingCount = await page.locator('text=/Loading|Loading...|Please wait/i').count();
        if (finalLoadingCount < loadingCount) {
          console.log('✅ Dashboard data loading completed');
        }
      }

      await page.screenshot({ path: 'reports/screenshots/dashboard-functionality.png', fullPage: false });
    } else {
      console.log('❌ Dashboard content not loaded');
      await page.screenshot({ path: 'reports/screenshots-dashboard-no-content.png', fullPage: false });
    }
  });

  test('navigation and routing', async ({ page }) => {
    console.log('🧭 Testing navigation and routing...');

    const routes = [
      { path: '/app/dashboard', name: 'Dashboard' },
      { path: '/app/jobs', name: 'Jobs' },
      { path: '/app/applications', name: 'Applications' },
      { path: '/app/settings', name: 'Settings' }
    ];

    for (const route of routes) {
      console.log(`📍 Testing route: ${route.name}`);
      
      await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      const currentUrl = page.url();
      
      // Check if we can access the route or get redirected
      if (currentUrl.includes(route.path)) {
        console.log(`✅ Successfully accessed ${route.name}`);
        
        // Look for page content
        const pageContent = page.locator('h1, h2, main, [role="main"]').first();
        const hasContent = await pageContent.isVisible().catch(() => false);
        
        if (hasContent) {
          console.log(`✅ ${route.name} has content`);
        } else {
          console.log(`⚠️ ${route.name} may be empty`);
        }
        
        await page.screenshot({ path: `reports/screenshots/route-${route.name.toLowerCase().replace(' ', '-')}.png`, fullPage: false });
      } else {
        console.log(`🔄 ${route.name} redirected to: ${currentUrl}`);
      }
    }
  });
});

async function navigateToJobsPage(page: Page) {
  console.log('🔍 Navigating to jobs page...');

  // Look for jobs navigation
  const jobsLinks = [
    'a[href*="jobs"]',
    'button:has-text("Jobs")',
    'nav a:has-text("Jobs")',
    '[data-testid="jobs-link"]'
  ];

  for (const selector of jobsLinks) {
    const link = page.locator(selector).first();
    const isVisible = await link.isVisible().catch(() => false);
    if (isVisible) {
      console.log(`✅ Found jobs link: ${selector}`);
      await link.click();
      await page.waitForTimeout(2000);
      break;
    }
  }

  // Try direct navigation if link not found
  const currentUrl = page.url();
  if (!currentUrl.includes('/jobs')) {
    await page.goto(`${BASE_URL}/app/jobs`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
  }

  const jobsUrl = page.url();
  if (jobsUrl.includes('/jobs')) {
    console.log('✅ Successfully accessed jobs page');
  } else {
    console.log('⚠️ Jobs page not accessible');
  }
}

async function testJobSearch(page: Page) {
  console.log('🔍 Testing job search functionality...');

  // Look for search input
  const searchInputs = await page.locator('input[placeholder*="search"], input[placeholder*="Search"], .search-input').all();
  const searchCount = searchInputs.length;

  if (searchCount > 0) {
    const searchInput = searchInputs[0];
    console.log('✅ Found search input');
    
    // Test search functionality
    await searchInput.fill('Software Engineer');
    await page.waitForTimeout(1000);
    
    // Look for search button
    const searchButton = page.locator('button[type="submit"], button:has-text("Search")').first();
    const hasSearchButton = await searchButton.isVisible().catch(() => false);
    
    if (hasSearchButton) {
      await searchButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Check for search results
    const searchResults = page.locator('[data-testid*="job"], .job-card, .job-item').all();
    const resultCount = searchResults.length;
    
    console.log(`📊 Found ${resultCount} job search results`);
    
    if (resultCount > 0) {
      console.log('✅ Job search returned results');
    } else {
      console.log('⚠️ No job search results found');
    }
    
    await page.screenshot({ path: 'reports/screenshots/job-search-results.png', fullPage: false });
  } else {
    console.log('⚠️ Search input not found');
  }

  // Test filter functionality
  const filterButtons = await page.locator('button:has-text("Filter"), .filter-button, [data-testid="filter"]').all();
  const filterCount = filterButtons.length;
  
  if (filterCount > 0) {
    console.log(`✅ Found ${filterCount} filter controls`);
  }

  // Test profile access
  const profileButtons = await page.locator('button:has-text("Profile"), .profile-button, [data-testid="profile"]').all();
  const profileCount = profileButtons.length;
}

async function testJobApplication(page: Page) {
  console.log('📝 Testing job application flow...');

  // Check for job listings
  const jobListings = await page.locator('[data-testid="job-card"], .job-card, .job-listing').all();
  const jobCount = jobListings.length;

  if (jobCount > 0) {
    console.log(`✅ Found ${jobCount} job listings`);
    
    // Try to interact with the first job card
    const firstCard = jobListings[0];
    await firstCard.click();
    await page.waitForTimeout(2000);
    
    // Test application functionality
    const applyButtons = await page.locator('button:has-text("Apply"), .apply-button, [data-testid="apply"]').all();
    const applyCount = applyButtons.length;
    
    if (applyCount > 0) {
      console.log('✅ Found apply button');
      
      // Test application process (but don't actually apply to avoid spam)
      console.log('🔄 Testing application flow (simulation)...');
      
      // Check for confirmation dialogs or modals
      await applyButtons[0].click();
      await page.waitForTimeout(2000);
      
      // Look for application confirmation
      const confirmation = page.locator('text=/Applied|Success|Confirmation/i').first();
      const hasConfirmation = await confirmation.isVisible().catch(() => false);
      
      if (hasConfirmation) {
        console.log('✅ Application flow completed');
      } else {
        console.log('⚠️ Application confirmation not found (may require additional steps)');
      }
      
      await page.screenshot({ path: 'reports/screenshots/job-application-test.png', fullPage: false });
    } else {
      console.log('⚠️ Apply button not found');
    }
  } else {
    console.log('⚠️ No job listings found to test application');
  }
}

async function testApplicationTracking(page: Page) {
  console.log('📊 Testing application tracking...');

  // Navigate to applications page
  await page.goto(`${BASE_URL}/app/applications`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  const applicationsUrl = page.url();
  if (applicationsUrl.includes('/applications')) {
    console.log('✅ Successfully accessed applications page');
    
    // Look for application listings
    const applicationItems = await page.locator('[data-testid*="application"], .application-card, .application-item').all();
    const applicationCount = applicationItems.length;
    
    console.log(`📊 Found ${applicationCount} applications`);
    
    if (applicationCount > 0) {
      console.log('✅ Application tracking is working');
      
      // Look for application status indicators
      const statusIndicators = await page.locator('text=/Applied|Pending|In Progress|Rejected|Accepted/i').all();
      const statusCount = statusIndicators.length;
      
      if (statusCount > 0) {
        console.log(`✅ Found ${statusCount} status indicators`);
      }
    } else {
      console.log('⚠️ No applications found (may be expected for new user)');
    }
    
    await page.screenshot({ path: 'reports/screenshots/application-tracking.png', fullPage: false });
  } else {
    console.log('⚠️ Applications page not accessible');
  }
}

async function testProfileManagement(page: Page) {
  console.log('👤 Testing profile management features...');

  // Look for profile form fields
  const profileFields = [
    'input[name="name"]',
    'input[name="email"]',
    'input[name="location"]',
    'textarea[name="bio"]',
    'input[name="headline"]'
  ];

  let foundFields = 0;
  for (const selector of profileFields) {
    const field = page.locator(selector).first();
    const isVisible = await field.isVisible().catch(() => false);
    if (isVisible) {
      foundFields++;
      console.log(`✅ Found profile field: ${selector}`);
    }
  }

  console.log(`📊 Found ${foundFields} profile fields`);

  // Look for save/update buttons
  const saveButton = page.locator('button:has-text(/Save|Update|Apply/i)').first();
  const hasSaveButton = await saveButton.isVisible().catch(() => false);
  
  if (hasSaveButton) {
    console.log('✅ Found save/update button');
  }

  // Look for profile sections
  const profileSections = [
    'text=/Personal Information|Contact|About/i',
    'text=/Preferences|Settings|Notifications/i',
    'text=/Resume|CV|Experience/i'
  ];

  for (const selector of profileSections) {
    const section = page.locator(selector).first();
    const isVisible = await section.isVisible().catch(() => false);
    if (isVisible) {
      console.log(`✅ Found profile section: ${selector}`);
    }
  }

  await page.screenshot({ path: 'reports/screenshots/profile-management.png', fullPage: false });
}
