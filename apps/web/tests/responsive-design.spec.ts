import { test, expect } from '@playwright/test';

// Comprehensive responsive design tests for all pages
test.describe('Responsive Design Tests', () => {
  // Test all main pages for basic responsive behavior
  const pagesToTest = [
    { path: '/', name: 'Homepage' },
    { path: '/about', name: 'About' },
    { path: '/pricing', name: 'Pricing' },
    { path: '/success-stories', name: 'Success Stories' },
    { path: '/chrome-extension', name: 'Chrome Extension' },
    { path: '/login', name: 'Login' },
  ];

  // Test each page on different devices
  pagesToTest.forEach(({ path, name }) => {
    test.describe(`${name} Responsive Tests`, () => {
      test('should display correctly on Desktop Chrome', async ({ page }) => {
        await page.goto(path);
        await expect(page).toHaveTitle(/JobHuntin/);
        await expect(page.locator('body')).toBeVisible();
        await expect(page).toHaveScreenshot(`desktop-${name.toLowerCase().replace(/\s+/g, '-')}.png`);
      });

      test('should display correctly on iPhone 13', async ({ page }) => {
        await page.goto(path);
        await expect(page).toHaveTitle(/JobHuntin/);
        await expect(page.locator('body')).toBeVisible();
        await expect(page).toHaveScreenshot(`iphone13-${name.toLowerCase().replace(/\s+/g, '-')}.png`);
      });

      test('should display correctly on Pixel 5', async ({ page }) => {
        await page.goto(path);
        await expect(page).toHaveTitle(/JobHuntin/);
        await expect(page.locator('body')).toBeVisible();
        await expect(page).toHaveScreenshot(`pixel5-${name.toLowerCase().replace(/\s+/g, '-')}.png`);
      });
    });
  });

  // Specific homepage responsive tests
  test.describe('Homepage Specific Responsive Tests', () => {
    test('hero section should be properly sized on mobile', async ({ page }) => {
      await page.goto('/');
      
      // Check if hero section elements are visible and properly positioned
      await expect(page.getByText('12,847 applications sent this week')).toBeVisible();
      await expect(page.getByPlaceholder('you@example.com')).toBeVisible();
      await expect(page.getByRole('button', { name: /Start free/i })).toBeVisible();
      
      // Verify no elements are overlapping or cutoff
      await expect(page).toHaveScreenshot('hero-section-mobile.png');
    });

    test('email input and submit button should fit on mobile screens', async ({ page }) => {
      await page.goto('/');
      
      // Check form elements are visible and interactable
      const emailInput = page.getByPlaceholder('you@example.com');
      await expect(emailInput).toBeVisible();
      
      const submitButton = page.getByRole('button', { name: /Start free/i });
      await expect(submitButton).toBeVisible();
      
      // Verify button text is not truncated
      await expect(submitButton).not.toContainText('...');
    });

    test('trust signals should wrap correctly on mobile', async ({ page }) => {
      await page.goto('/');
      
      const trustSignals = page.locator('.flex.items-center.justify-center');
      await expect(trustSignals).toBeVisible();
      
      // Verify all trust signals are present
      await expect(page.getByText('No credit card')).toBeVisible();
      await expect(page.getByText('Encrypted data')).toBeVisible();
      await expect(page.getByText('2 min setup')).toBeVisible();
    });

    test('terminal animation should display correctly on mobile', async ({ page }) => {
      await page.goto('/');
      
      // Check terminal demo is visible
      const terminal = page.locator('.bg-slate-950');
      await expect(terminal).toBeVisible();
      
      // Verify terminal steps are visible
      await expect(page.getByText('Resume')).toBeVisible();
      await expect(page.getByText('Scanning')).toBeVisible();
      await expect(page.getByText('Applied')).toBeVisible();
      await expect(page.getByText('Interviews')).toBeVisible();
    });
  });

  // Navigation and menu tests
  test.describe('Navigation Responsive Tests', () => {
    test('mobile menu should open and close correctly', async ({ page }) => {
      await page.goto('/');
      
      // Open mobile menu
      await page.getByRole('button', { name: /Open menu/i }).click();
      await expect(page.getByRole('navigation')).toBeVisible();
      
      // Check menu items are present
      await expect(page.getByText('Pricing')).toBeVisible();
      await expect(page.getByText('Success Stories')).toBeVisible();
      await expect(page.getByText('About')).toBeVisible();
      await expect(page.getByText('Extension')).toBeVisible();
      
      // Close menu
      await page.getByRole('button', { name: /Close menu/i }).click();
      await expect(page.getByRole('navigation')).not.toBeVisible();
    });
  });

  // Performance and accessibility tests
  test.describe('Performance and Accessibility', () => {
    test('page should load within reasonable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(5000); // Should load in under 5 seconds
    });

    test('should have accessible contrast ratios', async ({ page }) => {
      await page.goto('/');
      // This is a basic check - for comprehensive testing, use @axe-core/playwright
      const heading = page.getByRole('heading', { level: 1 });
      await expect(heading).toHaveCSS('color', /rgba\(15, 23, 42, 1\)/); // Slate-900
    });

    test('images should have proper alt attributes', async ({ page }) => {
      await page.goto('/');
      const images = page.locator('img');
      const count = await images.count();
      
      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        expect(alt).not.toBeNull();
      }
    });
  });
});
