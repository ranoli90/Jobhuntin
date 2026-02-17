/**
 * SMART SEO ENGINE - High-Impact Content Generation
 * 
 * Strategy:
 * 1. Use OpenRouter API with configurable model (default: GPT-4o-mini)
 * 2. Diverse content types: rankings, comparisons, current events, trends
 * 3. Never repeat the same content - tracks what was generated
 * 4. Complete logging with summaries
 * 5. Priority on high-ranking opportunities
 * 6. First run: submits all existing URLs to Google
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { google } from 'googleapis';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration
const CONFIG = {
  // GPT-4o-mini via OpenRouter - Best value: $0.15/1M input, $0.60/1M output
  MODEL: process.env.LLM_MODEL || 'openai/gpt-4o-mini',
  API_BASE: 'https://openrouter.ai/api/v1',

  // Rate limits
  DAILY_GENERATION_LIMIT: 100,
  BATCH_SIZE: 5,
  BATCH_DELAY_MS: 60000, // 1 minute between batches

  // Content diversity - ensure we don't repeat
  CONTENT_ROTATION_HOURS: 4,
};

// Content Types - Rotates to ensure diversity
const CONTENT_TYPES = [
  {
    id: 'competitor_comparison',
    name: 'Competitor Comparison',
    description: 'Compare JobHuntin vs competitors with unique angles',
    priority: 1,
    frequency: 'daily',
  },
  {
    id: 'industry_trends',
    name: 'Industry Trends & News',
    description: 'Current job market trends, salary reports, hiring news',
    priority: 2,
    frequency: 'daily',
  },
  {
    id: 'how_to_guides',
    name: 'How-To Guides',
    description: 'Practical guides for job seekers',
    priority: 2,
    frequency: 'weekly',
  },
  {
    id: 'location_deep_dive',
    name: 'Location Deep Dive',
    description: 'In-depth city/region job market analysis',
    priority: 3,
    frequency: 'weekly',
  },
  {
    id: 'role_analysis',
    name: 'Role Analysis',
    description: 'Specific job role requirements, salaries, growth',
    priority: 3,
    frequency: 'weekly',
  },
  {
    id: 'tool_reviews',
    name: 'Tool Reviews',
    description: 'Reviews of job search tools, ATS systems, etc.',
    priority: 4,
    frequency: 'biweekly',
  },
];

// Competitors to target - prioritized by search volume
const COMPETITORS = [
  { name: 'Teal', volume: 12000, keywords: ['teal jobs', 'teal ai', 'teal job tracker'] },
  { name: 'LazyApply', volume: 8500, keywords: ['lazyapply', 'lazy apply', 'lazyapply reviews'] },
  { name: 'Simplify', volume: 15000, keywords: ['simplify jobs', 'simplify ai', 'simplify extension'] },
  { name: 'JobCopilot', volume: 3200, keywords: ['jobcopilot', 'job copilot'] },
  { name: 'JobRight', volume: 4500, keywords: ['jobright', 'job right ai'] },
  { name: 'FinalRound', volume: 3800, keywords: ['finalround ai', 'final round interview'] },
  { name: 'LoopCV', volume: 2100, keywords: ['loopcv', 'loop cv'] },
  { name: 'AIApply', volume: 5500, keywords: ['aiapply', 'ai apply'] },
  { name: 'Careerflow', volume: 2800, keywords: ['careerflow', 'career flow ai'] },
  { name: 'Sonara', volume: 1900, keywords: ['sonara ai', 'sonara jobs'] },
];

// Trending topics - will be updated with current events
const TRENDING_TOPICS: string[] = [];

// State tracking
interface GenerationState {
  lastRun: string;
  currentContentTypeIndex: number;
  generatedPages: string[];
  competitorsCovered: string[];
  locationsCovered: string[];
  rolesCovered: string[];
  totalGenerated: number;
  dailyQuotaUsed: number;
  quotaResetDate: string;
  initialSubmissionDone: boolean;
}

const STATE_FILE = path.resolve(__dirname, '../../logs/seo-state.json');

function loadState(): GenerationState {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    }
  } catch (e) {
    console.warn('Could not load state, starting fresh');
  }

  return {
    lastRun: new Date().toISOString(),
    currentContentTypeIndex: 0,
    generatedPages: [],
    competitorsCovered: [],
    locationsCovered: [],
    rolesCovered: [],
    totalGenerated: 0,
    dailyQuotaUsed: 0,
    quotaResetDate: new Date().toISOString().split('T')[0],
    initialSubmissionDone: false,
  };
}

function saveState(state: GenerationState): void {
  const logDir = path.dirname(STATE_FILE);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

/**
 * Determine what content to generate next
 */
