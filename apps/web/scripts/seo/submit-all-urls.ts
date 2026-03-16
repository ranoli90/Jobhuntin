/**
 * submit-all-urls.ts
 * 
 * Quick script to submit all existing URLs from sitemaps to Google Indexing API
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { google } from 'googleapis';

import {
  dedupeUrls,
  getSubmissionDeduplicationWindowMs,
  shouldSkipRecentlySubmittedUrl,
  trackUrlSubmission,
} from './deduplication';
import { SEOError, SEO_ERROR_CODES } from './errors';
import { seoLogger } from './logger';
import { getMetricsCollector, incrementCounter, recordTimer, SEO_METRIC_NAMES } from './metrics';
import { closeSharedDatabaseConnection, PersistedSEOJobTracker } from './persistence';
import { retry, sleep } from './retry';
import { validateUrlBatch } from './validators';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = process.env.GOOGLE_SEARCH_CONSOLE_SITE || 'https://jobhuntin.com';
const logger = seoLogger.child({ script: 'submit-all-urls' });
const GOOGLE_AUTH_TIMEOUT_MS = 20_000;
const GOOGLE_SUBMISSION_TIMEOUT_MS = 15_000;
const GOOGLE_SUBMISSION_RETRIES = 2;

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function normalizeGoogleOperationError(
  error: unknown,
  operation: string,
  context: Record<string, unknown>
): Error {
  if (error instanceof SEOError) {
    return error;
  }

  const originalError = error instanceof Error ? error : new Error(String(error));
  const message = toErrorMessage(error).toLowerCase();
  const retryable =
    message.includes('timeout') ||
    message.includes('timed out') ||
    message.includes('network') ||
    message.includes('socket hang up') ||
    message.includes('econnreset') ||
    message.includes('503') ||
    message.includes('502') ||
    message.includes('429');

  const code = operation === 'authorize'
    ? SEO_ERROR_CODES.GOOGLE_AUTH_ERROR
    : SEO_ERROR_CODES.GOOGLE_API_ERROR;

  return new SEOError(
    code,
    `${operation} failed: ${originalError.message}`,
    {
      retryable,
      originalError,
      context,
    }
  );
}

async function main() {
  let tracker: PersistedSEOJobTracker | null = null;

  try {
    console.log('🚀 SUBMITTING ALL EXISTING URLS TO GOOGLE');
    console.log('='.repeat(60));
    console.log("📍 Site:", BASE_URL);
    console.log("⏰ Started:", new Date().toISOString());
    console.log('');

    // Extract URLs from all sitemaps
    const sitemapDir = path.resolve(__dirname, '../../public');
    const sitemapFiles = fs.readdirSync(sitemapDir).filter(f => f.startsWith('sitemap') && f.endsWith('.xml'));

    const allUrls: string[] = [];

    for (const file of sitemapFiles) {
      const content = fs.readFileSync(path.join(sitemapDir, file), 'utf-8');
      const matches = content.match(/<loc>(.*?)<\/loc>/g) || [];
      const urls = matches.map(m => m.replace(/<\/?loc>/g, ''));
      allUrls.push(...urls);
      console.log("📄", file + ":", urls.length, "URLs");
    }

    console.log("\n📊 Total URLs found:", allUrls.length);

    const { uniqueUrls, duplicateCount } = dedupeUrls(allUrls);
    const validatedUrls = validateUrlBatch(uniqueUrls);
    const dedupeWindowMs = getSubmissionDeduplicationWindowMs();
    const skippedResults: UrlSubmissionResult[] = [];
    const pendingUrls = validatedUrls.filter(url => {
      if (!shouldSkipRecentlySubmittedUrl(url, dedupeWindowMs, { script: 'submit-all-urls' })) {
        return true;
      }

      skippedResults.push({ url, status: 'skipped_recent_duplicate', timestamp: new Date().toISOString() });
      return false;
    });

    console.log("📊 Unique URLs:", validatedUrls.length);
    console.log("📊 Duplicate URLs suppressed in-process:", duplicateCount);
    console.log("📊 Recently submitted URLs skipped:", skippedResults.length);

    tracker = await PersistedSEOJobTracker.create({
      script: 'submit-all-urls',
      logger,
      payload: {
        baseUrl: BASE_URL,
        sitemapFiles,
        discoveredUrls: allUrls.length,
        uniqueUrls: validatedUrls.length,
        duplicateCount,
        skippedRecentDuplicates: skippedResults.length,
        argv: process.argv.slice(2),
      },
    });
    await tracker.progress('prepare', 10, 'Prepared sitemap URLs for submission', {
      sitemapFileCount: sitemapFiles.length,
      discoveredUrls: allUrls.length,
      uniqueUrls: validatedUrls.length,
      duplicateCount,
      skippedRecentDuplicates: skippedResults.length,
    });

    if (pendingUrls.length === 0) {
      logger.info('No URLs remain after deduplication checks', { duplicateCount, skippedRecent: skippedResults.length });
      await tracker.info('No URLs remain after deduplication checks', {
        duplicateCount,
        skippedRecent: skippedResults.length,
      }, 'submit-all-urls:no-op');
      await tracker.complete({
        totalDiscoveredUrls: allUrls.length,
        totalEligibleUrls: validatedUrls.length,
        duplicateUrlsSuppressed: duplicateCount,
        skippedRecentDuplicates: skippedResults.length,
        submittedUrls: 0,
        success: 0,
        errors: 0,
        status: 'noop',
      });
      console.log('\n✅ No new URLs to submit after deduplication checks.');
      return;
    }

    // Check for Google credentials
    const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
    if (!keyEnv) {
      throw new Error('GOOGLE_SERVICE_ACCOUNT_KEY not set');
    }

    // Parse credentials
    let keyContent;
    try {
      keyContent = JSON.parse(keyEnv);
      console.log("✅ Service account:", keyContent.client_email);
    } catch {
      // Try as file path
      try {
        keyContent = JSON.parse(fs.readFileSync(keyEnv, "utf8"));
        console.log("✅ Service account:", keyContent.client_email);
      } catch (e) {
        throw new Error('Could not parse GOOGLE_SERVICE_ACCOUNT_KEY');
      }
    }

    // Create JWT client
    const jwtClient = new google.auth.JWT({
      email: keyContent.client_email,
      key: keyContent.private_key,
      scopes: ['https://www.googleapis.com/auth/indexing']
    });

    console.log('\n🔐 Authenticating with Google...');
    await retry(
      async () => {
        try {
          await jwtClient.authorize();
        } catch (error) {
          throw normalizeGoogleOperationError(error, 'authorize', {
            script: 'submit-all-urls',
            clientEmail: keyContent.client_email,
          });
        }
      },
      {
        maxRetries: 1,
        baseDelay: 1000,
        timeout: GOOGLE_AUTH_TIMEOUT_MS,
        onRetry: async (attempt, error) => {
          incrementCounter(SEO_METRIC_NAMES.API_RETRY_COUNT, 1, { script: 'submit-all-urls' });
          logger.warn('Retrying Google authorization', {
            attempt,
            error: toErrorMessage(error),
          });
        },
      },
      'submit-all-urls-auth'
    );
    logger.info('Authenticated with Google Indexing API', {
      urlCount: pendingUrls.length,
      dailyLimit: 200,
    });
    await tracker.progress('authenticate', 20, 'Authenticated with Google Indexing API', {
      pendingUrls: pendingUrls.length,
      dailyLimit: 200,
      clientEmail: keyContent.client_email,
    });
    await tracker.info('Authenticated with Google Indexing API', {
      pendingUrls: pendingUrls.length,
      dailyLimit: 200,
      clientEmail: keyContent.client_email,
    }, 'submit-all-urls:authenticate');
    console.log('✅ Authenticated!');

    const indexing = google.indexing({ version: 'v3', auth: jwtClient });

    // Google limits: 200 URLs per day
    const dailyLimit = 200;
    const urlsToSubmit = pendingUrls.slice(0, dailyLimit);
    const quotaSkipped = pendingUrls.length - urlsToSubmit.length;

    console.log("\n📤 Submitting", urlsToSubmit.length, "URLs (daily limit:", dailyLimit + ")");
    if (quotaSkipped > 0) {
      console.log("📊 Remaining URLs deferred by daily limit:", quotaSkipped);
    }
    console.log('='.repeat(60));
    await tracker.progress('submission', 25, 'Submitting URLs to Google', {
      urlsToSubmit: urlsToSubmit.length,
      deferredByDailyLimit: quotaSkipped,
    });

    let successCount = 0;
    let errorCount = 0;
    const results: UrlSubmissionResult[] = [...skippedResults];

    for (let i = 0; i < urlsToSubmit.length; i++) {
      const url = urlsToSubmit[i];

      try {
        const startedAt = Date.now();
        process.stdout.write(`[${i + 1}/${urlsToSubmit.length}] ${url.substring(0, 60)}... `);

        await retry(
          async () => {
            try {
              return await indexing.urlNotifications.publish({
                requestBody: {
                  url: url,
                  type: 'URL_UPDATED'
                }
              });
            } catch (error) {
              throw normalizeGoogleOperationError(error, 'urlNotifications.publish', {
                script: 'submit-all-urls',
                url,
              });
            }
          },
          {
            maxRetries: GOOGLE_SUBMISSION_RETRIES,
            baseDelay: 1000,
            maxDelay: 5000,
            timeout: GOOGLE_SUBMISSION_TIMEOUT_MS,
            onRetry: async (attempt, error) => {
              incrementCounter(SEO_METRIC_NAMES.API_RETRY_COUNT, 1, { script: 'submit-all-urls' });
              logger.warn('Retrying URL submission', {
                url,
                attempt,
                error: toErrorMessage(error),
              });
            },
          },
          'submit-all-urls-publish'
        );

        console.log('✅');
        successCount++;
        incrementCounter(SEO_METRIC_NAMES.URLS_SUBMITTED, 1, { script: 'submit-all-urls' });
        recordTimer(SEO_METRIC_NAMES.URL_SUBMISSION_TIME, Date.now() - startedAt, { script: 'submit-all-urls' });
        trackUrlSubmission(url, 'success', { script: 'submit-all-urls' });
        await tracker.trackUrl(url, 'success', {
          stage: 'submission',
          sequence: i + 1,
        });
        results.push({ url, status: 'success', timestamp: new Date().toISOString() });

        // Rate limit: 1 second between requests
        if (i < urlsToSubmit.length - 1) {
          await sleep(1000);
        }

        const processedCount = successCount + errorCount;
        if (processedCount === urlsToSubmit.length || processedCount % 10 === 0) {
          await tracker.progress(
            'submission',
            Math.min(99, Math.round((processedCount / urlsToSubmit.length) * 100)),
            `Processed ${processedCount} of ${urlsToSubmit.length} URLs`,
            {
              processedCount,
              totalUrls: urlsToSubmit.length,
              successCount,
              errorCount,
              deferredByDailyLimit: quotaSkipped,
            }
          );
        }

      } catch (error: any) {
        console.log("❌", error.message);
        errorCount++;
        logger.error('URL submission failed', undefined, {
          url,
          error: toErrorMessage(error),
        });
        incrementCounter(SEO_METRIC_NAMES.URLS_FAILED, 1, { script: 'submit-all-urls' });
        trackUrlSubmission(url, 'error', { script: 'submit-all-urls', error: error.message });
        await tracker.trackUrl(url, 'error', {
          stage: 'submission',
          sequence: i + 1,
          error: toErrorMessage(error),
        });
        await tracker.error('URL submission failed', error, {
          url,
          sequence: i + 1,
        }, 'submit-all-urls:submit-url');
        results.push({ url, status: 'error', error: error.message, timestamp: new Date().toISOString() });
      }
    }

    // Save results
    const logDir = path.resolve(__dirname, '../../logs');
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    const logPath = path.join(logDir, `submission-${Date.now()}.json`);
    fs.writeFileSync(logPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      total: urlsToSubmit.length,
      duplicateUrlsSuppressed: duplicateCount,
      skippedRecentDuplicates: skippedResults.length,
      deferredByDailyLimit: quotaSkipped,
      success: successCount,
      errors: errorCount,
      results
    }, null, 2));

    console.log('\n' + '='.repeat(60));
    console.log('📊 SUBMISSION COMPLETE');
    console.log('='.repeat(60));
    console.log("✅ Success:", successCount);
    console.log("❌ Errors:", errorCount);
    console.log("📝 Log:", logPath);
    console.log("\n⏰ URLs will be indexed within 24-48 hours.");
    console.log("📈 Check status at: https://search.google.com/search-console");
    await tracker.snapshotMetrics(getMetricsCollector(), {
      flow: 'submit-all-urls',
      totalUrls: urlsToSubmit.length,
      deferredByDailyLimit: quotaSkipped,
    });
    await tracker.complete({
      totalDiscoveredUrls: allUrls.length,
      totalEligibleUrls: validatedUrls.length,
      duplicateUrlsSuppressed: duplicateCount,
      skippedRecentDuplicates: skippedResults.length,
      deferredByDailyLimit: quotaSkipped,
      submittedUrls: urlsToSubmit.length,
      success: successCount,
      errors: errorCount,
      logPath,
    });
  } catch (error) {
    if (tracker) {
      await tracker.snapshotMetrics(getMetricsCollector(), {
        flow: 'submit-all-urls',
      });
      await tracker.fail(error, {
        flow: 'submit-all-urls',
      });
    }

    throw error;
  } finally {
    await closeSharedDatabaseConnection();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
