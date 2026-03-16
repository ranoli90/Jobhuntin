/**
 * Input Validation Utilities
 * 
 * Comprehensive validation for all SEO engine inputs to prevent injection attacks
 * and ensure data integrity.
 */

/**
 * Validation error
 */
export class ValidationError extends Error {
  constructor(
    public field: string,
    message: string,
    public value?: unknown
  ) {
    super(`Validation error in ${field}: ${message}`);
    this.name = 'ValidationError';
  }
}

/**
 * Validate topic string
 */
export function validateTopic(topic: string): string {
  if (!topic || typeof topic !== 'string') {
    throw new ValidationError('topic', 'Topic must be a non-empty string', topic);
  }

  const trimmed = topic.trim();

  if (trimmed.length === 0) {
    throw new ValidationError('topic', 'Topic cannot be empty after trimming', topic);
  }

  if (trimmed.length > 200) {
    throw new ValidationError('topic', 'Topic must be less than 200 characters', topic);
  }

  // Remove potentially dangerous characters
  const sanitized = trimmed
    .replace(/[<>\"'`]/g, '')
    .replace(/\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (!sanitized) {
    throw new ValidationError('topic', 'Topic contains only invalid characters', topic);
  }

  // Check for SQL injection patterns
  if (/(\bOR\b|\bAND\b|\bDROP\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)/i.test(sanitized)) {
    throw new ValidationError('topic', 'Topic contains suspicious SQL patterns', topic);
  }

  return sanitized;
}

/**
 * Validate intent type
 */
export function validateIntent(intent: string): string {
  const validIntents = ['informational', 'commercial', 'transactional', 'navigational'];

  if (!intent || typeof intent !== 'string') {
    throw new ValidationError('intent', 'Intent must be a non-empty string', intent);
  }

  const normalized = intent.toLowerCase().trim();

  if (!validIntents.includes(normalized)) {
    throw new ValidationError(
      'intent',
      `Intent must be one of: ${validIntents.join(', ')}`,
      intent
    );
  }

  return normalized;
}

/**
 * Validate competitor name
 */
export function validateCompetitor(competitor: string | undefined): string | undefined {
  if (!competitor) {
    return undefined;
  }

  if (typeof competitor !== 'string') {
    throw new ValidationError('competitor', 'Competitor must be a string', competitor);
  }

  const trimmed = competitor.trim();

  if (trimmed.length === 0) {
    return undefined;
  }

  if (trimmed.length > 100) {
    throw new ValidationError('competitor', 'Competitor must be less than 100 characters', competitor);
  }

  // Remove potentially dangerous characters
  const sanitized = trimmed
    .replace(/[<>\"'`]/g, '')
    .replace(/\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (!sanitized) {
    throw new ValidationError('competitor', 'Competitor contains only invalid characters', competitor);
  }

  return sanitized;
}

/**
 * Validate URL
 */
export function validateUrl(url: string): string {
  if (!url || typeof url !== 'string') {
    throw new ValidationError('url', 'URL must be a non-empty string', url);
  }

  try {
    const parsed = new URL(url);

    // Only allow HTTPS
    if (parsed.protocol !== 'https:') {
      throw new ValidationError('url', 'URL must use HTTPS protocol', url);
    }

    return url;
  } catch (e) {
    throw new ValidationError('url', 'Invalid URL format', url);
  }
}

/**
 * Validate email
 */
export function validateEmail(email: string): string {
  if (!email || typeof email !== 'string') {
    throw new ValidationError('email', 'Email must be a non-empty string', email);
  }

  const trimmed = email.trim().toLowerCase();

  // Simple email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(trimmed)) {
    throw new ValidationError('email', 'Invalid email format', email);
  }

  if (trimmed.length > 254) {
    throw new ValidationError('email', 'Email must be less than 254 characters', email);
  }

  return trimmed;
}

/**
 * Validate batch of URLs
 */
export function validateUrlBatch(urls: string[]): string[] {
  if (!Array.isArray(urls)) {
    throw new ValidationError('urls', 'URLs must be an array', urls);
  }

  if (urls.length === 0) {
    throw new ValidationError('urls', 'URLs array cannot be empty', urls);
  }

  if (urls.length > 10000) {
    throw new ValidationError('urls', 'URLs array cannot exceed 10000 items', urls);
  }

  return urls.map((url, index) => {
    try {
      return validateUrl(url);
    } catch (e) {
      throw new ValidationError(`urls[${index}]`, (e as Error).message, url);
    }
  });
}

/**
 * Validate service ID
 */
export function validateServiceId(serviceId: string): string {
  if (!serviceId || typeof serviceId !== 'string') {
    throw new ValidationError('serviceId', 'Service ID must be a non-empty string', serviceId);
  }

  const trimmed = serviceId.trim();

  if (trimmed.length === 0) {
    throw new ValidationError('serviceId', 'Service ID cannot be empty', serviceId);
  }

  if (trimmed.length > 100) {
    throw new ValidationError('serviceId', 'Service ID must be less than 100 characters', serviceId);
  }

  // Only allow alphanumeric, hyphens, underscores
  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    throw new ValidationError('serviceId', 'Service ID can only contain alphanumeric characters, hyphens, and underscores', serviceId);
  }

  return trimmed;
}

/**
 * Validate batch size
 */
export function validateBatchSize(size: number, min: number = 1, max: number = 1000): number {
  if (!Number.isInteger(size) || size < min || size > max) {
    throw new ValidationError('batchSize', `Batch size must be an integer between ${min} and ${max}`, size);
  }
  return size;
}

/**
 * Validate retry count
 */
export function validateRetryCount(count: number, max: number = 10): number {
  if (!Number.isInteger(count) || count < 0 || count > max) {
    throw new ValidationError('retryCount', `Retry count must be an integer between 0 and ${max}`, count);
  }
  return count;
}

/**
 * Validate delay in milliseconds
 */
export function validateDelay(delayMs: number, min: number = 0, max: number = 300000): number {
  if (!Number.isInteger(delayMs) || delayMs < min || delayMs > max) {
    throw new ValidationError('delay', `Delay must be an integer between ${min}ms and ${max}ms`, delayMs);
  }
  return delayMs;
}

/**
 * Type for sanitizable values
 */
type SanitizedValue = string | number | boolean | null | undefined | Record<string, unknown> | unknown[];

/**
 * Sanitize string for logging (remove sensitive data)
 */
export function sanitizeForLogging(value: unknown): SanitizedValue {
  if (typeof value === 'string') {
    // Remove API keys, tokens, etc.
    return value
      .replace(/sk-[a-zA-Z0-9]{20,}/g, 'sk-***')
      .replace(/Bearer\s+[a-zA-Z0-9_-]+/g, 'Bearer ***')
      .replace(/api[_-]?key[=:]\s*[a-zA-Z0-9_-]+/gi, 'api_key=***');
  }

  if (typeof value === 'object' && value !== null) {
    const sanitized: Record<string, SanitizedValue> = Array.isArray(value) ? [] as unknown as Record<string, SanitizedValue> : {};
    for (const [key, val] of Object.entries(value)) {
      if (key.toLowerCase().includes('key') || key.toLowerCase().includes('secret') || key.toLowerCase().includes('token')) {
        sanitized[key] = '***';
      } else {
        sanitized[key] = sanitizeForLogging(val);
      }
    }
    return sanitized;
  }

  return value;
}