function getNextContentType(state: GenerationState): typeof CONTENT_TYPES[0] {
  // Rotate through content types
  const type = CONTENT_TYPES[state.currentContentTypeIndex % CONTENT_TYPES.length];
  return type;
}

/**
 * Get next competitor to target (prioritized by volume, not recently covered)
 */
function getNextCompetitor(state: GenerationState): typeof COMPETITORS[0] | null {
  // Sort by volume (descending)
  const sorted = [...COMPETITORS].sort((a, b) => b.volume - a.volume);

  // Find first not recently covered
  for (const comp of sorted) {
    const recentIdx = state.competitorsCovered.lastIndexOf(comp.name);
    if (recentIdx === -1) {
      return comp;
    }
    // Re-cover if it's been more than 50 generations
    if (state.generatedPages.length - recentIdx > 50) {
      return comp;
    }
  }

  // All covered recently, pick highest volume
  return sorted[0];
}

/**
 * Generate competitor comparison content
 */
async function generateCompetitorComparison(
  competitor: typeof COMPETITORS[0],
  state: GenerationState
): Promise<{ url: string; title: string; success: boolean }> {
  const timestamp = new Date().toISOString();
  console.log('\n' + '='.repeat(80));
  console.log(`📊 CONTENT TYPE: Competitor Comparison`);
  console.log(`🎯 TARGET: ${competitor.name} (${competitor.volume.toLocaleString()} searches/mo)`);
  console.log(`⏰ Started: ${timestamp}`);
  console.log('='.repeat(80));

  return new Promise((resolve) => {
    const childProcess = spawn('npx', [
      'tsx',
      'scripts/seo/generate-competitor-content.ts',
      competitor.name,
      '--model', CONFIG.MODEL,
      '--keywords', competitor.keywords.join(','),
    ], {
      cwd: path.resolve(__dirname, '../..'),
      stdio: 'inherit',
      env: {
        ...process.env,
        LLM_MODEL: CONFIG.MODEL,
        LLM_API_BASE: CONFIG.API_BASE,
      },
    });

    const start = Date.now();
    const timeoutMs = 5 * 60 * 1000;

    const timeout = setTimeout(() => {
      console.warn(`⏱️ TIMEOUT after 5 minutes`);
      childProcess.kill('SIGKILL');
    }, timeoutMs);

    childProcess.on('close', (code: number) => {
      clearTimeout(timeout);
      const duration = ((Date.now() - start) / 1000).toFixed(1);

      console.log('\n' + '-'.repeat(80));
      if (code === 0) {
        console.log(`✅ SUCCESS: ${competitor.name} comparison completed in ${duration}s`);
        const url = `https://jobhuntin.com/vs/${competitor.name.toLowerCase()}`;
        resolve({ url, title: `${competitor.name} vs JobHuntin`, success: true });
      } else {
        console.log(`❌ FAILED: ${competitor.name} comparison (exit ${code}) after ${duration}s`);
        resolve({ url: '', title: '', success: false });
      }
      console.log('-'.repeat(80) + '\n');
    });
  });
}

/**
 * Generate trending/news content
 */
async function generateTrendingContent(
  topic: string,
  state: GenerationState
): Promise<{ url: string; title: string; success: boolean }> {
  const timestamp = new Date().toISOString();
  console.log('\n' + '='.repeat(80));
  console.log(`📰 CONTENT TYPE: Industry Trends & News`);
  console.log(`🎯 TOPIC: ${topic}`);
  console.log(`⏰ Started: ${timestamp}`);
  console.log('='.repeat(80));

  return new Promise((resolve) => {
    const childProcess = spawn('npx', [
      'tsx',
      'scripts/seo/generate-trending-content.ts',
      topic,
      '--model', CONFIG.MODEL,
    ], {
      cwd: path.resolve(__dirname, '../..'),
      stdio: 'inherit',
      env: {
        ...process.env,
        LLM_MODEL: CONFIG.MODEL,
        LLM_API_BASE: CONFIG.API_BASE,
      },
    });

    const start = Date.now();
    const timeoutMs = 5 * 60 * 1000;

    const timeout = setTimeout(() => {
      childProcess.kill('SIGKILL');
    }, timeoutMs);

    childProcess.on('close', (code: number) => {
      clearTimeout(timeout);
      const duration = ((Date.now() - start) / 1000).toFixed(1);

      console.log('\n' + '-'.repeat(80));
      if (code === 0) {
        console.log(`✅ SUCCESS: Trending content for "${topic}" completed in ${duration}s`);
        const url = `https://jobhuntin.com/news/${topic.toLowerCase().replace(/\s+/g, '-')}`;
        resolve({ url, title: topic, success: true });
      } else {
        console.log(`❌ FAILED: Trending content (exit ${code}) after ${duration}s`);
        resolve({ url: '', title: '', success: false });
      }
      console.log('-'.repeat(80) + '\n');
    });
  });
}

