import { test, expect, Page } from '@playwright/test';

test.describe('Admin Pages - Usage Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/usage', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display usage analytics page', async ({ page }) => {
    await expect(page.getByText('Tenant Usage Analytics')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total Matches')).toBeVisible();
    await expect(page.getByText('API Calls')).toBeVisible();
    await expect(page.getByText('Active Tenants')).toBeVisible();
  });

  test('should show tenant breakdown table', async ({ page }) => {
    await expect(page.getByText('Tenant Breakdown')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('table')).toBeVisible();
  });

  test('should display quota bars for each tenant', async ({ page }) => {
    await expect(page.getByText('Match Quota')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('API Quota')).toBeVisible();
  });

  test('should show status badges', async ({ page }) => {
    await expect(page.getByText(/Healthy|Warning|Critical/i)).toBeVisible({ timeout: 10000 });
  });

  test('should have date range picker', async ({ page }) => {
    await expect(page.getByRole('group').or(page.locator('input[type="date"]').first())).toBeVisible({ timeout: 10000 });
  });

  test('should allow date range selection', async ({ page }) => {
    const dateInputs = page.locator('input[type="date"]');
    const count = await dateInputs.count();
    
    if (count >= 2) {
      await dateInputs.first().fill('2026-01-01');
      await dateInputs.nth(1).fill('2026-01-31');
    }
  });

  test('should have export functionality', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Export/i })).toBeVisible({ timeout: 10000 });
  });

  test('should show match volume chart', async ({ page }) => {
    await expect(page.getByText('Match Volume')).toBeVisible({ timeout: 10000 });
  });

  test('should show average quota used metric', async ({ page }) => {
    await expect(page.getByText('Avg Quota Used')).toBeVisible({ timeout: 10000 });
  });

  test('should highlight tenants near quota limits', async ({ page }) => {
    await page.route('**/api/admin/usage**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_matches: 15000,
          total_api_calls: 85000,
          period_start: '2026-01-01',
          period_end: '2026-01-31',
          tenants: [
            {
              tenant_id: 't1',
              tenant_name: 'Critical Tenant',
              matches_used: 4800,
              matches_limit: 5000,
              api_calls: 24000,
              api_limit: 25000,
              quota_percentage: 96,
            },
          ],
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('Critical')).toBeVisible({ timeout: 10000 });
  });

  test('should have back navigation', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Back/i })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Admin Pages - Match Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/matches', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display match monitoring page', async ({ page }) => {
    await expect(page.getByText('Match Monitoring')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Total Matches')).toBeVisible();
    await expect(page.getByText('Success Rate')).toBeVisible();
    await expect(page.getByText('Failed Matches')).toBeVisible();
  });

  test('should show matches table with columns', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Job')).toBeVisible();
    await expect(page.getByText('Tenant')).toBeVisible();
    await expect(page.getByText('Score')).toBeVisible();
    await expect(page.getByText('Status')).toBeVisible();
  });

  test('should have search functionality', async ({ page }) => {
    await expect(page.getByPlaceholder(/Search/i)).toBeVisible({ timeout: 10000 });
  });

  test('should have tenant filter dropdown', async ({ page }) => {
    await expect(page.getByRole('combobox').or(page.locator('select'))).toBeVisible({ timeout: 10000 });
  });

  test('should have score range filters', async ({ page }) => {
    await expect(page.getByPlaceholder(/Min/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder(/Max/i)).toBeVisible();
  });

  test('should show dealbreaker indicators', async ({ page }) => {
    await page.route('**/api/admin/matches**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          matches: [
            {
              id: 'm1',
              job_id: 'j1',
              job_title: 'Software Engineer',
              company: 'Test Co',
              tenant_id: 't1',
              tenant_name: 'Test Tenant',
              user_id: 'u1',
              score: 45,
              passed_dealbreakers: false,
              status: 'completed',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          per_page: 20,
          success_rate: 95,
        }),
      });
    });

    await page.reload();
    await expect(page.locator('[class*="amber"], [class*="warning"]').or(page.getByText(/!|⚠/))).toBeVisible({ timeout: 10000 });
  });

  test('should have pagination', async ({ page }) => {
    await page.route('**/api/admin/matches**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          matches: Array.from({ length: 20 }, (_, i) => ({
            id: `m${i}`,
            job_id: `j${i}`,
            job_title: `Job ${i}`,
            company: `Company ${i}`,
            tenant_id: 't1',
            tenant_name: 'Tenant',
            user_id: 'u1',
            score: 80,
            passed_dealbreakers: true,
            status: 'completed',
            created_at: new Date().toISOString(),
          })),
          total: 100,
          page: 1,
          per_page: 20,
          success_rate: 98,
        }),
      });
    });

    await page.reload();
    await expect(page.getByRole('button', { name: /Next/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /Previous/i })).toBeVisible();
  });

  test('should allow score override', async ({ page }) => {
    await page.route('**/api/admin/matches**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          matches: [
            {
              id: 'm1',
              job_id: 'j1',
              job_title: 'Test Job',
              company: 'Test Co',
              tenant_id: 't1',
              tenant_name: 'Test',
              user_id: 'u1',
              score: 75,
              passed_dealbreakers: true,
              status: 'completed',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          per_page: 20,
          success_rate: 100,
        }),
      });
    });

    await page.reload();
    await expect(page.getByRole('table')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Admin Pages - Alerts', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin/alerts', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('should display alerts page', async ({ page }) => {
    await expect(page.getByText('Real-time Alerts')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/active/i)).toBeVisible();
  });

  test('should show active and historical tabs', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Active/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /Historical/i })).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.getByRole('button', { name: /Historical/i }).click();
    await expect(page.getByRole('button', { name: /Historical/i }).or(page.locator('[class*="active"]'))).toBeVisible({ timeout: 5000 });
  });

  test('should show alert cards with severity indicators', async ({ page }) => {
    await expect(page.locator('[class*="red"], [class*="critical"]').or(page.getByText(/critical|warning|info/i))).toBeVisible({ timeout: 10000 });
  });

  test('should have severity filter', async ({ page }) => {
    await expect(page.getByRole('combobox').or(page.locator('select'))).toBeVisible({ timeout: 10000 });
  });

  test('should have status filter', async ({ page }) => {
    const selects = page.locator('select');
    const count = await selects.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('should show acknowledge buttons for active alerts', async ({ page }) => {
    await page.route('**/api/admin/alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          active: [
            {
              id: 'a1',
              type: 'warning',
              title: 'Test Alert',
              message: 'This is a test alert',
              tenant_id: 't1',
              tenant_name: 'Test Tenant',
              status: 'active',
              created_at: new Date().toISOString(),
              acknowledged_at: null,
              acknowledged_by: null,
            },
          ],
          historical: [],
        }),
      });
    });

    await page.reload();
    await expect(page.getByRole('button', { name: /Acknowledge/i })).toBeVisible({ timeout: 10000 });
  });

  test('should handle acknowledge action', async ({ page }) => {
    await page.route('**/api/admin/alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          active: [
            {
              id: 'a1',
              type: 'info',
              title: 'Test Alert',
              message: 'Test message',
              tenant_id: 't1',
              tenant_name: 'Test',
              status: 'active',
              created_at: new Date().toISOString(),
              acknowledged_at: null,
              acknowledged_by: null,
            },
          ],
          historical: [],
        }),
      });
    });

    await page.route('**/api/admin/alerts/a1/acknowledge', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true }),
      });
    });

    await page.reload();
    await page.getByRole('button', { name: /Acknowledge/i }).click({ timeout: 10000 });
  });

  test('should show empty state when no alerts', async ({ page }) => {
    await page.route('**/api/admin/alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          active: [],
          historical: [],
        }),
      });
    });

    await page.reload();
    await expect(page.getByText(/No Active Alerts|All systems operating/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display alert timestamps', async ({ page }) => {
    await expect(page.locator('time').or(page.getByText(/\d{4}/))).toBeVisible({ timeout: 10000 });
  });

  test('should show tenant information for each alert', async ({ page }) => {
    await page.route('**/api/admin/alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          active: [
            {
              id: 'a1',
              type: 'warning',
              title: 'Test Alert',
              message: 'Test message',
              tenant_id: 't1',
              tenant_name: 'Acme Corp',
              status: 'active',
              created_at: new Date().toISOString(),
              acknowledged_at: null,
              acknowledged_by: null,
            },
          ],
          historical: [],
        }),
      });
    });

    await page.reload();
    await expect(page.getByText('Acme Corp')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Admin Pages - Navigation', () => {
  test('should navigate back from usage page', async ({ page }) => {
    await page.goto('/admin/usage', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /Back/i }).click();
    await page.waitForURL(/.*\/(admin|app).*/, { timeout: 10000 });
  });

  test('should navigate back from matches page', async ({ page }) => {
    await page.goto('/admin/matches', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /Back/i }).click();
    await page.waitForURL(/.*\/(admin|app).*/, { timeout: 10000 });
  });

  test('should navigate back from alerts page', async ({ page }) => {
    await page.goto('/admin/alerts', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /Back/i }).click();
    await page.waitForURL(/.*\/(admin|app).*/, { timeout: 10000 });
  });
});
