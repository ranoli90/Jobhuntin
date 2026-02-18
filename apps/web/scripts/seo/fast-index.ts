/**
 * fast-index.ts — Multi-method fast indexing for all 1,600+ URLs
 * 
 * Strategy:
 *   1. Google Indexing API (200/day limit) — highest priority URLs first
 *   2. Sitemap ping to Google & Bing — triggers re-crawl of all sitemaps
 *   3. IndexNow API (Bing/Yandex) — instant indexing, no daily limit
 *   4. Tracks progress across runs so it resumes where it left off
 * 
 * Usage:
 *   npx tsx scripts/seo/fast-index.ts                    # Full run
 *   npx tsx scripts/seo/fast-index.ts --dry-run          # Preview
 *   npx tsx scripts/seo/fast-index.ts --ping-only        # Just ping sitemaps
 *   npx tsx scripts/seo/fast-index.ts --indexnow-only    # Just IndexNow
 *   npx tsx scripts/seo/fast-index.ts --reset            # Reset progress tracker
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import https from 'https';
import http from 'http';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = process.env.GOOGLE_SEARCH_CONSOLE_SITE || 'https://jobhuntin.com';
const LOGS_DIR = path.resolve(__dirname, '../../logs');
const PROGRESS_FILE = path.join(LOGS_DIR, 'indexing-progress.json');

// ─── CLI Args ────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const PING_ONLY = args.includes('--ping-only');
const INDEXNOW_ONLY = args.includes('--indexnow-only');
const RESET = args.includes('--reset');

// ─── Structured Logger ───────────────────────────────────────────────────────
function log(category: string, message: string): void {
  const ts = new Date().toISOString();
  console.log(`[${ts}] [FAST-INDEX:${category}] ${message}`);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function httpGet(url: string): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, (res) => {
      let body = '';
      res.on('data', (chunk: Buffer) => { body += chunk.toString(); });
      res.on('end', () => resolve({ status: res.statusCode || 0, body }));
    }).on('error', reject);
  });
}

function httpPost(url: string, data: string, headers: Record<string, string>): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const mod = parsed.protocol === 'https:' ? https : http;
    const req = mod.request({
      hostname: parsed.hostname,
      port: parsed.port,
      path: parsed.pathname + parsed.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...headers },
    }, (res) => {
      let body = '';
      res.on('data', (chunk: Buffer) => { body += chunk.toString(); });
      res.on('end', () => resolve({ status: res.statusCode || 0, body }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

// ─── Load all URLs from sitemaps ─────────────────────────────────────────────
function loadAllUrlsFromSitemaps(): string[] {
  const sitemapDir = path.resolve(__dirname, '../../public');
  const sitemapFiles = fs.readdirSync(sitemapDir)
    .filter((f: string) => f.startsWith('sitemap') && f.endsWith('.xml') && f !== 'sitemap.xml');

  const allUrls: string[] = [];
  for (const file of sitemapFiles) {
    const content = fs.readFileSync(path.join(sitemapDir, file), 'utf-8');
    const matches = content.match(/<loc>(.*?)<\/loc>/g) || [];
    const urls = matches.map((m: string) => m.replace(/<\/?loc>/g, ''));
    allUrls.push(...urls);
    log('SITEMAP', `${file}: ${urls.length} URLs`);
    // Log first 3 URLs from each sitemap as samples
    urls.slice(0, 3).forEach((u: string) => log('SITEMAP', `  sample: ${u}`));
    if (urls.length > 3) log('SITEMAP', `  ... and ${urls.length - 3} more`);
  }
  return [...new Set(allUrls)];
}

// ─── Progress Tracker ────────────────────────────────────────────────────────
interface Progress {
  googleApiSubmitted: string[];
  indexNowSubmitted: string[];
  lastGoogleRun: string | null;
  lastIndexNowRun: string | null;
  lastPingRun: string | null;
  totalUrls: number;
}

function loadProgress(): Progress {
  if (RESET || !fs.existsSync(PROGRESS_FILE)) {
    return { googleApiSubmitted: [], indexNowSubmitted: [], lastGoogleRun: null, lastIndexNowRun: null, lastPingRun: null, totalUrls: 0 };
  }
  try {
    return JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf-8'));
  } catch {
    return { googleApiSubmitted: [], indexNowSubmitted: [], lastGoogleRun: null, lastIndexNowRun: null, lastPingRun: null, totalUrls: 0 };
  }
}

function saveProgress(progress: Progress) {
  ensureDir(LOGS_DIR);
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
}

// ─── Method 1: Sitemap Ping ─────────────────────────────────────────────────
async function pingSitemaps(): Promise<void> {
  log('PING', '═══════════════════════════════════════════════════');
  log('PING', 'METHOD 1: SITEMAP PING (Google + Bing)');
  log('PING', '═══════════════════════════════════════════════════');

  const sitemapUrl = encodeURIComponent(`${BASE_URL}/sitemap.xml`);
  const pingTargets = [
    { name: 'Google', url: `https://www.google.com/ping?sitemap=${sitemapUrl}` },
    { name: 'Bing', url: `https://www.bing.com/ping?sitemap=${sitemapUrl}` },
  ];

  for (const target of pingTargets) {
    const start = Date.now();
    try {
      if (DRY_RUN) {
        log('PING', `[DRY] Would ping ${target.name}: ${target.url}`);
        continue;
      }
      const res = await httpGet(target.url);
      const ms = Date.now() - start;
      log('PING', `${res.status === 200 ? '✅' : '⚠️'} ${target.name} → HTTP ${res.status} (${ms}ms) | ${target.url}`);
    } catch (err: any) {
      const ms = Date.now() - start;
      log('PING', `❌ ${target.name} → FAILED (${ms}ms) | ${err.message}`);
    }
  }
}

// ─── Method 2: IndexNow (Bing, Yandex, Seznam, Naver) ──────────────────────
async function submitIndexNow(urls: string[], progress: Progress): Promise<number> {
  log('INDEXNOW', '═══════════════════════════════════════════════════');
  log('INDEXNOW', 'METHOD 2: INDEXNOW API (Bing + Yandex + Seznam)');
  log('INDEXNOW', '═══════════════════════════════════════════════════');

  // Filter out already-submitted URLs
  const submittedSet = new Set(progress.indexNowSubmitted);
  const pending = urls.filter(u => !submittedSet.has(u));
  log('INDEXNOW', `Total: ${urls.length} | Already submitted: ${progress.indexNowSubmitted.length} | Pending: ${pending.length}`);

  if (pending.length === 0) {
    log('INDEXNOW', '✅ All URLs already submitted via IndexNow');
    return 0;
  }

  // Log sample of pending URLs
  log('INDEXNOW', 'Sample pending URLs:');
  pending.slice(0, 5).forEach((u, i) => log('INDEXNOW', `  ${i + 1}. ${u}`));
  if (pending.length > 5) log('INDEXNOW', `  ... and ${pending.length - 5} more`);

  const host = new URL(BASE_URL).hostname;
  const indexNowKey = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6';

  // Ensure the key file exists in public dir for verification
  const keyFilePath = path.resolve(__dirname, `../../public/${indexNowKey}.txt`);
  if (!fs.existsSync(keyFilePath)) {
    fs.writeFileSync(keyFilePath, indexNowKey);
    log('INDEXNOW', `Created IndexNow key file: public/${indexNowKey}.txt`);
  }

  const engines = [
    'https://api.indexnow.org/indexnow',
    'https://www.bing.com/indexnow',
    'https://yandex.com/indexnow',
  ];

  let totalSubmitted = 0;
  const BATCH_SIZE = 500;

  for (let i = 0; i < pending.length; i += BATCH_SIZE) {
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(pending.length / BATCH_SIZE);
    const batch = pending.slice(i, i + BATCH_SIZE);
    const payload = JSON.stringify({
      host,
      key: indexNowKey,
      keyLocation: `${BASE_URL}/${indexNowKey}.txt`,
      urlList: batch,
    });

    log('INDEXNOW', `Batch ${batchNum}/${totalBatches}: ${batch.length} URLs (${batch[0]} ... ${batch[batch.length - 1]})`);

    for (const engine of engines) {
      const start = Date.now();
      try {
        if (DRY_RUN) {
          log('INDEXNOW', `[DRY] Would submit ${batch.length} URLs to ${engine}`);
          continue;
        }
        const res = await httpPost(engine, payload, {});
        const ms = Date.now() - start;
        const ok = res.status >= 200 && res.status < 300;
        log('INDEXNOW', `${ok ? '✅' : '⚠️'} ${engine} → HTTP ${res.status} (${ms}ms) | ${batch.length} URLs`);
        if (!ok) log('INDEXNOW', `  Response body: ${res.body.slice(0, 200)}`);
        if (ok) {
          totalSubmitted += batch.length;
          progress.indexNowSubmitted.push(...batch);
        }
      } catch (err: any) {
        const ms = Date.now() - start;
        log('INDEXNOW', `❌ ${engine} → FAILED (${ms}ms) | ${err.message}`);
      }
    }

    if (i + BATCH_SIZE < pending.length) await sleep(1000);
  }

  progress.lastIndexNowRun = new Date().toISOString();
  log('INDEXNOW', `Done: ${totalSubmitted} URLs submitted across all engines`);
  return totalSubmitted;
}

// ─── Method 3: Google Indexing API ──────────────────────────────────────────
async function submitGoogleIndexingApi(urls: string[], progress: Progress): Promise<number> {
  log('GOOGLE', '═══════════════════════════════════════════════════');
  log('GOOGLE', 'METHOD 3: GOOGLE INDEXING API (200/day limit)');
  log('GOOGLE', '═══════════════════════════════════════════════════');

  const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!keyEnv) {
    log('GOOGLE', '⚠️ GOOGLE_SERVICE_ACCOUNT_KEY not set — skipping');
    log('GOOGLE', '💡 Set this env var in Render dashboard to enable direct Google indexing');
    return 0;
  }
  log('GOOGLE', `🔑 GOOGLE_SERVICE_ACCOUNT_KEY found (${keyEnv.length} chars)`);

  // Check if we already hit the daily limit
  const lastRun = progress.lastGoogleRun ? new Date(progress.lastGoogleRun) : null;
  const now = new Date();
  const isSameDay = lastRun && lastRun.toDateString() === now.toDateString();
  const todaySubmitted = isSameDay ? progress.googleApiSubmitted.length : 0;
  const dailyLimit = 200;
  const remaining = dailyLimit - todaySubmitted;

  if (remaining <= 0) {
    log('GOOGLE', `⚠️ Daily limit reached (${dailyLimit}). Run again tomorrow.`);
    log('GOOGLE', `Last run: ${progress.lastGoogleRun}`);
    return 0;
  }

  // Reset daily counter if new day
  if (!isSameDay) {
    log('GOOGLE', `New day detected — resetting daily counter (was ${progress.googleApiSubmitted.length})`);
    progress.googleApiSubmitted = [];
  }

  // Prioritize URLs not yet submitted
  const submittedSet = new Set(progress.googleApiSubmitted);
  const pending = urls.filter(u => !submittedSet.has(u));
  const batch = pending.slice(0, remaining);

  log('GOOGLE', `Daily limit: ${dailyLimit} | Used today: ${todaySubmitted} | Remaining: ${remaining}`);
  log('GOOGLE', `Pending URLs: ${pending.length} | This batch: ${batch.length}`);

  if (batch.length === 0) {
    log('GOOGLE', '✅ All URLs already submitted via Google API');
    return 0;
  }

  // Log first/last URLs in batch
  log('GOOGLE', `First URL: ${batch[0]}`);
  log('GOOGLE', `Last URL: ${batch[batch.length - 1]}`);

  if (DRY_RUN) {
    log('GOOGLE', `[DRY] Would submit ${batch.length} URLs to Google Indexing API`);
    batch.slice(0, 10).forEach((u, i) => log('GOOGLE', `  ${i + 1}. ${u}`));
    if (batch.length > 10) log('GOOGLE', `  ... and ${batch.length - 10} more`);
    return 0;
  }

  // Load Google API
  let keyContent: any;
  try {
    keyContent = JSON.parse(keyEnv);
    log('GOOGLE', '✅ Parsed credentials as JSON string');
  } catch {
    try {
      keyContent = JSON.parse(fs.readFileSync(keyEnv, 'utf8'));
      log('GOOGLE', `✅ Loaded credentials from file: ${keyEnv}`);
    } catch {
      log('GOOGLE', '❌ Could not parse GOOGLE_SERVICE_ACCOUNT_KEY as JSON or file path');
      return 0;
    }
  }

  // Dynamic import googleapis only when needed
  const { google } = await import('googleapis');
  const jwtClient = new google.auth.JWT({
    email: keyContent.client_email,
    key: keyContent.private_key,
    scopes: ['https://www.googleapis.com/auth/indexing'],
  });

  log('GOOGLE', `🔐 Authenticating as ${keyContent.client_email}...`);
  await jwtClient.authorize();
  log('GOOGLE', `✅ Authenticated successfully`);

  const indexing = google.indexing({ version: 'v3', auth: jwtClient });
  let successCount = 0;
  let errorCount = 0;
  let consecutive429 = 0;

  for (let i = 0; i < batch.length; i++) {
    const url = batch[i];
    const start = Date.now();
    try {
      const response = await indexing.urlNotifications.publish({
        requestBody: { url, type: 'URL_UPDATED' },
      });
      const ms = Date.now() - start;
      log('GOOGLE', `[${i + 1}/${batch.length}] ✅ ${url} (${ms}ms)`);
      progress.googleApiSubmitted.push(url);
      successCount++;
      consecutive429 = 0;
    } catch (err: any) {
      const ms = Date.now() - start;
      const msg = err?.response?.data?.error?.message || err.message;
      const code = err?.response?.status || 'N/A';
      log('GOOGLE', `[${i + 1}/${batch.length}] ❌ ${url} → HTTP ${code} (${ms}ms) | ${msg}`);
      errorCount++;

      if (code === 429) {
        consecutive429++;
        if (consecutive429 >= 3) {
          log('GOOGLE', `🛑 3 consecutive 429s — daily quota exhausted. Stopping early (${i + 1}/${batch.length}).`);
          break;
        }
      } else {
        consecutive429 = 0;
      }
    }

    // Rate limit: ~1 req/sec
    if (i < batch.length - 1) await sleep(1100);

    // Progress checkpoint every 50 URLs
    if ((i + 1) % 50 === 0) {
      log('GOOGLE', `--- Progress: ${i + 1}/${batch.length} | ✅ ${successCount} | ❌ ${errorCount} ---`);
      saveProgress(progress);
    }
  }

  progress.lastGoogleRun = new Date().toISOString();
  log('GOOGLE', `Done: ${successCount}/${batch.length} submitted (${errorCount} errors)`);
  return successCount;
}

// ─── Main ────────────────────────────────────────────────────────────────────
async function main() {
  const runStart = Date.now();
  log('MAIN', '═══════════════════════════════════════════════════════════');
  log('MAIN', '🚀 FAST-INDEX: Multi-Method URL Indexing');
  log('MAIN', '═══════════════════════════════════════════════════════════');
  log('MAIN', `Site: ${BASE_URL}`);
  log('MAIN', `Node: ${process.version}`);
  log('MAIN', `Env: ${process.env.NODE_ENV || 'development'}`);
  if (DRY_RUN) log('MAIN', '🔍 DRY RUN MODE — no actual submissions');
  if (RESET) log('MAIN', '🔄 RESET — progress tracker cleared');

  ensureDir(LOGS_DIR);
  const progress = loadProgress();

  // Load all URLs
  const allUrls = loadAllUrlsFromSitemaps();
  progress.totalUrls = allUrls.length;
  log('MAIN', `Total unique URLs from sitemaps: ${allUrls.length}`);

  // Categorize for reporting
  const jobUrls = allUrls.filter(u => u.includes('/jobs/'));
  const competitorUrls = allUrls.filter(u => /\/(vs|alternative-to|reviews|switch-from|pricing-vs)\//.test(u));
  const categoryUrls = allUrls.filter(u => u.includes('/best/'));
  const otherUrls = allUrls.length - jobUrls.length - competitorUrls.length - categoryUrls.length;
  log('MAIN', `Breakdown: ${jobUrls.length} job | ${competitorUrls.length} competitor | ${categoryUrls.length} category | ${otherUrls} other`);

  // Priority order: competitors first (high conversion), then categories, then jobs
  const prioritized = [
    ...competitorUrls,
    ...categoryUrls,
    ...allUrls.filter(u => !jobUrls.includes(u) && !competitorUrls.includes(u) && !categoryUrls.includes(u)),
    ...jobUrls,
  ];

  let totalIndexed = 0;

  // Method 1: Always ping sitemaps
  await pingSitemaps();

  if (!PING_ONLY) {
    // Method 2: IndexNow (no daily limit, instant for Bing/Yandex)
    if (!INDEXNOW_ONLY) {
      const indexNowCount = await submitIndexNow(prioritized, progress);
      totalIndexed += indexNowCount;
    } else {
      const indexNowCount = await submitIndexNow(prioritized, progress);
      totalIndexed += indexNowCount;
    }

    // Method 3: Google Indexing API (200/day, highest impact)
    if (!INDEXNOW_ONLY) {
      const googleCount = await submitGoogleIndexingApi(prioritized, progress);
      totalIndexed += googleCount;
    }
  }

  // Save progress
  saveProgress(progress);

  // Summary
  const runDuration = ((Date.now() - runStart) / 1000).toFixed(1);
  log('SUMMARY', '═══════════════════════════════════════════════════════════');
  log('SUMMARY', '📊 FAST-INDEX RUN COMPLETE');
  log('SUMMARY', '═══════════════════════════════════════════════════════════');
  log('SUMMARY', `Duration: ${runDuration}s`);
  log('SUMMARY', `Total URLs: ${allUrls.length}`);
  log('SUMMARY', `Google API submitted (all time): ${progress.googleApiSubmitted.length}/${allUrls.length}`);
  log('SUMMARY', `IndexNow submitted (all time): ${progress.indexNowSubmitted.length}/${allUrls.length}`);
  log('SUMMARY', `Google API remaining: ${allUrls.length - progress.googleApiSubmitted.length}`);
  log('SUMMARY', `IndexNow remaining: ${allUrls.length - progress.indexNowSubmitted.length}`);

  const daysToComplete = Math.ceil((allUrls.length - progress.googleApiSubmitted.length) / 200);
  log('SUMMARY', `Days to submit all via Google API: ${daysToComplete}`);
  log('SUMMARY', `Progress file: ${PROGRESS_FILE}`);
  log('SUMMARY', `Last Google run: ${progress.lastGoogleRun || 'never'}`);
  log('SUMMARY', `Last IndexNow run: ${progress.lastIndexNowRun || 'never'}`);
  log('SUMMARY', `Last Ping run: ${progress.lastPingRun || 'never'}`);
}

main().catch((err) => {
  log('FATAL', `Error: ${err.message}`);
  log('FATAL', `Stack: ${err.stack}`);
  process.exit(1);
});