/**
 * Generate location-specific content
 */
async function generateLocationContent(
  location: string,
  role: string,
  state: GenerationState
): Promise<{ url: string; title: string; success: boolean }> {
  const timestamp = new Date().toISOString();
  console.log('\n' + '='.repeat(80));
  console.log(`📍 CONTENT TYPE: Location Deep Dive`);
  console.log(`🎯 TARGET: ${role} jobs in ${location}`);
  console.log(`⏰ Started: ${timestamp}`);
  console.log('='.repeat(80));

  return new Promise((resolve) => {
    const childProcess = spawn('npx', [
      'tsx',
      'scripts/seo/generate-city-content.ts',
      location,
      role,
      '--model', CONFIG.MODEL,
    ], {
      cwd: path.resolve(__dirname, '../..'),
      stdio: 'inherit',
      env: {
        ...process.env,
        LLM_MODEL: CONFIG.MODEL,
        LLM_API_BASE: CONFIG.API_BASE,
      },
    });

    const start = Date.now();
    const timeoutMs = 10 * 60 * 1000;

    const timeout = setTimeout(() => {
      childProcess.kill('SIGKILL');
    }, timeoutMs);

    childProcess.on('close', (code: number) => {
      clearTimeout(timeout);
      const duration = ((Date.now() - start) / 1000).toFixed(1);

      console.log('\n' + '-'.repeat(80));
      if (code === 0) {
        console.log(`✅ SUCCESS: ${role} in ${location} completed in ${duration}s`);
        const url = `https://jobhuntin.com/jobs/${role.toLowerCase().replace(/\s+/g, '-')}-in-${location.toLowerCase().replace(/\s+/g, '-')}`;
        resolve({ url, title: `${role} Jobs in ${location}`, success: true });
      } else {
        console.log(`❌ FAILED: ${role} in ${location} (exit ${code}) after ${duration}s`);
        resolve({ url: '', title: '', success: false });
      }
      console.log('-'.repeat(80) + '\n');
    });
  });
}

/**
 * Submit all existing URLs from sitemaps to Google (first run only)
 */
