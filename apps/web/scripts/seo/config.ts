/**
 * SEO Engine Configuration
 * 
 * Centralized configuration with validation and environment variable support.
 * All configuration is validated at startup to prevent runtime errors.
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';

/**
 * Google Service Account Key interface
 */
export interface GoogleServiceAccountKey {
  type: 'service_account';
  project_id: string;
  private_key_id: string;
  private_key: string;
  client_email: string;
  client_id: string;
  auth_uri: string;
  token_uri: string;
  auth_provider_x509_cert_url: string;
  client_x509_cert_url: string;
}

/**
 * SEO URL Endpoints - Centralized for easy updates
 */
export interface SEOUrlEndpoints {
  // Base URL
  baseUrl: string;

  // LLM API
  openRouterApiUrl: string;

  // Search Engine Indexing APIs
  googleIndexingApiUrl: string;
  googleSitemapPingUrl: string;
  bingSitemapPingUrl: string;

  // IndexNow API endpoints
  indexNowEndpoints: string[];
}

/**
 * Competitor Intelligence Configuration
 * Stores basic competitor metadata that can be loaded from JSON
 */
export interface CompetitorIntelligenceConfig {
  dataFile: string;
}

/**
 * SEO Engine Configuration
 */
export interface SEOConfig {
  // URLs
  urls: SEOUrlEndpoints;

  // Competitor data
  competitorConfig: CompetitorIntelligenceConfig;

  // Google API
  googleServiceAccountKey: GoogleServiceAccountKey;
  googleSearchConsoleUrl: string;

  // Database
  databaseUrl: string;

  // Redis
  redisUrl: string;

  // LLM
  llmApiKey: string;
  llmApiBase: string;
  llmModel: string;

  // Generation settings
  parallelWorkers: number;
  dailyGenerationLimit: number;
  batchSize: number;
  batchDelayMs: number;
  contentFreshnessHours: number;

  // Submission settings
  submissionBatchSize: number;
  submissionDelayMs: number;
  submissionMaxRetries: number;

