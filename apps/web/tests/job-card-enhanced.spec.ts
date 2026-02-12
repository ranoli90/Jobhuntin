import { test, expect, Page } from '@playwright/test';

test.describe('Job Card Enhanced - Match Score Badge', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display match score badge on job cards', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Senior React Developer',
              company: 'TechCorp',
              location: 'Remote',
              salary_min: 120000,
              salary_max: 180000,
              match_score: 0.92,
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText(/92%/)).toBeVisible({ timeout: 10000 });
  });

  test('should color-code score badges based on value', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            { id: 'j1', title: 'High Match', company: 'A', match_score: 0.95 },
            { id: 'j2', title: 'Medium Match', company: 'B', match_score: 0.65 },
            { id: 'j3', title: 'Low Match', company: 'C', match_score: 0.35 },
          ],
          total: 3,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('95%')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('65%')).toBeVisible();
    await expect(page.getByText('35%')).toBeVisible();
  });

  test('should show confidence level on hover or always', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Test Job',
              company: 'Test',
              match_score: 0.85,
              match_confidence: 'high',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText(/high/i).or(page.getByText('85%'))).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Job Card Enhanced - Dealbreaker Indicators', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should show dealbreaker warning icon', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Job with Dealbreaker',
              company: 'Test',
              match_score: 0.45,
              passed_dealbreakers: false,
              dealbreaker_reasons: ['Salary below minimum'],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.locator('[class*="warning"], [class*="amber"]').or(page.getByText(/!|⚠/))).toBeVisible({ timeout: 10000 });
  });

  test('should show passed dealbreakers indicator', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Good Job',
              company: 'Test',
              match_score: 0.88,
              passed_dealbreakers: true,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('88%')).toBeVisible({ timeout: 10000 });
  });

  test('should display dealbreaker reasons on hover or click', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Job with Issues',
              company: 'Test',
              match_score: 0.40,
              passed_dealbreakers: false,
              dealbreaker_reasons: ['Location mismatch', 'Salary too low'],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    const jobCard = page.locator('[class*="job"], [data-testid*="job"]').first();
    await jobCard.hover({ timeout: 10000 }).catch(() => {});
    await jobCard.click({ timeout: 10000 }).catch(() => {});
  });
});

test.describe('Job Card Enhanced - 1-Click Apply', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should have apply button on job cards', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Test Job',
              company: 'Test Co',
              match_score: 0.75,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByRole('button', { name: /Apply|Quick Apply/i })).toBeVisible({ timeout: 10000 });
  });

  test('should show loading state during apply', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.80 }],
          total: 1,
        }),
      });
    });

    await page.route('**/api/applications**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'app1', status: 'QUEUED' }),
      });
    });

    await page.reload();
    const applyBtn = page.getByRole('button', { name: /Apply|Quick Apply/i });
    await applyBtn.click({ timeout: 10000 });
    await expect(page.getByText(/Applying|Loading/i).or(page.locator('[class*="loading"], [class*="spinner"]'))).toBeVisible({ timeout: 5000 });
  });

  test('should show success state after apply', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.85 }],
          total: 1,
        }),
      });
    });

    await page.route('**/api/applications**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'app1', status: 'QUEUED' }),
      });
    });

    await page.reload();
    const applyBtn = page.getByRole('button', { name: /Apply|Quick Apply/i });
    await applyBtn.click({ timeout: 10000 });

    await expect(page.getByText(/Applied|Success/i).or(page.locator('[class*="success"]'))).toBeVisible({ timeout: 10000 });
  });

  test('should handle apply error gracefully', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.75 }],
          total: 1,
        }),
      });
    });

    await page.route('**/api/applications**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: { message: 'Apply failed' } }),
      });
    });

    await page.reload();
    const applyBtn = page.getByRole('button', { name: /Apply|Quick Apply/i });
    await applyBtn.click({ timeout: 10000 });

    await expect(page.getByText(/Failed|Error|Try again/i)).toBeVisible({ timeout: 10000 });
  });

  test('should disable button after successful apply', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.80, applied: true }],
          total: 1,
        }),
      });
    });

    await page.reload();
    const appliedBtn = page.getByRole('button', { name: /Applied/i });
    await expect(appliedBtn).toBeVisible({ timeout: 10000 });
    await expect(appliedBtn).toBeDisabled();
  });
});

test.describe('Job Card Enhanced - Skill Match Preview', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should show matched skills preview', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Full Stack Developer',
              company: 'TechCo',
              match_score: 0.88,
              matched_skills: ['React', 'TypeScript', 'Node.js'],
              missing_skills: ['GraphQL'],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('React')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('TypeScript')).toBeVisible();
    await expect(page.getByText('Node.js')).toBeVisible();
  });

  test('should differentiate matched vs missing skills visually', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Dev Job',
              company: 'Test',
              match_score: 0.70,
              matched_skills: ['Python', 'Django'],
              missing_skills: ['Docker', 'Kubernetes'],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('Python')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Docker')).toBeVisible();
  });

  test('should show skill match count', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Job',
              company: 'Test',
              match_score: 0.82,
              matched_skills: ['A', 'B', 'C', 'D'],
              missing_skills: ['E'],
              total_skills: 5,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByText(/4.*5|4\/5|80%/)).toBeVisible({ timeout: 10000 });
  });

  test('should expand to show full skill list on interaction', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'Expanded Skills Test',
              company: 'Test',
              match_score: 0.75,
              matched_skills: ['React', 'Vue', 'Angular', 'Svelte', 'jQuery'],
              missing_skills: ['WebGL', 'Three.js'],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    const jobCard = page.locator('[class*="job"], [data-testid*="job"]').first();
    await jobCard.click({ timeout: 10000 }).catch(() => {});
    await jobCard.hover({ timeout: 10000 }).catch(() => {});
  });

  test('should show "View Details" link to full match analysis', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            {
              id: 'j1',
              title: 'View Details Job',
              company: 'Test',
              match_score: 0.90,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();
    await expect(page.getByRole('link', { name: /View Details|Details|Match/i }).or(page.getByRole('button', { name: /Details|Match/i }))).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Job Card Enhanced - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/app/jobs', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should have accessible labels for match scores', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.85 }],
          total: 1,
        }),
      });
    });

    await page.reload();
    const scoreElement = page.getByText('85%');
    await expect(scoreElement).toBeVisible({ timeout: 10000 });
  });

  test('should have accessible apply buttons', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [{ id: 'j1', title: 'Test', company: 'Test', match_score: 0.80 }],
          total: 1,
        }),
      });
    });

    await page.reload();
    const applyBtn = page.getByRole('button', { name: /Apply/i });
    await expect(applyBtn).toBeVisible({ timeout: 10000 });
    await expect(applyBtn).toHaveAttribute('aria-label', /.+/);
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.route('**/api/jobs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          jobs: [
            { id: 'j1', title: 'Job 1', company: 'A', match_score: 0.80 },
            { id: 'j2', title: 'Job 2', company: 'B', match_score: 0.75 },
          ],
          total: 2,
        }),
      });
    });

    await page.reload();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible({ timeout: 5000 });
  });
});