async function submitExistingUrls(): Promise<number> {
  console.log('\n📤 FIRST RUN: Submitting existing URLs to Google...');

  // Extract URLs from sitemaps
  const sitemapDir = path.resolve(__dirname, '../../public');
  if (!fs.existsSync(sitemapDir)) {
    console.log('⚠️ No sitemap directory found');
    return 0;
  }

  const sitemapFiles = fs.readdirSync(sitemapDir).filter(f =>
    f.startsWith('sitemap') && f.endsWith('.xml')
  );

  const allUrls: string[] = [];

  for (const file of sitemapFiles) {
    const content = fs.readFileSync(path.join(sitemapDir, file), 'utf-8');
    const matches = content.match(/<loc>(.*?)<\/loc>/g) || [];
    const urls = matches.map(m => m.replace(/<\/?loc>/g, ''));
    allUrls.push(...urls);
    console.log(`   📄 ${file}: ${urls.length} URLs`);
  }

  const uniqueUrls = [...new Set(allUrls)];
  console.log(`   📊 Total unique URLs: ${uniqueUrls.length}`);

  // Check for Google credentials
  const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!keyEnv) {
    console.log('⚠️ GOOGLE_SERVICE_ACCOUNT_KEY not set, skipping submission');
    return 0;
  }

  console.log(`   🔑 GOOGLE_SERVICE_ACCOUNT_KEY found (${keyEnv.length} chars)`);

  // Parse credentials
  let keyContent;
  try {
    keyContent = JSON.parse(keyEnv);
    console.log(`   ✅ Parsed as JSON string`);
  } catch (e1) {
    console.log(`   ⚠️ Not valid JSON string, trying as file path...`);
    try {
      if (fs.existsSync(keyEnv)) {
        keyContent = JSON.parse(fs.readFileSync(keyEnv, 'utf8'));
        console.log(`   ✅ Loaded from file: ${keyEnv}`);
      } else {
        console.log(`   ⚠️ File does not exist: ${keyEnv}`);
        console.log(`   ⚠️ Parse error: ${e1}`);
        return 0;
      }
    } catch (e2) {
      console.log(`   ⚠️ Could not parse Google credentials`);
      console.log(`   ⚠️ Error 1: ${e1}`);
      console.log(`   ⚠️ Error 2: ${e2}`);
      return 0;
    }
  }

  console.log(`   🔐 Service account configured`);

  // Create JWT client
  const jwtClient = new google.auth.JWT({
    email: keyContent.client_email,
    key: keyContent.private_key,
    scopes: ['https://www.googleapis.com/auth/indexing']
  });

  try {
    await jwtClient.authorize();
    const indexing = google.indexing({ version: 'v3', auth: jwtClient });

    // Submit up to 200 URLs (daily limit)
    const urlsToSubmit = uniqueUrls.slice(0, 200);
    let successCount = 0;

    console.log(`   📤 Submitting ${urlsToSubmit.length} URLs...`);

    for (let i = 0; i < urlsToSubmit.length; i++) {
      const url = urlsToSubmit[i];
      try {
        await indexing.urlNotifications.publish({
          requestBody: { url, type: 'URL_UPDATED' }
        });
        successCount++;
        process.stdout.write(`\r   Progress: ${i + 1}/${urlsToSubmit.length} (${successCount} success)`);

        // Rate limit
        if (i < urlsToSubmit.length - 1) {
          await new Promise(r => setTimeout(r, 1000));
        }
      } catch (e) {
        // Continue on error
      }
    }

    console.log(`\n   ✅ Submitted ${successCount} URLs to Google`);
    return successCount;

  } catch (e) {
    console.log(`   ⚠️ Google API error: ${e}`);
    return 0;
  }
}

/**
 * Main automation run
 */