  // Environment
  environment: 'development' | 'production';
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

/**
 * Validate Google Service Account Key format
 */
function validateGoogleKey(keyConfig: string): GoogleServiceAccountKey {
  let key: Partial<GoogleServiceAccountKey>;

  try {
    // Try to parse as JSON
    key = JSON.parse(keyConfig);
  } catch {
    // Try to load from file
    if (fs.existsSync(keyConfig)) {
      try {
        key = JSON.parse(fs.readFileSync(keyConfig, 'utf-8'));
      } catch (e) {
        throw new Error(`Invalid JSON in Google key file: ${keyConfig}`);
      }
    } else {
      throw new Error('GOOGLE_SERVICE_ACCOUNT_KEY is neither valid JSON nor a file path');
    }
  }

  // Validate required fields
  const required = ['type', 'project_id', 'private_key', 'client_email'];
  for (const field of required) {
    if (!key[field]) {
      throw new Error(`Missing required field in Google key: ${field}`);
    }
  }

  if (key.type !== 'service_account') {
    throw new Error(`Invalid key type: ${key.type} (expected "service_account")`);
  }

  // Validate private key format
  if (!key.private_key.includes('BEGIN PRIVATE KEY') && !key.private_key.includes('BEGIN RSA PRIVATE KEY')) {
    throw new Error('Invalid private key format (missing PEM headers)');
  }

  // Sanitize private key - ensure proper newlines
  key.private_key = key.private_key
    .replace(/\\n/g, '\n')
    .replace(/\\/g, '')
    .trim();

  return key as GoogleServiceAccountKey;
}

/**
 * Validate numeric configuration
 */
function validateNumericConfig(
  value: number,
  name: string,
  min: number,
  max: number
): number {
  if (isNaN(value) || value < min || value > max) {
    throw new Error(
      `Invalid ${name}: ${value} (must be between ${min} and ${max})`
    );
  }
  return value;
}

/**
 * Load URL endpoints from environment variables
 */
function loadUrlEndpoints(): SEOUrlEndpoints {
  return {
    // Base URL - primary site URL
    baseUrl: process.env.BASE_URL || 'https://jobhuntin.com',

    // LLM API - OpenRouter endpoint
    openRouterApiUrl: process.env.OPENROUTER_API_URL || 'https://openrouter.ai/api/v1',

    // Google Indexing API
    googleIndexingApiUrl: 'https://indexing.googleapis.com/v3/urlNotifications:publish',

    // Sitemap ping URLs
    googleSitemapPingUrl: 'https://www.google.com/ping',
    bingSitemapPingUrl: 'https://www.bing.com/ping',

    // IndexNow API endpoints (Bing, Yandex, Seznam, etc.)
    indexNowEndpoints: [
      'https://api.indexnow.org/indexnow',
      'https://www.bing.com/indexnow',
      'https://yandex.com/indexnow',
    ],
  };
}

/**
 * Load competitor intelligence configuration
 */
function loadCompetitorConfig(): CompetitorIntelligenceConfig {
  return {
    // Path relative to the SEO scripts directory
    dataFile: process.env.SEO_COMPETITOR_DATA_FILE || '../../src/data/competitors.json',
  };
}

/**
 * Load and validate configuration from environment variables
 */
export function loadAndValidateConfig(): SEOConfig {
  const googleKeyEnv = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!googleKeyEnv) {
    throw new Error('Missing required environment variable: GOOGLE_SERVICE_ACCOUNT_KEY');
  }

  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('Missing required environment variable: DATABASE_URL');
  }

  const llmApiKey = process.env.LLM_API_KEY;
  if (!llmApiKey) {
    throw new Error('Missing required environment variable: LLM_API_KEY');
  }

  const urls = loadUrlEndpoints();
  const competitorConfig = loadCompetitorConfig();

  const config: SEOConfig = {
    // URLs
    urls,

    // Competitor config
    competitorConfig,

    // Google API
    googleServiceAccountKey: validateGoogleKey(googleKeyEnv),
    googleSearchConsoleUrl: process.env.GOOGLE_SEARCH_CONSOLE_SITE || '',

    // Database
    databaseUrl,

    // Redis
    redisUrl: process.env.REDIS_URL || 'redis://localhost:6379/0',

    // LLM - use URLs from config
    llmApiKey,
    llmApiBase: process.env.LLM_API_BASE || urls.openRouterApiUrl,
    llmModel: process.env.LLM_MODEL || 'openai/gpt-4o-mini',

    // Generation settings
    parallelWorkers: validateNumericConfig(
      parseInt(process.env.SEO_PARALLEL_WORKERS || '2'),
      'SEO_PARALLEL_WORKERS',
      1,
      10
    ),
    dailyGenerationLimit: validateNumericConfig(
      parseInt(process.env.SEO_DAILY_LIMIT || '50'),
      'SEO_DAILY_LIMIT',
      1,
      1000
    ),
    batchSize: validateNumericConfig(
      parseInt(process.env.SEO_BATCH_SIZE || '5'),
      'SEO_BATCH_SIZE',
      1,
      50
    ),
    batchDelayMs: validateNumericConfig(
      parseInt(process.env.SEO_BATCH_DELAY_MS || '30000'),
      'SEO_BATCH_DELAY_MS',
      1000,
      300000
    ),
    contentFreshnessHours: validateNumericConfig(
      parseInt(process.env.SEO_CONTENT_FRESHNESS_HOURS || '2'),
      'SEO_CONTENT_FRESHNESS_HOURS',
      1,
      168
    ),

    // Submission settings
    submissionBatchSize: validateNumericConfig(
      parseInt(process.env.SEO_SUBMISSION_BATCH_SIZE || '10'),
      'SEO_SUBMISSION_BATCH_SIZE',
      1,
      100
    ),
    submissionDelayMs: validateNumericConfig(
      parseInt(process.env.SEO_SUBMISSION_DELAY_MS || '2000'),
      'SEO_SUBMISSION_DELAY_MS',
      100,
      60000
    ),
    submissionMaxRetries: validateNumericConfig(
      parseInt(process.env.SEO_SUBMISSION_MAX_RETRIES || '5'),
      'SEO_SUBMISSION_MAX_RETRIES',
      1,
      20
    ),

    // Environment
    environment: (process.env.NODE_ENV as 'development' | 'production') || 'development',
    logLevel: (process.env.LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') || 'info',
  };

  // Validate Google Search Console URL if provided
  if (config.googleSearchConsoleUrl && !config.googleSearchConsoleUrl.startsWith('https://')) {
    throw new Error('GOOGLE_SEARCH_CONSOLE_SITE must be a valid HTTPS URL');
  }

  // Validate base URL format
  if (!config.urls.baseUrl.startsWith('https://') && !config.urls.baseUrl.startsWith('http://')) {
    throw new Error('BASE_URL must be a valid HTTP/HTTPS URL');
  }

  return config;
}

/**
 * Get configuration singleton
 */
let configInstance: SEOConfig | null = null;

export function getConfig(): SEOConfig {
  if (!configInstance) {
    configInstance = loadAndValidateConfig();
  }
  return configInstance;
}

/**
 * Reset configuration (for testing)
 */
export function resetConfig(): void {
  configInstance = null;
}
