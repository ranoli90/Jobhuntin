/**
 * submit-to-google.ts
 * 
 * Submits programmatic SEO URLs to Google's Indexing API for faster crawling.
 * Requires a Google Cloud service account with Indexing API permissions.
 * 
 * Usage:
 *   npx tsx scripts/seo/submit-to-google.ts              # Submit all URLs
 *   npx tsx scripts/seo/submit-to-google.ts --dry-run     # Preview without submitting
 *   npx tsx scripts/seo/submit-to-google.ts --slug teal   # Submit only URLs for "teal"
 * 
 * Environment variables:
 *   GOOGLE_SERVICE_ACCOUNT_KEY - path to service account JSON key file OR the raw JSON content string
 *   
 * Setup:
 *   1. Create a Google Cloud project
 *   2. Enable the Web Search Indexing API
 *   3. Create a service account and download the JSON key
 *   4. Add the service account email as an owner in Google Search Console
 *   5. Set GOOGLE_SERVICE_ACCOUNT_KEY env var to the path of the JSON key file
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = 'https://jobhuntin.com';

// Load data
const competitors = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, '../../src/data/competitors.json'), 'utf-8')
);
const categories = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, '../../src/data/categories.json'), 'utf-8')
);
const roles = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, '../../src/data/roles.json'), 'utf-8')
);
const locations = JSON.parse(
    fs.readFileSync(path.resolve(__dirname, '../../src/data/locations.json'), 'utf-8')
);

// Parse CLI args
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const slugFilter = args.includes('--slug') ? args[args.indexOf('--slug') + 1] : null;

// Build URL list
function getAllUrls(): string[] {
    const urls: string[] = [];

    // Static routes
    const staticRoutes = [
        '/', '/pricing', '/success-stories', '/chrome-extension', '/recruiters',
        '/about', '/guides',
        '/guides/how-to-beat-ats-with-ai',
        '/guides/automated-job-search-ethics',
        '/guides/scaling-your-applications-safely',
        '/guides/ai-cover-letter-mastery',
    ];
    urls.push(...staticRoutes.map(r => `${BASE_URL}${r}`));

    // Competitor routes (5 page types per brand)
    const filteredCompetitors = slugFilter
        ? competitors.filter((c: any) => c.slug === slugFilter)
        : competitors;

    for (const comp of filteredCompetitors) {
        urls.push(`${BASE_URL}/vs/${comp.slug}`);
        urls.push(`${BASE_URL}/alternative-to/${comp.slug}`);
        urls.push(`${BASE_URL}/reviews/${comp.slug}`);
        urls.push(`${BASE_URL}/switch-from/${comp.slug}`);
        urls.push(`${BASE_URL}/pricing-vs/${comp.slug}`);
    }

    // Category hubs
    for (const cat of categories) {
        urls.push(`${BASE_URL}/best/${cat.slug}`);
    }

    // Local Job Niche routes (Roles × Locations)
    // We limit this for Indexing API submission to top priority combos to stay within default quotas
    // but the sitemap will have all of them.
    const priorityLocations = locations.slice(0, 30); // Top 30 cities
    const priorityRoles = roles.slice(0, 10); // Top 10 roles

    for (const role of priorityRoles) {
        for (const loc of priorityLocations) {
            urls.push(`${BASE_URL}/jobs/${role.id}/${loc.id}`);
        }
    }

    // SAFETY FILTER: Google Indexing API is ONLY for JobPosting and BroadcastEvent
    // We strictly filter out non-job URLs to prevent API suspension
    const jobPostingUrls = urls.filter(u => u.includes('/jobs/'));

    if (urls.length !== jobPostingUrls.length) {
        console.warn(`⚠️  Filtered out ${urls.length - jobPostingUrls.length} non-job URLs from Indexing API submission (Safety Protocol).`);
        console.warn(`   Only /jobs/... URLs are valid for this API.`);
    }

    return jobPostingUrls;
}

// Google Indexing API submission
async function getAccessToken(keyConfig: string): Promise<string> {
    // Check if it's an API Key (starts with AIza) - which is invalid for Indexing API
    if (keyConfig.startsWith('AIza')) {
        throw new Error(
            `The provided key starts with "AIza", which looks like a broad API Key. ` +
            `The Google Indexing API requires a Service Account JSON key (OAuth 2.0) to authorize URL notifications. ` +
            `Please create a Service Account in Google Cloud, download the JSON key file, and set GOOGLE_SERVICE_ACCOUNT_KEY to its path or content.`
        );
    }

    try {
        const { google } = await import('googleapis');
        let key;

        // Check if keyConfig is a file path
        // We use try-catch around fs.statSync just in case the string is too long (raw JSON) to be a valid path
        let isFile = false;
        try {
            if (fs.existsSync(keyConfig) && fs.statSync(keyConfig).isFile()) {
                isFile = true;
            }
        } catch {
            // Ignore error, assume it's not a file path (too long filename etc)
            isFile = false;
        }

        if (isFile) {
            key = JSON.parse(fs.readFileSync(keyConfig, 'utf-8'));
        } else {
            // Try to parse as raw JSON string
            try {
                key = JSON.parse(keyConfig);
            } catch (e) {
                // If it's not JSON, throw specific error
                throw new Error(`GOOGLE_SERVICE_ACCOUNT_KEY is neither a valid file path nor a valid JSON string.`);
            }
        }

        // Sanitize private key - Google's library needs actual newlines
        if (key.private_key && typeof key.private_key === 'string') {
            key.private_key = key.private_key
                .replace(/\\n/g, '\n')
                .replace(/\"/g, '')
                .trim();

            // Ensure PEM start/end tags have newlines around them if missing
            if (key.private_key.includes('BEGIN PRIVATE KEY') && !key.private_key.startsWith('-----BEGIN')) {
                // Try to fix formatting
            }
        }

        const auth = new google.auth.GoogleAuth({
            credentials: key,
            scopes: ['https://www.googleapis.com/auth/indexing'],
        });

        const tokens = await auth.getAccessToken();
        return tokens!;
    } catch (error) {
        throw new Error(
            `Failed to authenticate. Ensure GOOGLE_SERVICE_ACCOUNT_KEY points to a valid service account JSON key.\n` +
            `Run: npm install googleapis\n` +
            `Error: ${error}`
        );
    }
}

async function submitUrl(url: string, accessToken: string, type: 'URL_UPDATED' | 'URL_DELETED' = 'URL_UPDATED'): Promise<{ url: string; status: string; error?: string }> {
    try {
        const response = await fetch('https://indexing.googleapis.com/v3/urlNotifications:publish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
            },
            body: JSON.stringify({ url, type }),
        });

        if (response.ok) {
            return { url, status: 'success' };
        } else {
            const error = await response.text();
            return { url, status: 'error', error: `${response.status}: ${error}` };
        }
    } catch (error) {
        return { url, status: 'error', error: String(error) };
    }
}

async function submitBatch(urls: string[], accessToken: string): Promise<void> {
    const BATCH_SIZE = 10; // Google rate limit: ~200/day, ~600/minute for batch
    const DELAY_MS = 2000; // Increased to 2 seconds for safety

    console.log(`\n📤 Submitting ${urls.length} URLs to Google Indexing API...`);
    console.log(`⚠️  Safety Protocol Active: JobPostings ONLY. Slow-rolling submission.`);

    let success = 0;
    let errors = 0;

    for (let i = 0; i < urls.length; i += BATCH_SIZE) {
        const batch = urls.slice(i, i + BATCH_SIZE);
        const results = await Promise.all(
            batch.map(url => submitUrl(url, accessToken))
        );

        for (const result of results) {
            if (result.status === 'success') {
                console.log(`  ✅ ${result.url}`);
                success++;
            } else {
                console.log(`  ❌ ${result.url} — ${result.error}`);
                errors++;
            }
        }

        // Rate limit delay between batches
        if (i + BATCH_SIZE < urls.length) {
            await new Promise(resolve => setTimeout(resolve, DELAY_MS));
        }
    }

    console.log(`\n📊 Results: ${success} submitted, ${errors} errors, ${urls.length} total`);
}

// Main
async function main() {
    const urls = getAllUrls();

    console.log('🔍 Google Indexing API — URL Submission Tool');
    console.log(`   URLs to submit: ${urls.length}`);
    if (slugFilter) console.log(`   Filter: ${slugFilter}`);
    if (dryRun) console.log(`   Mode: DRY RUN (no submissions)`);
    console.log('');

    if (dryRun) {
        console.log('📋 URLs that would be submitted:\n');
        urls.forEach((url, i) => console.log(`  ${i + 1}. ${url}`));
        console.log(`\n✅ Dry run complete. ${urls.length} URLs listed.`);
        return;
    }

    // Rename variable to reflect it can be content too
    const keyConfig = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
    console.log(`DEBUG: GOOGLE_SERVICE_ACCOUNT_KEY found: ${!!keyConfig}`);
    if (!keyConfig) {
        console.log('⚠️  GOOGLE_SERVICE_ACCOUNT_KEY environment variable not set.');
        console.log('');
        console.log('To use the Google Indexing API:');
        console.log('  1. Create a Google Cloud project');
        console.log('  2. Enable the "Web Search Indexing API"');
        console.log('  3. Create a service account and download the JSON key');
        console.log('  4. Add the service account email as an owner in Google Search Console');
        console.log('  5. Set GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/key.json (or the raw JSON content)');
        console.log('');
        console.log('For now, running in dry-run mode:');
        console.log('');
        urls.forEach((url, i) => console.log(`  ${i + 1}. ${url}`));
        console.log(`\n📋 ${urls.length} URLs ready for submission once API is configured.`);
        return;
    }

    console.log('🔑 Authenticating with Google...');
    try {
        const accessToken = await getAccessToken(keyConfig);
        console.log('✅ Authenticated.\n');
        await submitBatch(urls, accessToken);
    } catch (error: any) {
        console.error(`❌ Authentication failed: ${error.message}`);
        // Do NOT exit(1) if it's just a key mismatch in dev, but here we want to alert the user
        // We will fallback to dry run logic so they see what would happen
        console.log('\n⚠️ Falling back to dry-run mode due to authentication failure.\n');
        urls.forEach((url, i) => console.log(`  ${i + 1}. ${url}`));
    }
}

main().catch(console.error);
