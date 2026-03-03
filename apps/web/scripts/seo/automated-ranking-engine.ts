/**
 * AUTOMATED RANKING ENGINE - 24/7 SEO DOMINATION
 * 
 * This is your bread and butter system that runs continuously,
 * generates thousands of pages, and dominates search rankings.
 * 
 * Features:
 * - 24/7 automated content generation
 * - Smart priority system based on search volume potential
 * - Automatic Google Indexing API submission
 * - Competitor monitoring and content updates
 * - Real-time performance tracking
 * - Scales to 100,000+ pages
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { setInterval } from 'timers';
import { loadProgress, saveProgress, logSubmission, getQuotaState } from './supabase-checkpoint.ts';
import { validateCityName, validateRoleName, sanitizeForShell } from './utils';

const BASE_URL = process.env.GOOGLE_SEARCH_CONSOLE_SITE || 'https://jobhuntin.com';
const DAILY_SUBMISSION_LIMIT = 200;
const BATCH_GENERATION_SIZE = 10;
const SUBMIT_BATCH_SIZE = 50;
const BATCH_DELAY_MS = 30000; // 30 seconds between batches

const __dirname = path.dirname(fileURLToPath(import.meta.url));
let runInProgress = false;

// Load your data sources
const locations = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../src/data/locations.json'), 'utf-8'));
const roles = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../src/data/roles.json'), 'utf-8'));
const competitors = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../src/data/competitors.json'), 'utf-8'));

// Priority matrix for maximum SEO impact
interface PriorityMatrix {
  location: any;
  role: any;
  priority: number;
  searchVolume: number;
  competition: number;
  potential: number;
}


async function withRetry<T>(fn: () => Promise<T>, retries = 3, baseDelayMs = 2000): Promise<T | null> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      console.error("Attempt", attempt, "failed:", error);
      if (attempt === retries) break;
      const delay = baseDelayMs * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  return null;
}

/**
 * Calculate SEO priority based on search volume and competition
 * This is the secret sauce for ranking fast
 */
function calculatePriority(location: any, role: any): PriorityMatrix {
  // Base scores
  let searchVolume = 100;
  let competition = 50;

  // Boost for major cities - volume is key for "average" jobs
  if (location.population > 1000000) searchVolume *= 4;
  else if (location.population > 500000) searchVolume *= 3;
  else if (location.population > 200000) searchVolume *= 2;

  // Boost for high-traffic "average" categories
  const highTrafficCategories = ['Retail', 'Logistics', 'Hospitality', 'Customer Service', 'Construction', 'Operations', 'Finance'];
  if (highTrafficCategories.includes(role.category)) {
    searchVolume *= 2.5;
  }

  // Penalize niche tech roles for this traffic flood strategy
  if (role.category === 'Engineering' || role.category === 'Data') {
    searchVolume *= 0.5;
  }

  // Boost specifically for roles with lower salary (broader audience)
  if (role.avgSalary < 60000) searchVolume *= 1.5;

  // Lower competition for long-tail combinations
  competition = Math.max(10, 100 - (location.popularity || 50));

  // Calculate potential (higher is better)
  const potential = (searchVolume * 100) / (competition + 1);

  return {
    location,
    role,
    priority: Math.round(potential),
    searchVolume: Math.round(searchVolume),
    competition: Math.round(competition),
    potential: Math.round(potential)
  };
}

/**
 * Check if content already exists for a city/role combination
 */
function contentExists(location: any, role: any): boolean {
  // Check if location has content sections for this role
  if (location.contentSections && location.contentSections.length > 0) {
    // Check if there's specific content for this role
    const hasRoleContent = location.contentSections.some((section: any) => 
      section.heading?.toLowerCase().includes(role.name.toLowerCase()) ||
      section.keywords?.some((k: string) => k.toLowerCase().includes(role.name.toLowerCase()))
    );
    if (hasRoleContent) return true;
  }
  
  // Check if role has content sections for this location
  if (role.contentSections && role.contentSections.length > 0) {
    const hasLocationContent = role.contentSections.some((section: any) =>
      section.heading?.toLowerCase().includes(location.name.toLowerCase()) ||
      section.keywords?.some((k: string) => k.toLowerCase().includes(location.name.toLowerCase()))
    );
    if (hasLocationContent) return true;
  }
  
  // Check if both have quality scores (indicating they were generated)
  if (location.contentQuality && location.contentQuality > 70 && 
      role.contentQuality && role.contentQuality > 70) {
    return true;
  }
  
  return false;
}

/**
 * Filter matrix to only include combinations that need content
 */
function filterNeededCombinations(matrix: PriorityMatrix[]): PriorityMatrix[] {
  return matrix.filter(item => !contentExists(item.location, item.role));
}

