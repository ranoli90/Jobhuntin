import { expect, type Page, type TestInfo } from '@playwright/test';
import path from 'path';

export async function takeFullPageScreenshot(page: Page, testInfo: TestInfo) {
  const screenshotPath = path.join('baselines', `${testInfo.title.replace(/[^a-z0-9]+/gi, '_')}.png`);
  await expect(page).toHaveScreenshot({ fullPage: true, path: screenshotPath });
}
