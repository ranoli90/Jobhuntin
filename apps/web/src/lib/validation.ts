/**
 * Comprehensive Validation Library
 * Microsoft-level implementation with security-first approach
 */

// XSS Protection Utilities
export class XSSProtection {
  private static readonly HTML_ENTITIES = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
    "`": "&#x60;",
    "=": "&#x3D;",
  };

  private static readonly CSS_KEYWORDS = [
    "javascript:",
    "data:",
    "vbscript:",
    "onload=",
    "onerror=",
    "onclick=",
    "onmouseover=",
    "onfocus=",
    "onblur=",
    "onchange=",
    "onsubmit=",
    "expression(",
    "import(",
    "url(",
    "@import",
    "behavior:",
  ];

  static sanitizeHTML(input: string): string {
    if (typeof input !== "string") return "";

    return input
      .replaceAll(/["&'/<=>`]/g, (match) => this.HTML_ENTITIES[match as keyof typeof XSSProtection.HTML_ENTITIES] || match)
      .replaceAll(/<script[^>]*>.*?<\/script>/gi, "")
      .replaceAll(/<iframe[^>]*>.*?<\/iframe>/gi, "")
      .replaceAll(/<object[^>]*>.*?<\/object>/gi, "")
      .replaceAll(/<embed[^>]*>/gi, "")
      .replaceAll(/javascript:/gi, "")
      .replaceAll(/on\w+\s*=/gi, "");
  }

  static sanitizeCSS(input: string): string {
    if (typeof input !== "string") return "";

    let sanitized = input.toLowerCase();

    // Remove dangerous CSS keywords (escape regex special chars for safety)
    for (const keyword of this.CSS_KEYWORDS) {
      const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      // nosemgrep: javascript.lang.security.audit.detect-non-literal-regexp - keywords from constant array, escaped for ReDoS safety
      sanitized = sanitized.replace(new RegExp(escaped, 'gi'), '');
    }

      // Remove url() functions that could contain javascript
      sanitized = sanitized.replaceAll(/url\s*\(\s*["']*javascript:[^"']*["']*\s*\)/gi, '');

    return sanitized;
  }

  static sanitizeURL(url: string): string {
    if (typeof url !== "string") return "";

    try {
      // Basic URL validation
      const parsed = new URL(url);

      // Only allow http, https, and relative protocols
      if (!["http:", "https:", ""].includes(parsed.protocol)) {
        return "";
      }

      // Remove dangerous characters
      return parsed.toString().replaceAll(/["'<>`]/g, "");
    } catch {
      // If URL parsing fails, do basic sanitization
      return url.replaceAll(/["'<>`]/g, "").slice(0, 2048);
    }
  }

  static sanitizeInput(input: string, maxLength: number = 1000): string {
    if (typeof input !== "string") return "";

    return input
      .slice(0, Math.max(0, maxLength))
      .replaceAll(/[\u0000-\u001F\u007F]/g, "") // Remove control characters
      .replaceAll(/[<>]/g, "") // Remove HTML brackets
      .replaceAll(/javascript:/gi, "") // Remove JavaScript protocol
      .replaceAll(/data:/gi, "") // Remove data URIs
      .replaceAll(/vbscript:/gi, "") // Remove VBScript protocol
      .replaceAll(/on\w+\s*=/gi, "") // Remove event handlers
      .trim();
  }
}

// Input Validation Schemas
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: string) => string | null;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export class Validator {
  static email(email: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!email) {
      errors.push("Email is required");
      return { isValid: false, errors, warnings };
    }

    // RFC 5322 compliant email validation
    // Domain must allow dot-separated labels (e.g. example.com, company.co.uk)
    const emailRegex =
      /^[\w!#$%&'*+./=?^`{|}~-]+@(?:[\dA-Za-z](?:[\dA-Za-z-]{0,61}[\dA-Za-z])?\.)+[\dA-Za-z](?:[\dA-Za-z-]{0,61}[\dA-Za-z])?$/;
    if (!emailRegex.test(email)) {
      errors.push("Invalid email format");
    }

    // Length validation
    if (email.length > 254) {
      errors.push("Email address is too long");
    }

    // Local part validation (before @)
    const [localPart, domain] = email.split("@");
    if (localPart.length > 64) {
      errors.push("Local part is too long");
    }

    // Domain validation
    if (domain) {
      if (domain.length > 253) {
        errors.push("Domain name is too long");
      }

      // Check for consecutive dots
      if (domain.includes("..")) {
        errors.push("Domain cannot contain consecutive dots");
      }

      // Check domain starts/ends with hyphen
      if (domain.startsWith("-") || domain.endsWith("-")) {
        errors.push("Domain cannot start or end with hyphen");
      }
    }

    // Check for suspicious patterns
    if (email.includes("+") && email.split("+").length > 2) {
      warnings.push("Multiple plus signs detected");
    }

    // Check for common disposable email patterns
    const disposablePatterns = [
      "temp",
      "throwaway",
      "10minutemail",
      "guerrillamail",
      "yopmail",
    ];
    const lowerEmail = email.toLowerCase();
    for (const pattern of disposablePatterns) {
      if (lowerEmail.includes(pattern)) {
        warnings.push("Possible disposable email address");
        break;
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  static password(password: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!password) {
      errors.push("Password is required");
      return { isValid: false, errors, warnings };
    }

    // Length requirements
    if (password.length < 10) {
      errors.push("Password must be at least 10 characters long");
    }

    if (password.length > 128) {
      errors.push("Password is too long");
    }

    // Character requirements
    if (!/[a-z]/.test(password)) {
      errors.push("Password must contain lowercase letters");
    }

    if (!/[A-Z]/.test(password)) {
      errors.push("Password must contain uppercase letters");
    }

    if (!/\d/.test(password)) {
      errors.push("Password must contain numbers");
    }

    if (!/[!"#$%&'()*+,./:;<=>?@[\\\]^_{|}\-]/.test(password)) {
      errors.push("Password must contain special characters");
    }

    // Security warnings
    if (password.toLowerCase().includes("password")) {
      warnings.push('Password should not contain the word "password"');
    }

    if (password.toLowerCase().includes("123456")) {
      warnings.push("Avoid using sequential numbers");
    }

    // Check for common patterns
    const commonPatterns = [
      /^123456/,
      /^password/i,
      /^qwerty/i,
      /^admin/i,
      /123456$/,
      /password$/i,
      /qwerty$/i,
      /admin$/,
    ];

    if (commonPatterns.some((pattern) => pattern.test(password))) {
      warnings.push("Password is too common");
    }

    // Dictionary check for common passwords
    const commonPasswords = [
      "password",
      "123456",
      "password123",
      "admin",
      "qwerty",
      "letmein",
      "welcome",
      "monkey",
      "dragon",
      "master",
      "sunshine",
      "iloveyou",
      "football",
      "baseball",
      "shadow",
      "superman",
      "michael",
      "ninja",
      "mustang",
      "password1",
    ];

    if (commonPasswords.includes(password.toLowerCase())) {
      errors.push("Password is too common");
    }

    // Check for keyboard patterns
    if (this._hasKeyboardPattern(password)) {
      warnings.push("Password contains keyboard pattern");
    }

    // Check for repeated characters
    if (this._hasExcessiveRepetition(password)) {
      warnings.push("Password contains excessive repetition");
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  private static _hasKeyboardPattern(password: string): boolean {
    const keyboardPatterns = [
      "qwerty",
      "asdf",
      "zxcv",
      "1234",
      "qweasd",
      "qwertyuiop",
      "asdfghjkl",
      "zxcvbnm",
    ];
    const lowerPassword = password.toLowerCase();
    return keyboardPatterns.some((pattern) => lowerPassword.includes(pattern));
  }

  private static _hasExcessiveRepetition(password: string): boolean {
    // Check if more than 50% of password is the same character
    const charCount: Record<string, number> = {};
    for (const char of password) {
      charCount[char] = (charCount[char] || 0) + 1;
    }

    const maxCount = Math.max(...Object.values(charCount));
    return maxCount > password.length * 0.5;
  }

  static name(name: string, fieldName: string = "Name"): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!name) {
      errors.push(`${fieldName} is required`);
      return { isValid: false, errors, warnings };
    }

    // Length validation
    if (name.length < 2) {
      errors.push(`${fieldName} must be at least 2 characters long`);
    }

    if (name.length > 100) {
      errors.push(`${fieldName} is too long`);
    }

    // Character validation
    if (!/^[\s'A-Za-z\-]+$/.test(name)) {
      errors.push(
        `${fieldName} can only contain letters, spaces, hyphens, and apostrophes`,
      );
    }

    // Security checks
    if (/<script|javascript:|on\w+=/i.test(name)) {
      errors.push(`${fieldName} contains invalid characters`);
    }

    // Warnings
    if (name.trim() !== name) {
      warnings.push(`${fieldName} should not start or end with spaces`);
    }

    if (name.includes("  ")) {
      warnings.push(`${fieldName} should not contain consecutive spaces`);
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  static salary(salary: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!salary) {
      errors.push("Salary is required");
      return { isValid: false, errors, warnings };
    }

    // Remove common formatting characters
    const cleanSalary = salary.replaceAll(/[\s$,]/g, "");

    // Check if it's a valid number
    const salaryNumber = parseFloat(cleanSalary);
    if (isNaN(salaryNumber)) {
      errors.push('Salary must be a valid number');
      return { isValid: false, errors, warnings };
    }
    
    // Range validation
    if (salaryNumber < 0) {
      errors.push('Salary cannot be negative');
    }
    
    if (salaryNumber > 10000000) {
      errors.push('Salary seems unreasonably high');
    }
    
    if (salaryNumber < 15_000) {
      warnings.push("Salary seems very low for professional roles");
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  static phoneNumber(phone: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!phone) {
      return { isValid: true, errors, warnings }; // Phone is often optional
    }

    // Remove common formatting characters
    const cleanPhone = phone.replaceAll(/[\s()\-]/g, "");

    // Check if it contains only numbers
    if (!/^\+?\d+$/.test(cleanPhone)) {
      errors.push(
        "Phone number can only contain numbers and optional + prefix",
      );
    }

    // Length validation
    if (cleanPhone.length < 10) {
      errors.push("Phone number is too short");
    }

    if (cleanPhone.length > 15) {
      errors.push("Phone number is too long");
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  static validateField(value: string, rules: ValidationRule): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required validation
    if (rules.required && (!value || value.trim() === "")) {
      errors.push("This field is required");
    }

    if (!value) {
      return { isValid: errors.length === 0, errors, warnings };
    }

    // Length validation
    if (rules.minLength && value.length < rules.minLength) {
      errors.push(`Must be at least ${rules.minLength} characters long`);
    }

    if (rules.maxLength && value.length > rules.maxLength) {
      errors.push(`Must be no more than ${rules.maxLength} characters long`);
    }

    // Pattern validation
    if (rules.pattern && !rules.pattern.test(value)) {
      errors.push("Invalid format");
    }

    // Custom validation
    if (rules.custom) {
      const customError = rules.custom(value);
      if (customError) {
        errors.push(customError);
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }
}

// Rate Limiting Protection
export class RateLimiter {
  private static attempts = new Map<
    string,
    { count: number; resetTime: number }
  >();
  private static cleanupInterval: ReturnType<typeof setInterval> | null = null;
  private static readonly CLEANUP_INTERVAL_MS = 60_000; // Clean up every minute

  /**
   * Start periodic cleanup of expired entries to prevent memory leaks
   */
  static startCleanup(): void {
    if (this.cleanupInterval) return;
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      for (const [key, record] of this.attempts.entries()) {
        if (now > record.resetTime) {
          this.attempts.delete(key);
        }
      }
    }, this.CLEANUP_INTERVAL_MS);
  }

  /**
   * Stop cleanup interval (for testing or app shutdown)
   */
  static stopCleanup(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }

  static isAllowed(
    identifier: string,
    maxAttempts: number = 1,
    windowMs: number = 60_000 // 1 minute
  ): { allowed: boolean; resetIn: number } {
    const now = Date.now();
    const key = identifier;

    let record = this.attempts.get(key);

    if (!record || now > record.resetTime) {
      record = { count: 0, resetTime: now + windowMs };
      this.attempts.set(key, record);
    }

    // Check if already over limit before incrementing
    if (record.count >= maxAttempts) {
      const resetIn = Math.max(0, Math.ceil((record.resetTime - now) / 1000));
      return { allowed: false, resetIn };
    }

    record.count++;

    const allowed = record.count <= maxAttempts;
    const resetIn = Math.max(0, Math.ceil((record.resetTime - now) / 1000));

    return { allowed, resetIn };
  }

  static reset(identifier: string): void {
    this.attempts.delete(identifier);
  }

  /**
   * Clear all rate limit entries (for testing or admin use)
   */
  static clearAll(): void {
    this.attempts.clear();
  }
}

// Auto-start cleanup when module is loaded
if (typeof window !== "undefined") {
  RateLimiter.startCleanup();
}

// CSRF Protection
export class CSRFProtection {
  private static readonly TOKEN_LENGTH = 32;
  private static readonly STORAGE_KEY = "csrf_token";

  static generateToken(): string {
    const array = new Uint8Array(this.TOKEN_LENGTH);
    crypto.getRandomValues(array);
    return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
      "",
    );
  }

  static getToken(): string {
    let token = localStorage.getItem(this.STORAGE_KEY);
    if (!token) {
      token = this.generateToken();
      localStorage.setItem(this.STORAGE_KEY, token);
    }
    return token;
  }

  static validateToken(token: string): boolean {
    const storedToken = this.getToken();
    return token === storedToken;
  }

  static refreshToken(): string {
    const newToken = this.generateToken();
    localStorage.setItem(this.STORAGE_KEY, newToken);
    return newToken;
  }
}

// Content Security Policy Helper
export const CSPHelper = {
  generateNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode(...array));
  },
  
  validateNonce(nonce: string, expectedNonce: string): boolean {
    return nonce === expectedNonce;
  },
};

// Export all validation utilities
export const ValidationUtils = {
  sanitize: XSSProtection.sanitizeHTML.bind(XSSProtection),
  sanitizeCSS: XSSProtection.sanitizeCSS.bind(XSSProtection),
  sanitizeURL: XSSProtection.sanitizeURL.bind(XSSProtection),
  sanitizeInput: XSSProtection.sanitizeInput.bind(XSSProtection),

  validate: {
    email: Validator.email.bind(Validator),
    password: Validator.password.bind(Validator),
    name: Validator.name.bind(Validator),
    salary: Validator.salary.bind(Validator),
    phone: Validator.phoneNumber.bind(Validator),
    field: Validator.validateField.bind(Validator),
  },

  security: {
    rateLimit: RateLimiter.isAllowed.bind(RateLimiter),
    resetRateLimit: RateLimiter.reset.bind(RateLimiter),
    csrf: {
      generate: CSRFProtection.generateToken.bind(CSRFProtection),
      validate: CSRFProtection.validateToken.bind(CSRFProtection),
      refresh: CSRFProtection.refreshToken.bind(CSRFProtection),
    },
    csp: {
      generateNonce: CSPHelper.generateNonce.bind(CSPHelper),
      validateNonce: CSPHelper.validateNonce.bind(CSPHelper),
    },
  },
};
