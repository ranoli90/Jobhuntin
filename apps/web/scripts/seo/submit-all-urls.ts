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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE_URL = process.env.GOOGLE_SEARCH_CONSOLE_SITE || 'https://jobhuntin.com';

async function main() {
  console.log('🚀 SUBMITTING ALL EXISTING URLS TO GOOGLE');
  console.log('='.repeat(60));
  console.log(`📍 Site: ${BASE_URL}`);
  console.log(`⏰ Started: ${new Date().toISOString()}`);
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
    console.log(`📄 ${file}: ${urls.length} URLs`);
  }
  
  console.log(`\n📊 Total URLs found: ${allUrls.length}`);
  
  // Dedupe
  const uniqueUrls = [...new Set(allUrls)];
  console.log(`📊 Unique URLs: ${uniqueUrls.length}`);
  
  // Check for Google credentials
  const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!keyEnv) {
    console.error('❌ GOOGLE_SERVICE_ACCOUNT_KEY not set');
    process.exit(1);
  }

  // Parse credentials
  let keyContent;
  try {
    keyContent = JSON.parse(keyEnv);
    console.log(`✅ Service account: ${keyContent.client_email}`);
  } catch {
    // Try as file path
    try {
      keyContent = JSON.parse(fs.readFileSync(keyEnv, 'utf8'));
      console.log(`✅ Service account: ${keyContent.client_email}`);
    } catch (e) {
      console.error('❌ Could not parse GOOGLE_SERVICE_ACCOUNT_KEY');
      process.exit(1);
    }
  }

  // Create JWT client
  const jwtClient = new google.auth.JWT({
    email: keyContent.client_email,
    key: keyContent.private_key,
    scopes: ['https://www.googleapis.com/auth/indexing']
  });

  console.log('\n🔐 Authenticating with Google...');
  await jwtClient.authorize();
  console.log('✅ Authenticated!');

  const indexing = google.indexing({ version: 'v3', auth: jwtClient });

  // Google limits: 200 URLs per day
  const dailyLimit = 200;
  const urlsToSubmit = uniqueUrls.slice(0, dailyLimit);
  
  console.log(`\n📤 Submitting ${urlsToSubmit.length} URLs (daily limit: ${dailyLimit})`);
  console.log('='.repeat(60));

  let successCount = 0;
  let errorCount = 0;
  const results: any[] = [];

  for (let i = 0; i < urlsToSubmit.length; i++) {
    const url = urlsToSubmit[i];
    
    try {
      process.stdout.write(`[${i + 1}/${urlsToSubmit.length}] ${url.substring(0, 60)}... `);
      
      const response = await indexing.urlNotifications.publish({
        requestBody: {
          url: url,
          type: 'URL_UPDATED'
        }
      });
      
      console.log('✅');
      successCount++;
      results.push({ url, status: 'success', timestamp: new Date().toISOString() });
      
      // Rate limit: 1 second between requests
      if (i < urlsToSubmit.length - 1) {
        await new Promise(r => setTimeout(r, 1000));
      }
      
    } catch (error: any) {
      console.log(`❌ ${error.message}`);
      errorCount++;
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
    success: successCount,
    errors: errorCount,
    results
  }, null, 2));

  console.log('\n' + '='.repeat(60));
  console.log('📊 SUBMISSION COMPLETE');
  console.log('='.repeat(60));
  console.log(`✅ Success: ${successCount}`);
  console.log(`❌ Errors: ${errorCount}`);
  console.log(`📝 Log: ${logPath}`);
  console.log(`\n⏰ URLs will be indexed within 24-48 hours.`);
  console.log(`📈 Check status at: https://search.google.com/search-console`);
}

main().catch(console.error);