async function runAutomation(): Promise<void> {
  console.log('\n');
  console.log('█'.repeat(80));
  console.log('█  🤖 SMART SEO ENGINE - DIVERSIFIED CONTENT GENERATION              █');
  console.log('█'.repeat(80));
  console.log(`📅 Run started: ${new Date().toISOString()}`);
  console.log(`🧠 Model: ${CONFIG.MODEL} via OpenRouter`);
  console.log(`📊 Daily limit: ${CONFIG.DAILY_GENERATION_LIMIT} pages`);
  console.log('');

  // Load state
  const state = loadState();

  // First run: submit all existing URLs
  if (!state.initialSubmissionDone) {
    const submitted = await submitExistingUrls();
    if (submitted > 0) {
      state.initialSubmissionDone = true;
      state.dailyQuotaUsed = submitted;
      saveState(state);
    }
    console.log('');
  }

  // Check if quota reset needed
  const today = new Date().toISOString().split('T')[0];
  if (state.quotaResetDate !== today) {
    console.log('🔄 Daily quota reset');
    state.dailyQuotaUsed = 0;
    state.quotaResetDate = today;
  }

  // Check quota
  if (state.dailyQuotaUsed >= CONFIG.DAILY_GENERATION_LIMIT) {
    console.log('🚦 Daily quota exhausted. Waiting for reset.');
    return;
  }

  const remainingQuota = CONFIG.DAILY_GENERATION_LIMIT - state.dailyQuotaUsed;
  console.log(`📊 Quota remaining: ${remainingQuota}/${CONFIG.DAILY_GENERATION_LIMIT}`);
  console.log('');

  let generatedThisRun = 0;
  const results: Array<{ type: string; url: string; title: string; success: boolean }> = [];

  // Generate content based on rotation
  for (let i = 0; i < CONFIG.BATCH_SIZE && state.dailyQuotaUsed < CONFIG.DAILY_GENERATION_LIMIT; i++) {
    const contentType = getNextContentType(state);
    console.log(`\n📋 Content type: ${contentType.name} (${contentType.description})`);

    let result: { url: string; title: string; success: boolean };

    switch (contentType.id) {
      case 'competitor_comparison': {
        const competitor = getNextCompetitor(state);
        if (competitor) {
          result = await generateCompetitorComparison(competitor, state);
          if (result.success) {
            state.competitorsCovered.push(competitor.name);
          }
        } else {
          console.log('⚠️ No competitor to target');
          continue;
        }
        break;
      }

      case 'industry_trends': {
        // Rotate through trending topics
        const topics = [
          'AI job market 2026',
          'tech layoffs 2026',
          'remote work trends',
          'salary negotiation tips',
          'resume trends 2026',
          'interview trends',
          'ATS changes 2026',
          'LinkedIn algorithm',
          'job search statistics',
          'hiring trends 2026',
        ];
        const topic = topics[generatedThisRun % topics.length];
        result = await generateTrendingContent(topic, state);
        break;
      }

      case 'location_deep_dive': {
        const locationsPath = path.resolve(__dirname, '../../src/data/locations.json');
        const rolesPath = path.resolve(__dirname, '../../src/data/roles.json');

        let locations: any[] = [];
        let roles: any[] = [];

        try {
          locations = JSON.parse(fs.readFileSync(locationsPath, 'utf-8'));
          roles = JSON.parse(fs.readFileSync(rolesPath, 'utf-8'));
        } catch {
          console.log('⚠️ Could not load locations/roles data');
          continue;
        }

        const location = locations[Math.floor(Math.random() * locations.length)];
        const role = roles[Math.floor(Math.random() * roles.length)];

        result = await generateLocationContent(location.name, role.name, state);

        if (result.success) {
          state.locationsCovered.push(location.name);
          state.rolesCovered.push(role.name);
        }
        break;
      }

      case 'how_to_guides': {
        const guides = [
          'how to write a resume',
          'how to prepare for an interview',
          'how to negotiate salary',
          'how to optimize linkedin profile',
          'how to write a cover letter',
          'how to handle rejection',
          'how to network effectively',
          'how to switch careers',
          'how to work remotely',
          'how to get a promotion',
        ];
        const guide = guides[generatedThisRun % guides.length];
        result = await generateTrendingContent(guide, state);
        break;
      }

      case 'role_analysis': {
        const rolesPath = path.resolve(__dirname, '../../src/data/roles.json');
        let roles: any[] = [];
        try {
          roles = JSON.parse(fs.readFileSync(rolesPath, 'utf-8'));
        } catch {
          console.log('⚠️ Could not load roles data');
          continue;
        }
        const role = roles[Math.floor(Math.random() * roles.length)];
        result = await generateTrendingContent(`${role.name} career guide 2026`, state);
        if (result.success) {
          state.rolesCovered.push(role.name);
        }
        break;
      }

      case 'tool_reviews': {
        const tools = [
          { name: 'ChatGPT for job search', keywords: ['chatgpt resume', 'chatgpt interview'] },
          { name: 'Grammarly', keywords: ['grammarly resume', 'grammarly professional'] },
          { name: 'Canva Resume Builder', keywords: ['canva resume', 'canva cv'] },
          { name: 'LinkedIn Premium', keywords: ['linkedin premium worth it', 'linkedin premium job search'] },
          { name: 'Indeed Resume', keywords: ['indeed resume builder', 'indeed cv'] },
          { name: 'ZipRecruiter', keywords: ['ziprecruiter reviews', 'ziprecruiter worth it'] },
        ];
        const tool = tools[Math.floor(Math.random() * tools.length)];
        result = await generateTrendingContent(`${tool.name} review 2026`, state);
        break;
      }

      default:
        console.log(`⚠️ Unknown content type: ${contentType.id}`);
        continue;
    }

    results.push({ type: contentType.id, ...result });

    if (result.success) {
      state.generatedPages.push(result.url);
      state.dailyQuotaUsed++;
      generatedThisRun++;
    }

    // Rotate content type
    state.currentContentTypeIndex = (state.currentContentTypeIndex + 1) % CONTENT_TYPES.length;

    // Delay between generations
    if (i < CONFIG.BATCH_SIZE - 1 && state.dailyQuotaUsed < CONFIG.DAILY_GENERATION_LIMIT) {
      console.log(`\n⏳ Waiting ${CONFIG.BATCH_DELAY_MS / 1000}s before next generation...`);
      await new Promise(resolve => setTimeout(resolve, CONFIG.BATCH_DELAY_MS));
    }
  }

  // Save state
  state.lastRun = new Date().toISOString();
  state.totalGenerated += generatedThisRun;
  saveState(state);

  // Print summary
  console.log('\n');
  console.log('█'.repeat(80));
  console.log('█  📊 RUN SUMMARY                                                      █');
  console.log('█'.repeat(80));
  console.log(`✅ Generated this run: ${generatedThisRun} pages`);
  console.log(`📊 Daily quota used: ${state.dailyQuotaUsed}/${CONFIG.DAILY_GENERATION_LIMIT}`);
  console.log(`📈 Total generated: ${state.totalGenerated} pages`);
  console.log('');
  console.log('Generated URLs:');
  results.filter(r => r.success).forEach((r, i) => {
    console.log(`  ${i + 1}. [${r.type}] ${r.title}`);
    console.log(`     ${r.url}`);
  });
  console.log('');

  // Submit newly generated URLs to Google
  const successfulUrls = results.filter(r => r.success).map(r => r.url);
  if (successfulUrls.length > 0) {
    await submitUrlsToGoogle(successfulUrls);
  }

  // Log to file
  const logPath = path.resolve(__dirname, '../../logs/seo-run-log.json');
  const logDir = path.dirname(logPath);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  const logEntry = {
    timestamp: new Date().toISOString(),
    generatedThisRun,
    dailyQuotaUsed: state.dailyQuotaUsed,
    results,
    model: CONFIG.MODEL,
  };

  let logs: any[] = [];
  try {
    if (fs.existsSync(logPath)) {
      logs = JSON.parse(fs.readFileSync(logPath, 'utf-8'));
    }
  } catch { }
  logs.push(logEntry);
  fs.writeFileSync(logPath, JSON.stringify(logs, null, 2));
}

