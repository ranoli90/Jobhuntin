import { test, expect, Page } from '@playwright/test';

test.setTimeout(60000);

test.describe('Onboarding AI Flow', () => {
  test('should display AI suggestions during onboarding', async ({ page }) => {
    // Navigate to the login page and create a new user
    await page.goto('/login/register', { waitUntil: 'networkidle' });

    const email = `testuser-${Date.now()}@example.com`;
    await page.getByPlaceholder('tech-wizard@example.com').fill(email);
    await page.getByPlaceholder('Create a strong password').fill('StrongP@ss1!');
    await page.getByPlaceholder('Confirm password').fill('StrongP@ss1!');
    await page.getByRole('button', { name: /Create Account/i }).click();

    // Wait for the confirmation email screen
    await expect(page.getByText('Confirm your email')).toBeVisible({ timeout: 10000 });

    // In a real test, we would get the magic link from the email.
    // For this test, we will simulate the user clicking the magic link by navigating to the onboarding page.
    await page.goto('/app/onboarding', { waitUntil: 'networkidle' });

    // Onboarding step 1: Welcome
    await expect(page.getByText('Welcome to your new command center')).toBeVisible();
    await page.getByRole('button', { name: /Let's Go/i }).click();

    // Onboarding step 2: Resume Upload
    await expect(page.getByText('Upload your resume')).toBeVisible();

    // Mock the resume upload
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByRole('button', { name: /Upload Resume/i }).click(),
    ]);
    await fileChooser.setFiles({
      name: 'resume.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('dummy resume content'),
    });

    // Mock the resume parse API response
    await page.route('**/api/webhook/resume_parse', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_id: 'test-user-id',
          profile: {
            contact: { full_name: 'Test User' },
            experience: [{ title: 'Software Engineer' }],
            skills: ['TypeScript', 'React', 'Node.js'],
          },
          resume_url: 'https://example.com/resume.pdf',
        }),
      });
    });

    // After upload, it should navigate to the skill review step
    await expect(page.getByText('Review Your Skills')).toBeVisible({ timeout: 15000 });

    // Verify AI-suggested skills are displayed
    await expect(page.getByText('TypeScript')).toBeVisible();
    await expect(page.getByText('React')).toBeVisible();
    await expect(page.getByText('Node.js')).toBeVisible();

    // Onboarding step 3: Skill Review
    await page.getByRole('button', { name: /Next/i }).click();

    // Onboarding step 4: Role Preferences
    await expect(page.getByText('What are your target roles?')).toBeVisible();

    // Verify AI-suggested roles are displayed
    await expect(page.getByText('Software Engineer')).toBeVisible();
    await page.getByRole('button', { name: /Next/i }).click();

    // Onboarding step 5: Work Style
    await expect(page.getByText('How do you like to work?')).toBeVisible();
    await page.getByRole('button', { name: /Next/i }).click();

    // Onboarding step 6: Ready
    await expect(page.getByText("You're all set!")).toBeVisible();
    await page.getByRole('button', { name: /Go to Dashboard/i }).click();

    // Verify navigation to the dashboard
    await page.waitForURL('**/app/dashboard**', { timeout: 15000 });
    expect(page.url()).toContain('/app/dashboard');
  });
});