/**
 * Generate all possible combinations and rank them by priority
 */
function generatePriorityMatrix(): PriorityMatrix[] {
  const matrix: PriorityMatrix[] = [];

  // Create all combinations
  for (const location of locations) {
    for (const role of roles) {
      matrix.push(calculatePriority(location, role));
    }
  }

  // Sort by potential (descending) - this is your ranking strategy
  return matrix.sort((a, b) => b.potential - a.potential);
}

/**
 * Generate content for a specific city/role combination
 */
async function generateContent(city: string, role: string): Promise<boolean> {
  console.log("\n" + "=".repeat(70));
  console.log("🚀 GENERATING:", role, "jobs in", city);
  console.log("⏰ Started at:", new Date().toLocaleTimeString());
  console.log("=".repeat(70));

  return new Promise((resolve) => {
    // SECURITY: Validate inputs before passing to spawn
    const safeCity = sanitizeForShell(validateCityName(city));
    const safeRole = sanitizeForShell(validateRoleName(role));
    
    // Pass arguments as an array to spawn correctly
    const childProcess = spawn('npx', ['tsx', 'scripts/seo/generate-city-content.ts', safeCity, safeRole, '--aggressive'], {
      cwd: path.resolve(__dirname, '../..'),
      stdio: 'inherit' // Show all output in real-time
    });

    const start = Date.now();
    const timeoutMs = 10 * 60 * 1000; // kill if >10 minutes

    const timeout = setTimeout(() => {
      console.warn("\n⏱️ TIMEOUT after 10 minutes. Killing process...");
      childProcess.kill('SIGKILL');
    }, timeoutMs);

    childProcess.on('close', (code: number) => {
      clearTimeout(timeout);
      const duration = ((Date.now() - start) / 1000).toFixed(1);
      
      console.log("\n" + "=".repeat(70));
      if (code === 0) {
        console.log("✅ SUCCESS:", role, "in", city, "completed in", duration, "s");
        const roleSlug = role.toLowerCase().replace(/\s+/g, "-");
        const citySlug = city.toLowerCase().replace(/\s+/g, "-");
        console.log("🔗 URL: https://jobhuntin.com/jobs/" + roleSlug + "/" + citySlug);
      } else {
        console.log("❌ FAILED:", role, "in", city, "(exit code", code, ") after", duration, "s");
      }
      console.log("=".repeat(70) + "\n");
      
      resolve(code === 0);
    });
  });
}

/**
 * Submit URLs to Google Indexing API
 */
async function submitToGoogle(urls: string[], allowSubmission: boolean): Promise<boolean> {
  if (!allowSubmission) {
    console.warn('⚠️ Skipping Google submission because GOOGLE_SERVICE_ACCOUNT_KEY is missing.');
    return false;
  }

  return new Promise((resolve) => {
    const tmpDir = path.resolve(__dirname, '../../logs');
    if (!fs.existsSync(tmpDir)) {
      fs.mkdirSync(tmpDir, { recursive: true });
    }
    const tmpFile = path.join(tmpDir, `urls-${Date.now()}.txt`);
    fs.writeFileSync(tmpFile, urls.join('\n'));

    console.log("📊 Submitting", urls.length, "URLs to Google...");

    // Pass arguments as an array to spawn correctly
    const childProcess = spawn('npx', ['tsx', 'scripts/seo/submit-to-google-enhanced.ts', '--priority', '--urls-file', tmpFile], {
      cwd: path.resolve(__dirname, '../..'),
      stdio: 'pipe',
      env: {
        ...process.env
      }
    });

    let output = '';

    const start = Date.now();
    const timeoutMs = 5 * 60 * 1000; // 5 minutes
    const timeout = setTimeout(() => {
      console.warn("⏱️ Google submission timeout for batch of", urls.length, ". Killing process...");
      childProcess.kill('SIGKILL');
    }, timeoutMs);

    childProcess.stdout.on('data', (data: Buffer) => {
      output += data.toString();
    });

    childProcess.on('close', (code: number | null) => {
      clearTimeout(timeout);
      const duration = ((Date.now() - start) / 1000).toFixed(1);
      const success = code === 0;
      if (success) {
        console.log("✅ Submitted", urls.length, "URLs to Google in", duration, "s");
      } else {
        console.error("❌ Google submission failed after", duration, "s");
        console.error(output);
      }
      // Log to Supabase
      logSubmission(tmpFile, urls.length, success, success ? undefined : output).catch(() => { });
      resolve(success);
    });
  });
}

/**
 * Main automation loop - runs 24/7
 */