async function submitUrlsToGoogle(urls: string[]): Promise<number> {
  const keyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!keyEnv) {
    console.log('⚠️ GOOGLE_SERVICE_ACCOUNT_KEY not set, skipping URL submission');
    return 0;
  }

  console.log(`\n📤 Submitting ${urls.length} new URLs to Google...`);

  let keyContent;
  try {
    keyContent = JSON.parse(keyEnv);
  } catch {
    console.log('⚠️ Could not parse Google credentials');
    return 0;
  }

  try {
    const jwtClient = new google.auth.JWT({
      email: keyContent.client_email,
      key: keyContent.private_key,
      scopes: ['https://www.googleapis.com/auth/indexing']
    });

    await jwtClient.authorize();
    const indexing = google.indexing({ version: 'v3', auth: jwtClient });

    let successCount = 0;
    for (let i = 0; i < urls.length; i++) {
      try {
        await indexing.urlNotifications.publish({
          requestBody: { url: urls[i], type: 'URL_UPDATED' }
        });
        successCount++;
        console.log(`   ✅ Submitted: ${urls[i]}`);
        await new Promise(r => setTimeout(r, 200));
      } catch (e: any) {
        console.log(`   ⚠️ Failed: ${urls[i]} - ${e.message}`);
      }
    }

    console.log(`\n📤 Submitted ${successCount}/${urls.length} URLs to Google`);
    return successCount;
  } catch (e) {
    console.log(`⚠️ Google API error: ${e}`);
    return 0;
  }
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  // Check required env vars
  if (!process.env.LLM_API_KEY) {
    console.error('❌ LLM_API_KEY not set. Content generation will fail.');
    process.exit(1);
  }
  if (!process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
    console.warn('⚠️ GOOGLE_SERVICE_ACCOUNT_KEY not set. Google submission disabled.');
  }

  console.log('🚀 Starting Smart SEO Engine...');
  console.log(`🧠 Model: ${CONFIG.MODEL}`);
  console.log(`💰 Cost: ~$0.15 per 1M input tokens (GPT-4o-mini via OpenRouter)`);
  console.log('');

  try {
    await runAutomation();
  } catch (error) {
    console.error('❌ Automation failed:', error);
  }

  // Schedule next run in 4 hours
  const nextRun = new Date(Date.now() + 4 * 60 * 60 * 1000);
  console.log(`\n⏰ Next run scheduled: ${nextRun.toISOString()}`);
}

// Error handling
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled rejection:', error);
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught exception:', error);
});

main().catch(console.error);
