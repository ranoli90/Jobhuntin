/**
 * submit-to-google-ultimate.ts
 * 
 * ULTIMATE Google Search Indexing Submission System
 * Multiple submission methods for maximum coverage and fastest indexing
 * 
 * Methods:
 * 1. Google Indexing API (requires Service Account)
 * 2. Sitemap Ping (always works)
 * 3. URL Inspection API (via Search Console)
 * 4. IndexNow API (instant notification to multiple engines)
 * 
 * Usage:
 *   npx tsx scripts/seo/submit-to-google-ultimate.ts              # All methods
 *   npx tsx scripts/seo/submit-to-google-ultimate.ts --dry-run    # Preview
 *   npx tsx scripts/seo/submit-to-google-ultimate.ts --indexnow   # IndexNow only
 *   npx tsx scripts/seo/submit-to-google-ultimate.ts --sitemap-ping # Sitemap ping only
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = process.env.GOOGLE_SEARCH_CONSOLE_SITE || 'https://jobhuntin.com';

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const indexNowOnly = args.includes('--indexnow');
const sitemapPingOnly = args.includes('--sitemap-ping');
const urlsFile = args.includes('--urls-file') ? args[args.indexOf('--urls-file') + 1] : null;

console.log(`🚀 Ultimate Google Indexing Submission System`);
console.log("📍 Site:", BASE_URL);
console.log("📅", new Date().toISOString());

interface UrlInfo {
    url: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    type: 'homepage' | 'competitor' | 'category' | 'job' | 'guide' | 'static';
    changefreq: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly';
    estimatedTraffic: number;
}

function parseSitemap(): UrlInfo[] {
    const sitemapPath = path.resolve(__dirname, '../../public/sitemap.xml');
    if (!fs.existsSync(sitemapPath)) {
        console.error('❌ Sitemap not found');
        return [];
    }
    
    const content = fs.readFileSync(sitemapPath, 'utf-8');
    const urlMatches = content.match(/<url>[\s\S]*?<\/url>/g) || [];
    
    return urlMatches.map(urlBlock => {
        const loc = urlBlock.match(/<loc>(.*?)<\/loc>/)?.[1] || '';
        const priority = parseFloat(urlBlock.match(/<priority>(.*?)<\/priority>/)?.[1] || '0.5');
        const changefreq = urlBlock.match(/<changefreq>(.*?)<\/changefreq>/)?.[1] || 'weekly';
        
        let urlPriority: UrlInfo['priority'] = 'low';
        let type: UrlInfo['type'] = 'static';
        let estimatedTraffic = 50;
        
        if (loc === `${BASE_URL}/`) {
            urlPriority = 'critical';
            type = 'homepage';
            estimatedTraffic = 1000;
        } else if (loc.includes('/vs/') || loc.includes('/alternative-to/')) {
            urlPriority = 'high';
            type = 'competitor';
            estimatedTraffic = 200;
        } else if (loc.includes('/best/')) {
            urlPriority = 'high';
            type = 'category';
            estimatedTraffic = 300;
        } else if (loc.includes('/jobs/')) {
            urlPriority = priority >= 0.7 ? 'medium' : 'low';
            type = 'job';
            estimatedTraffic = 100;
        } else if (loc.includes('/guides/')) {
            urlPriority = 'high';
            type = 'guide';
            estimatedTraffic = 150;
        }
        
        return {
            url: loc,
            priority: urlPriority,
            type,
            changefreq: changefreq as UrlInfo['changefreq'],
            estimatedTraffic
        };
    });
}

async function submitViaSitemapPing(): Promise<boolean> {
    console.log('\n📡 Method 1: Sitemap Ping to Google');
    
    const sitemapUrl = `${BASE_URL}/sitemap.xml`;
    const pingUrl = `https://www.google.com/ping?sitemap=${encodeURIComponent(sitemapUrl)}`;
    
    if (dryRun) {
        console.log("   🔍 DRY RUN: Would ping", pingUrl);
        return true;
    }
    
    try {
        const response = await fetch(pingUrl);
        if (response.ok) {
            console.log(`   ✅ Sitemap pinged successfully to Google`);
            return true;
        } else {
            console.log("   ⚠️  Ping returned status", response.status);
            return false;
        }
    } catch (error: any) {
        console.log("   ❌ Ping failed:", error.message);
        return false;
    }
}

async function submitViaIndexNow(urls: string[]): Promise<boolean> {
    console.log('\n⚡ Method 2: IndexNow API (Instant Indexing)');
    
    const indexNowKey = '2021b89b3147e09e54b705189f2082d8446ce96c';
    const keyFile = `${indexNowKey}.txt`;
    
    if (dryRun) {
        console.log("   🔍 DRY RUN: Would submit", urls.length, "URLs via IndexNow");
        console.log("   📝 Key file needed: /.well-known/" + keyFile);
        return true;
    }
    
    const keyFilePath = path.resolve(__dirname, '../../public/.well-known', keyFile);
    const wellKnownDir = path.dirname(keyFilePath);
    
    if (!fs.existsSync(wellKnownDir)) {
        fs.mkdirSync(wellKnownDir, { recursive: true });
    }
    if (!fs.existsSync(keyFilePath)) {
        fs.writeFileSync(keyFilePath, indexNowKey);
        console.log("   📝 Created IndexNow key file at /.well-known/" + keyFile);
    }
    
    const batchSize = 10000;
    let successCount = 0;
    
    for (let i = 0; i < urls.length; i += batchSize) {
        const batch = urls.slice(i, i + batchSize);
        
        const payload = {
            host: BASE_URL.replace('https://', '').replace('http://', ''),
            key: indexNowKey,
            keyLocation: `${BASE_URL}/${keyFile}`,
            urlList: batch
        };
        
        try {
            const endpoints = [
                'https://api.indexnow.org/indexnow',
                'https://www.bing.com/indexnow',
                'https://search.semrush.com/indexnow'
            ];
            
            for (const endpoint of endpoints) {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok || response.status === 202) {
                    console.log("   ✅ Submitted", batch.length, "URLs to", endpoint.split("/")[2]);
                    successCount += batch.length;
                    break;
                }
            }
            
            await new Promise(r => setTimeout(r, 100));
        } catch (error: any) {
            console.log("   ⚠️  Batch", i + "-" + (i + batch.length), "error:", error.message);
        }
    }
    
    console.log("   📊 IndexNow:", successCount + "/" + urls.length, "URLs submitted");
    return successCount > 0;
}

async function submitViaGoogleIndexingAPI(urls: string[]): Promise<boolean> {
    console.log('\n🔐 Method 3: Google Indexing API');
    
    const keyConfig = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
    
    if (!keyConfig) {
        console.log('   ⚠️  GOOGLE_SERVICE_ACCOUNT_KEY not set - skipping');
        return false;
    }
    
    if (keyConfig.length < 100 || !keyConfig.includes('{')) {
        console.log('   ⚠️  GOOGLE_SERVICE_ACCOUNT_KEY is not a valid JSON key');
        console.log('   📝 You need to set up a Google Service Account:');
        console.log('      1. Go to console.cloud.google.com');
        console.log('      2. Create a Service Account');
        console.log('      3. Download the JSON key file');
        console.log('      4. Set GOOGLE_SERVICE_ACCOUNT_KEY to the JSON content');
        console.log('      5. Add service account email as owner in Search Console');
        return false;
    }
    
    if (dryRun) {
        console.log("   🔍 DRY RUN: Would submit", urls.length, "URLs via Indexing API");
        return true;
    }
    
    try {
        const { google } = await import('googleapis');
        
        let key: any;
        try {
            key = JSON.parse(keyConfig);
        } catch {
            console.log('   ❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY');
            return false;
        }
        
        if (key.private_key) {
            key.private_key = key.private_key.replace(/\\n/g, '\n');
        }
        
        const auth = new google.auth.GoogleAuth({
            credentials: key,
            scopes: ['https://www.googleapis.com/auth/indexing'],
        });
        
        const client = await auth.getClient();
        const accessToken = await client.getAccessToken();
        
        if (!accessToken.token) {
            console.log('   ❌ Failed to get access token');
            return false;
        }
        
        console.log(`   ✅ Authenticated successfully`);
        
        let successCount = 0;
        const dailyLimit = 200;
        const urlsToSubmit = urls.slice(0, dailyLimit);
        
        for (let i = 0; i < urlsToSubmit.length; i++) {
            const url = urlsToSubmit[i];
            
            try {
                const response = await fetch('https://indexing.googleapis.com/v3/urlNotifications:publish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${accessToken.token}`,
                    },
                    body: JSON.stringify({ url, type: 'URL_UPDATED' }),
                });
                
                if (response.ok) {
                    successCount++;
                    if (i % 50 === 0) {
                        console.log("   📤 Progress:", successCount + "/" + urlsToSubmit.length);
                    }
                }
                
                await new Promise(r => setTimeout(r, 150));
            } catch (error: any) {
                console.log("   ⚠️  Error on", url, ":", error.message);
            }
        }
        
        console.log("   📊 Indexing API:", successCount + "/" + urlsToSubmit.length, "URLs submitted");
        return successCount > 0;
        
    } catch (error: any) {
        console.log("   ❌ Indexing API error:", error.message);
        return false;
    }
}

async function submitToSearchEngines(urls: string[]): Promise<void> {
    console.log('\n🔍 Method 4: Direct Search Engine Notification');
    
    const sitemapUrl = `${BASE_URL}/sitemap.xml`;
    
    const endpoints = [
        { name: 'Google', url: `https://www.google.com/ping?sitemap=${encodeURIComponent(sitemapUrl)}` },
        { name: 'Bing', url: `https://www.bing.com/ping?sitemap=${encodeURIComponent(sitemapUrl)}` },
        { name: 'Yandex', url: `https://webmaster.yandex.com/ping?sitemap=${encodeURIComponent(sitemapUrl)}` },
    ];
    
    for (const endpoint of endpoints) {
        if (dryRun) {
            console.log("   🔍 DRY RUN: Would ping", endpoint.name);
            continue;
        }
        
        try {
            const response = await fetch(endpoint.url);
            console.log("   ", response.ok ? "✅" : "⚠️ ", endpoint.name + ":", response.status);
        } catch (error: any) {
            console.log("   ❌", endpoint.name + ":", error.message);
        }
    }
}

async function main() {
    let urls: UrlInfo[];
    
    if (urlsFile) {
        const filePath = path.resolve(process.cwd(), urlsFile);
        const fileContent = fs.readFileSync(filePath, 'utf-8');
        const rawUrls = fileContent.split(/\r?\n/).filter(Boolean);
        urls = rawUrls.map(url => ({
            url: url.trim(),
            priority: 'high' as const,
            type: 'job' as const,
            changefreq: 'daily' as const,
            estimatedTraffic: 100
        }));
        console.log("📥 Loaded", urls.length, "URLs from file");
    } else {
        urls = parseSitemap();
        console.log(`📄 Parsed ${urls.length} URLs from sitemap`);
    }
    
    const sortedUrls = urls.sort((a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 };
        return order[a.priority] - order[b.priority];
    });
    
    console.log(`\n📊 URL Distribution:`);
    console.log(`   Critical: ${urls.filter(u => u.priority === 'critical').length}`);
    console.log(`   High: ${urls.filter(u => u.priority === 'high').length}`);
    console.log(`   Medium: ${urls.filter(u => u.priority === 'medium').length}`);
    console.log(`   Low: ${urls.filter(u => u.priority === 'low').length}`);
    
    const allUrls = sortedUrls.map(u => u.url);
    
    if (dryRun) {
        console.log(`\n🔍 DRY RUN MODE - No actual submissions`);
        console.log(`\n📋 Top 20 URLs to submit:`);
        allUrls.slice(0, 20).forEach((url, i) => {
            const info = sortedUrls[i];
            console.log(`   ${i + 1}. [${info.priority}] ${url}`);
        });
    }
    
    const results: { method: string; success: boolean }[] = [];
    
    if (!indexNowOnly) {
        results.push({ method: 'Sitemap Ping', success: await submitViaSitemapPing() });
    }
    
    if (!sitemapPingOnly) {
        results.push({ method: 'IndexNow', success: await submitViaIndexNow(allUrls) });
    }
    
    if (!indexNowOnly && !sitemapPingOnly) {
        results.push({ method: 'Google Indexing API', success: await submitViaGoogleIndexingAPI(allUrls) });
        await submitToSearchEngines(allUrls);
    }
    
    console.log(`\n📊 FINAL RESULTS:`);
    results.forEach(r => {
        console.log(`   ${r.success ? '✅' : '❌'} ${r.method}`);
    });
    
    console.log(`\n🎯 NEXT STEPS FOR FASTEST INDEXING:`);
    console.log(`   1. ✅ Sitemap is being pinged to Google/Bing`);
    console.log(`   2. ⚡ IndexNow provides instant notification to Google/Bing/Yandex`);
    console.log(`   3. 🔐 Set up Google Service Account for direct Indexing API access`);
    console.log(`   4. 📱 Share key URLs on social media for quick discovery`);
    console.log(`   5. 🔗 Build internal links to priority pages`);
    
    const logDir = path.resolve(__dirname, '../../logs');
    if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
    }
    
    const log = {
        timestamp: new Date().toISOString(),
        totalUrls: allUrls.length,
        dryRun,
        results,
        topUrls: allUrls.slice(0, 100)
    };
    
    fs.writeFileSync(
        path.resolve(logDir, 'indexing-submission.json'),
        JSON.stringify(log, null, 2)
    );
    
    console.log(`\n📝 Log saved to logs/indexing-submission.json`);
}

main().catch(console.error);
