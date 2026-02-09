import { test, expect } from '@playwright/test';

test.describe('Authentication System', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('Login UI Elements should be visible', async ({ page }) => {
    await expect(page.getByText("Let's get hunting")).toBeVisible();
    await expect(page.getByRole('button', { name: 'Magic Link' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Password Login' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create Account' })).toBeVisible();
  });

  test('Invalid Login should show error', async ({ page }) => {
    // Switch to Password Login
    await page.getByRole('button', { name: 'Password Login' }).click();
    
    // Fill invalid credentials
    await page.getByPlaceholder('tech-wizard@example.com').fill('invalid@example.com');
    await page.getByPlaceholder('••••••••').fill('wrongpassword');
    
    // Submit
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Expect error message
    // Note: The actual error message depends on Supabase response.
    // Based on code: setFormError(err.message || "Sign-in failed");
    // Common Supabase error: "Invalid login credentials"
    await expect(page.getByRole('alert')).toBeVisible();
  });

  test('Registration Form Validation', async ({ page }) => {
    // Switch to Create Account
    await page.getByRole('button', { name: 'Create Account' }).click();
    
    // Check for password requirements visibility
    await expect(page.getByText('Security Checklist')).toBeVisible();
    await expect(page.getByText('10+ characters')).toBeVisible();

    // Fill weak password
    await page.getByPlaceholder('tech-wizard@example.com').fill('newuser@example.com');
    await page.getByPlaceholder('Create a strong password').fill('weak');
    
    // Submit should be disabled or show error
    // Code says: disabled={isLoading || !canSubmit ...}
    // canSubmit checks passwordIsStrong
    const submitBtn = page.getByRole('button', { name: 'Create Account' });
    await expect(submitBtn).toBeDisabled();
    
    // Make password strong
    await page.getByPlaceholder('Create a strong password').fill('StrongPass1!');
    await page.getByPlaceholder('Confirm password').fill('StrongPass1!');
    
    // Submit should be enabled
    await expect(submitBtn).toBeEnabled();
  });
});

test.describe('Pricing Page ("prickng" investigation)', () => {
  test('Pricing page should render correctly', async ({ page }) => {
    await page.goto('/pricing');
    
    // Check for main header
    // web/src/pages/Pricing.tsx has "Pricing that pays for itself."
    // Wait, the file I read earlier had "Pricing that <br/> pays for itself."
    await expect(page.getByText('Pricing that')).toBeVisible();
    await expect(page.getByText('pays for itself')).toBeVisible();
    
    // Check for plans
    // The code I read for pages/Pricing.tsx had "Starter", "Pro Hunter", "Agency"
    await expect(page.getByText('Starter')).toBeVisible();
    await expect(page.getByText('Pro Hunter')).toBeVisible();
    await expect(page.getByText('Agency')).toBeVisible();
  });
});
