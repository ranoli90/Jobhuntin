
/**
 * monitor-indexing.ts
 * 
 * Checks the indexing status of the sitemap URLs using the Google Search Console API.
 * Reports which URLs are indexed and which are missing.
 * Optionally re-submits missing URLs to the Indexing API.
 * 
 * Usage:
 *   npx tsx scripts/seo/monitor-indexing.ts
 *   npx tsx scripts/seo/monitor-indexing.ts --submit-missing
 */

import 'dotenv/config';
import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Helper to resolve paths relative to this script
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration
const SERVICE_ACCOUNT_KEY = process.env.GOOGLE_SERVICE_ACCOUNT_KEY || './service-account.json';
const SITE_URL = 'https://jobhuntin.com'; // Change to your actual domain
const SITEMAP_URL = `${SITE_URL}/sitemap.xml`;

async function getAuthClient() {
    // If it's a file path
    if (fs.existsSync(SERVICE_ACCOUNT_KEY) && fs.statSync(SERVICE_ACCOUNT_KEY).isFile()) {
        return new google.auth.GoogleAuth({
            keyFile: SERVICE_ACCOUNT_KEY,
            scopes: [
                'https://www.googleapis.com/auth/webmasters.readonly',
                'https://www.googleapis.com/auth/indexing'
            ],
        });
    }

    // If it's a raw JSON string
    if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY && process.env.GOOGLE_SERVICE_ACCOUNT_KEY.includes('{')) {
        const credentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY);
        return google.auth.fromJSON(credentials);
    }

    throw new Error(`Service account key not found. Set GOOGLE_SERVICE_ACCOUNT_KEY to a file path or JSON string.`);
}

async function parseSitemap(url: string): Promise<string[]> {
    console.log(`Fetching sitemap from ${url}...`);
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch sitemap: ${response.statusText}`);
        const xml = await response.text();

        // Simple regex parse (robust enough for standard sitemaps)
        const matches = xml.match(/<loc>(.*?)<\/loc>/g);
        if (!matches) return [];

        return matches.map(m => m.replace(/<\/?loc>/g, ''));
    } catch (error) {
        console.warn(`⚠️ Could not fetch sitemap (is the site live?). Using local simulation if needed.`);
        return [];
    }
}

async function checkIndexingStatus() {
    const auth = await getAuthClient();
    const searchConsole = google.searchconsole({ version: 'v1', auth: auth as any });
    const indexing = google.indexing({ version: 'v3', auth: auth as any });

    const sitemapUrls = await parseSitemap(SITEMAP_URL);
    if (sitemapUrls.length === 0) {
        console.error('No URLs found in sitemap. Ensure the site is deployed and sitemap.xml is accessible.');
        return;
    }

    console.log(`Checking status for ${sitemapUrls.length} URLs...`);

    // Allow --submit-missing flag
    const shouldSubmitMissing = process.argv.includes('--submit-missing');

    // Search Console API has quotas, so we query in batches or aggregate
    // For "is it indexed?", we can use the URL Inspection API (very low quota) or Search Analytics data (laggy but bulk).
    // The plan suggested Search Analytics query for "pages receiving impressions".
    // This confirms they are indexed AND ranking. It doesn't show "crawled but not indexed".

    // Let's use Search Analytics as a proxy for "active" pages.
    const today = new Date();
    const threeDaysAgo = new Date(today);
    threeDaysAgo.setDate(today.getDate() - 3);

    try {
        const res = await searchConsole.searchanalytics.query({
            siteUrl: SITE_URL,
            requestBody: {
                startDate: '2025-01-01', // Adjust as needed
                endDate: today.toISOString().split('T')[0],
                dimensions: ['page'],
                rowLimit: 25000,
            },
        });

        const activeUrls = new Set(res.data.rows?.map(r => r.keys![0]) || []);

        const missing = sitemapUrls.filter(url => !activeUrls.has(url));
        const indexedCount = activeUrls.size;

        console.log(`\n📊 Indexing Report for ${SITE_URL}`);
        console.log(`-----------------------------------`);
        console.log(`Total URLs in Sitemap: ${sitemapUrls.length}`);
        console.log(`Active in Search (last 90d): ${indexedCount}`);
        console.log(`Potentially Missing/Inactive: ${missing.length}`);

        if (missing.length > 0) {
            console.log(`\nTop 5 Missing URLs:`);
            missing.slice(0, 5).forEach(url => console.log(` - ${url}`));

            if (shouldSubmitMissing) {
                console.log(`\n🚀 Submitting ${missing.length} missing URLs to Indexing API...`);
                for (const url of missing) {
                    try {
                        await indexing.urlNotifications.publish({
                            requestBody: {
                                url: url,
                                type: 'URL_UPDATED',
                            },
                        });
                        console.log(`   Submitted: ${url}`);
                        // Rate limit generic
                        await new Promise(r => setTimeout(r, 600));
                    } catch (e: any) {
                        console.error(`   Failed to submit ${url}: ${e.message}`);
                    }
                }
            } else {
                console.log(`\nRun with --submit-missing to automatically submit these to Google.`);
            }
        } else {
            console.log(`\n✅ Great job! All sitemap URLs are receiving search traffic.`);
        }

    } catch (error: any) {
        console.error(`Error querying Search Console: ${error.message}`);
        console.log('Ensure the Service Account has "Owner" or "Full" permissions in Search Console settings.');
    }
}

checkIndexingStatus().catch(console.error);
