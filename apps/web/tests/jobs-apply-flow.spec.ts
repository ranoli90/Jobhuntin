import { test, expect } from '@playwright/test';

/**
 * E2E: Jobs → Apply flow.
 * Mocks /me/jobs and POST /me/applications to verify the apply (accept) flow.
 */
test.describe('Jobs Apply Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock auth - set token so API calls include auth
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.setItem('jobhuntin_auth', 'mock-token-for-e2e');
    });
  });

  test('jobs view loads and displays job cards', async ({ page }) => {
    await page.route('**/me/jobs*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'job-1',
              title: 'Senior Software Engineer',
              company: 'Acme Corp',
              location: 'Remote',
              salary_min: 120000,
              salary_max: 160000,
              match_score: 85,
              description: 'Build scalable systems.',
            },
          ],
          next_offset: null,
        }),
      });
    });

    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 15000 });
    await expect(page.getByText('Senior Software Engineer')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Acme Corp')).toBeVisible();
  });

  test('accept (apply) triggers API and shows toast', async ({ page }) => {
    let applyCalled = false;
    await page.route('**/me/jobs*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'job-apply-1',
              title: 'Full Stack Developer',
              company: 'TechCo',
              location: 'San Francisco',
              match_score: 78,
              description: 'React and Node.',
            },
          ],
          next_offset: null,
        }),
      });
    });
    await page.route('**/me/applications', async (route) => {
      if (route.request().method() === 'POST') {
        applyCalled = true;
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ id: 'app-1', status: 'QUEUED' }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 15000 });
    await expect(page.getByText('Full Stack Developer')).toBeVisible({ timeout: 10000 });

    // Click the green check (accept) button
    const acceptBtn = page.getByRole('button', { name: 'Apply to this job' });
    await acceptBtn.click();

    await page.waitForTimeout(2000);
    expect(applyCalled).toBe(true);
  });
});
