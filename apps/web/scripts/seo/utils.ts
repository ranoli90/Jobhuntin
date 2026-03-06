/**
 * SEO Script Utilities - Input validation and safe execution
 * 
 * SECURITY: All SEO scripts must validate inputs before passing to child processes
 * to prevent command injection attacks.
 */

import path from 'path';

// Allowed characters for file paths and identifiers
const SAFE_PATH_PATTERN = /^[a-zA-Z0-9\-_\./]+$/;
const SAFE_IDENTIFIER_PATTERN = /^[a-zA-Z0-9\-_]+$/;
const SAFE_CITY_ROLE_PATTERN = /^[a-zA-Z0-9\-_\s,']+$/;
// Keywords can have spaces (e.g., "simplify jobs", "remote work")
const SAFE_KEYWORD_PATTERN = /^[a-zA-Z0-9\-_\s]+$/;

/**
 * Validates that a string is safe to pass as a command argument.
 * Prevents command injection via shell metacharacters.
 */
export function validateSafeString(input: string, pattern: RegExp, maxLength: number = 100): string {
  if (typeof input !== 'string') {
    throw new Error(`Input must be a string, got ${typeof input}`);
  }
  
  if (input.length > maxLength) {
    throw new Error(`Input exceeds maximum length of ${maxLength}`);
  }
  
  if (!pattern.test(input)) {
    throw new Error(`Input contains invalid characters: ${input.substring(0, 50)}`);
  }
  
  // Check for path traversal attempts
  if (input.includes('..')) {
    throw new Error('Path traversal detected');
  }
  
  return input;
}

/**
 * Validates a city name for SEO scripts.
 */
export function validateCityName(city: string): string {
  return validateSafeString(city, SAFE_CITY_ROLE_PATTERN, 100);
}

/**
 * Validates a role name for SEO scripts.
 */
export function validateRoleName(role: string): string {
  return validateSafeString(role, SAFE_CITY_ROLE_PATTERN, 100);
}

/**
 * Validates a competitor name.
 */
export function validateCompetitorName(name: string): string {
  return validateSafeString(name, SAFE_IDENTIFIER_PATTERN, 50);
}

/**
 * Validates a file path.
 */
export function validateFilePath(filePath: string): string {
  const normalized = path.normalize(filePath);
  return validateSafeString(normalized, SAFE_PATH_PATTERN, 200);
}

/**
 * Validates keyword list.
 */
export function validateKeywords(keywords: string[]): string[] {
  if (!Array.isArray(keywords)) {
    throw new Error('Keywords must be an array');
  }
  // Keywords can contain spaces (e.g., "simplify jobs", "remote work")
  return keywords.map(k => validateSafeString(k, SAFE_KEYWORD_PATTERN, 100));
}

/**
 * Sanitizes a string for safe shell usage (removes all shell metacharacters).
 */
export function sanitizeForShell(input: string): string {
  return input
    .replace(/[&;|$`\\"'<>{}\[\]()]/g, '')
    .replace(/\n|\r|\t/g, ' ')
    .trim();
}

/**
 * Validates an array of URLs.
 */
export function validateUrls(urls: string[]): string[] {
  if (!Array.isArray(urls)) {
    throw new Error('URLs must be an array');
  }
  return urls.map(url => {
    try {
      const parsed = new URL(url);
      // Only allow http/https
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        throw new Error(`Invalid protocol: ${parsed.protocol}`);
      }
      return url;
    } catch {
      throw new Error(`Invalid URL: ${url}`);
    }
  });
}

/**
 * Environment variable validation for SEO scripts.
 */
export function validateEnvVars(required: string[]): void {
  const missing: string[] = [];
  for (const env of required) {
    if (!process.env[env]) {
      missing.push(env);
    }
  }
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}
