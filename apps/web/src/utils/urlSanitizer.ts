// URL Slug Sanitization - Prevents spammy URLs and ensures clean structure
export interface SlugSanitizationOptions {
  maxLength?: number;
  allowHyphens?: boolean;
  removeStopWords?: boolean;
  preventKeywordStuffing?: boolean;
}

const DEFAULT_OPTIONS: SlugSanitizationOptions = {
  maxLength: 50,
  allowHyphens: true,
  removeStopWords: true,
  preventKeywordStuffing: true
};

// Common stop words that should be removed from slugs
const STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
  'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
  'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
  'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
  'can', 'shall', 'job', 'jobs', 'career', 'careers', 'position', 'positions', 'role', 'roles'
]);

// Common keyword stuffing patterns to detect and prevent
const STUFFING_PATTERNS = [
  /(lead|principal|senior|junior|entry|mid|level).{0,10}\1/i, // Repeated prefixes
  /(manager|director|engineer|developer|analyst).{0,10}\1/i, // Repeated roles
  /(remote|hybrid|onsite|inoffice).{0,10}\1/i, // Repeated work types
  /(full|part|time|contract|temporary).{0,10}\1/i, // Repeated employment types
  /^.{60,}/, // Overly long slugs
  /(\w+)(-\1){2,}/i, // Repeated words with hyphens
];

/**
 * Sanitizes a string to create a clean, SEO-friendly URL slug
 */
export function sanitizeSlug(
  input: string, 
  options: SlugSanitizationOptions = {}
): string {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  if (!input || typeof input !== 'string') {
    return '';
  }

  // Convert to lowercase and trim
  let slug = input.toLowerCase().trim();
  
  // Remove special characters except hyphens and spaces
  slug = slug.replace(/[^a-z0-9\s-]/g, '');
  
  // Remove multiple spaces and hyphens
  slug = slug.replace(/\s+/g, ' ').replace(/-+/g, '-');
  
  // Remove stop words if enabled
  if (opts.removeStopWords) {
    slug = slug
      .split(' ')
      .filter(word => !STOP_WORDS.has(word))
      .join(' ');
  }
  
  // Prevent keyword stuffing
  if (opts.preventKeywordStuffing) {
    for (const pattern of STUFFING_PATTERNS) {
      if (pattern.test(slug)) {
        // If stuffing detected, take only first meaningful part
        const words = slug.split(/[\s-]+/).slice(0, 3);
        slug = words.join('-');
        break;
      }
    }
  }
  
  // Limit length
  if (opts.maxLength && slug.length > opts.maxLength) {
    slug = slug.substring(0, opts.maxLength).replace(/-+$/, '');
  }
  
  // Replace spaces with hyphens if allowed
  if (opts.allowHyphens) {
    slug = slug.replace(/\s+/g, '-');
  } else {
    slug = slug.replace(/\s+/g, '');
  }
  
  // Remove leading/trailing hyphens
  slug = slug.replace(/^-+|-+$/g, '');
  
  return slug || 'unknown'; // Fallback to prevent empty slugs
}

/**
 * Validates if a slug is clean and not spammy
 */
export function isValidSlug(slug: string): boolean {
  if (!slug || typeof slug !== 'string') return false;
  
  // Check for stuffing patterns
  for (const pattern of STUFFING_PATTERNS) {
    if (pattern.test(slug)) return false;
  }
  
  // Check length
  if (slug.length > 60) return false;
  
  // Check for too many hyphens (indicates stuffing)
  const hyphenCount = (slug.match(/-/g) || []).length;
  if (hyphenCount > 3) return false;
  
  // Check for repeated characters
  const repeatedChars = slug.match(/(.)\1{2,}/g);
  if (repeatedChars) return false;
  
  return true;
}

/**
 * Generates a clean job role slug
 */
export function generateJobSlug(role: string, seniority?: string): string {
  const parts = [];
  
  // Add seniority if provided and not already in role
  if (seniority && !role.toLowerCase().includes(seniority.toLowerCase())) {
    parts.push(seniority);
  }
  
  parts.push(role);
  
  return sanitizeSlug(parts.join('-'));
}

/**
 * Generates a clean location slug
 */
export function generateLocationSlug(city: string, state?: string, country?: string): string {
  const parts = [];
  
  if (city) parts.push(city);
  if (state) parts.push(state);
  if (country && country !== 'USA') parts.push(country); // Don't add USA for US locations
  
  return sanitizeSlug(parts.join('-'));
}

/**
 * Creates a clean job page URL path
 */
export function generateJobPagePath(role: string, location: string): string {
  const roleSlug = generateJobSlug(role);
  const locationSlug = generateLocationSlug(location);
  
  return `/jobs/${roleSlug}/${locationSlug}`;
}

/**
 * Validates and cleans existing URLs
 */
export function cleanExistingUrl(url: string): string {
  try {
    const urlObj = new URL(url);
    const pathParts = urlObj.pathname.split('/').filter(Boolean);
    
    if (pathParts.length >= 3 && pathParts[0] === 'jobs') {
      const role = pathParts[1];
      const location = pathParts[2];
      
      // Clean role and location slugs
      const cleanRole = sanitizeSlug(role);
      const cleanLocation = sanitizeSlug(location);
      
      return `/jobs/${cleanRole}/${cleanLocation}`;
    }
    
    return url;
  } catch {
    return url;
  }
}

/**
 * Detects if a URL pattern indicates spammy generation
 */
export function detectSpammyPattern(url: string): boolean {
  const path = new URL(url, 'https://jobhuntin.com').pathname;
  const pathParts = path.split('/').filter(Boolean);
  
  // Check for job pages with suspicious patterns
  if (pathParts.length >= 3 && pathParts[0] === 'jobs') {
    const role = pathParts[1];
    const location = pathParts[2];
    
    // Check for repeated keywords
    const roleWords = role.split('-');
    const locationWords = location.split('-');
    
    // Count repeated words
    const wordCount: Record<string, number> = {};
    [...roleWords, ...locationWords].forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    // If any word appears more than twice, it's likely spam
    const hasRepeats = Object.values(wordCount).some(count => count > 2);
    
    // Check for undefined or empty parts
    const hasUndefined = role.includes('undefined') || location.includes('undefined');
    
    return hasRepeats || hasUndefined || !isValidSlug(role) || !isValidSlug(location);
  }
  
  return false;
}

/**
 * Bulk clean URLs from a list
 */
export function cleanUrlList(urls: string[]): Array<{ original: string; cleaned: string; isSpammy: boolean }> {
  return urls.map(url => ({
    original: url,
    cleaned: cleanExistingUrl(url),
    isSpammy: detectSpammyPattern(url)
  }));
}