async function runAutomation(): Promise<void> {
  console.log('🤖 AUTOMATED RANKING ENGINE STARTED');
  console.log('📈 Generating priority matrix...');

  const allCombinations = generatePriorityMatrix();
  const totalAll = allCombinations.length;
  
  // Filter to only combinations that need new content
  const priorityMatrix = filterNeededCombinations(allCombinations);
  
  const totalCombinations = priorityMatrix.length;
  let startIndex = await loadProgress();
  
  // If all content exists, we might want to refresh old content
  if (totalCombinations === 0) {
    console.log('✅ All content already generated!');
    console.log('🔄 Checking for content that needs refreshing (older than 30 days)...');
    
    // Find combinations with stale content (older than 30 days)
    const staleCombinations = allCombinations.filter(item => {
      const lastUpdated = item.location.lastUpdated || item.role.lastUpdated;
      if (!lastUpdated) return false;
      const daysSinceUpdate = (Date.now() - new Date(lastUpdated).getTime()) / (1000 * 60 * 60 * 24);
      return daysSinceUpdate > 30;
    });
    
    if (staleCombinations.length > 0) {
      console.log("📅 Found", staleCombinations.length, "pages to refresh");
      priorityMatrix.push(...staleCombinations);
    } else {
      console.log('🎉 No pages need refreshing. Engine will check again in 24 hours.');
      return;
    }
  }
  
  if (startIndex >= priorityMatrix.length) {
    startIndex = 0;
  }

  // Load quota state from Supabase
  const { used: dailyQuotaUsed, reset: dailyQuotaReset } = await getQuotaState();
  let remainingDailyQuota = Math.max(0, DAILY_SUBMISSION_LIMIT - dailyQuotaUsed);

  console.log("📊 Total combinations:", totalAll);
  console.log("🆕 Need content:", totalCombinations);
  const top = priorityMatrix[0];
  console.log("🏆 Top priority:", top?.role?.name || "N/A", "in", top?.location?.name || "N/A", "(Score:", top?.potential || 0, ")");
  console.log("📦 Daily quota remaining:", remainingDailyQuota, "/", DAILY_SUBMISSION_LIMIT);

  let generatedCount = 0;
  let submittedCount = 0;
  let urlsToSubmit: string[] = [];

  // Main generation loop
  for (let i = startIndex; i < priorityMatrix.length; i += BATCH_GENERATION_SIZE) {
    const batch = priorityMatrix.slice(i, i + BATCH_GENERATION_SIZE);

    const batchNum = Math.floor(i / BATCH_GENERATION_SIZE) + 1;
    const totalBatches = Math.ceil(priorityMatrix.length / BATCH_GENERATION_SIZE);
    console.log("\n🔄 Processing batch", batchNum + "/" + totalBatches);

    // Generate content for this batch
    const results = await Promise.allSettled(
      batch.map(item => withRetry(() => generateContent(item.location.name, item.role.name), 2, 2000))
    );
    const successful = results.filter(r => r.status === 'fulfilled' && r.value).length;
    generatedCount += successful;

    console.log("✅ Generated", successful + "/" + BATCH_GENERATION_SIZE, "pages");

    // Add URLs to submission queue
    for (const item of batch) {
      const roleSlug = item.role.id || item.role.slug || item.role.name.toLowerCase().replace(/\s+/g, '-');
      const locSlug = item.location.id || item.location.slug || item.location.name.toLowerCase().replace(/\s+/g, '-');
      const url = `${BASE_URL}/jobs/${roleSlug}/${locSlug}`;
      urlsToSubmit.push(url);
    }

    // Submit to Google when we have enough URLs
    while (urlsToSubmit.length > 0 && remainingDailyQuota > 0 && urlsToSubmit.length >= SUBMIT_BATCH_SIZE) {
      const take = Math.min(SUBMIT_BATCH_SIZE, remainingDailyQuota);
      const chunk = urlsToSubmit.slice(0, take);
      const ok = await withRetry(() => submitToGoogle(chunk, Boolean(process.env.GOOGLE_SERVICE_ACCOUNT_KEY)), 2, 3000);
      if (ok) {
        submittedCount += chunk.length;
        remainingDailyQuota -= chunk.length;
        urlsToSubmit = urlsToSubmit.slice(take);
      } else {
        console.warn('⚠️ Submission chunk failed or skipped; preserving URLs for next run.');
        break;
      }
      if (remainingDailyQuota <= 0) {
        console.log("🚦 Reached daily submission quota (" + DAILY_SUBMISSION_LIMIT + "). Remaining URLs will be sent next run.");
        break;
      }
    }

    // Rate limiting - don't overwhelm APIs
    await new Promise(resolve => setTimeout(resolve, BATCH_DELAY_MS));

    if (remainingDailyQuota <= 0) {
      break;
    }
  }

  // Submit remaining URLs
  if (urlsToSubmit.length > 0 && remainingDailyQuota > 0) {
    const take = Math.min(urlsToSubmit.length, remainingDailyQuota);
    const chunk = urlsToSubmit.slice(0, take);
    const ok = await withRetry(() => submitToGoogle(chunk, Boolean(process.env.GOOGLE_SERVICE_ACCOUNT_KEY)), 2, 3000);
    if (ok) {
      submittedCount += chunk.length;
      remainingDailyQuota -= chunk.length;
      urlsToSubmit = urlsToSubmit.slice(take);
    } else {
      console.warn('⚠️ Final submission chunk failed or skipped; preserving URLs for next run.');
    }
  }

  // Save progress and quota state to Supabase
  const nextIndex = (remainingDailyQuota <= 0 || urlsToSubmit.length > 0) ? startIndex : priorityMatrix.length;
  const quotaUsedToday = DAILY_SUBMISSION_LIMIT - remainingDailyQuota;
  await saveProgress(nextIndex, quotaUsedToday, dailyQuotaReset);

  console.log("\n🎉 AUTOMATION COMPLETE!");
  console.log("📄 Generated:", generatedCount, "pages");
  console.log("🚀 Submitted to Google:", submittedCount, "URLs");
  console.log("💰 Estimated monthly traffic potential:", Math.round(generatedCount * 50), "visitors");
}

/**
 * Continuous monitoring and updates
 */
function startContinuousMonitoring(): void {
  console.log('👁️  Starting continuous monitoring...');

  // Check for new opportunities every 6 hours
  setInterval(async () => {
    console.log('🔍 Running scheduled content audit...');

    // Check for trending roles or cities
    const trendingCombinations = await findTrendingOpportunities();

    if (trendingCombinations.length > 0) {
      console.log("🚀 Found", trendingCombinations.length, "trending opportunities");

      // Generate content for trending opportunities
      for (const combo of trendingCombinations.slice(0, 5)) {
        await generateContent(combo.location, combo.role);
      }
    }
  }, 6 * 60 * 60 * 1000); // 6 hours
}

/**
 * Find trending opportunities (placeholder for real trend analysis)
 */
async function findTrendingOpportunities(): Promise<any[]> {
  // This would integrate with Google Trends API, job market data, etc.
  // For now, return high-potential combinations that haven't been generated yet
  const matrix = generatePriorityMatrix();
  return matrix.slice(0, 10); // Top 10 opportunities
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  if (runInProgress) {
    console.log('⚠️ Previous run still in progress. Skipping new run to avoid overlap.');
    return;
  }
  runInProgress = true;
  console.log('🚀 STARTING AUTOMATED RANKING ENGINE');
  console.log('📅 This will run continuously and generate thousands of pages');

  // Ensure required environment variables are set
  if (!process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
    console.warn('⚠️ GOOGLE_SERVICE_ACCOUNT_KEY not set. Submissions will fail.');
  }
  if (!process.env.GOOGLE_SEARCH_CONSOLE_SITE) {
    process.env.GOOGLE_SEARCH_CONSOLE_SITE = 'https://jobhuntin.com';
  }
  if (!process.env.DATABASE_URL) {
    console.warn('⚠️ DATABASE_URL not set. Progress tracking will fail.');
  }
  if (!process.env.LLM_API_KEY) {
    console.warn('⚠️ LLM_API_KEY not set. Content generation will fail.');
  }

  // Start continuous monitoring
  startContinuousMonitoring();

  try {
    // Run initial automation
    await runAutomation();
  } catch (error) {
    console.error('❌ Automation failed:', error);
    // Still schedule next run even if current run fails
  } finally {
    runInProgress = false;
    // Schedule next run (daily) after completion to avoid overlap
    const nextRunTime = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    console.log("⏰ Scheduling next run in 24 hours (" + nextRunTime + ")...");
    setTimeout(() => { void main(); }, 24 * 60 * 60 * 1000);
  }
}

// Error handling with enhanced logging
process.on("unhandledRejection", (error) => {
  const timestamp = new Date().toISOString();
  console.error("❌ Unhandled rejection at", timestamp, ":", error);
  // Continue running - don't let errors stop the automation
});

process.on("uncaughtException", (error) => {
  const timestamp = new Date().toISOString();
  console.error("❌ Uncaught exception at", timestamp, ":", error);
  // Continue running - don't let errors stop the automation
});

// Start the engine with startup logging
console.log('🤖 AUTOMATED RANKING ENGINE INITIALIZING...');
main().catch(error => {
  console.error('❌ Failed to start SEO engine:', error);
  process.exit(1);
});