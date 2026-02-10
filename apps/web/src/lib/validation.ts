/**
 * Comprehensive Validation Library
 * Microsoft-level implementation with security-first approach
 */

// XSS Protection Utilities
export class XSSProtection {
  private static readonly HTML_ENTITIES = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;',
  };

  private static readonly CSS_KEYWORDS = [
    'javascript:', 'data:', 'vbscript:', 'onload=', 'onerror=', 'onclick=',
    'onmouseover=', 'onfocus=', 'onblur=', 'onchange=', 'onsubmit=',
    'expression(', 'import(', 'url(', '@import', 'behavior:'
  ];

  static sanitizeHTML(input: string): string {
    if (typeof input !== 'string') return '';
    
    return input
      .replace(/[&<>"'`=/]/g, (match) => this.HTML_ENTITIES[match as keyof typeof XSSProtection.HTML_ENTITIES] || match)
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '')
      .replace(/<object[^>]*>.*?<\/object>/gi, '')
      .replace(/<embed[^>]*>/gi, '')
      .replace(/javascript:/gi, '')
      .replace(/on\w+\s*=/gi, '');
  }

  static sanitizeCSS(input: string): string {
    if (typeof input !== 'string') return '';
    
    let sanitized = input.toLowerCase();
    
    // Remove dangerous CSS keywords
    this.CSS_KEYWORDS.forEach(keyword => {
      sanitized = sanitized.replace(new RegExp(keyword, 'gi'), '');
    });
    
    // Remove url() functions that could contain javascript
    sanitized = sanitized.replace(/url\s*\(\s*['"]*javascript:[^'"]*['"]*\s*\)/gi, '');
    
    return sanitized;
  }

  static sanitizeURL(url: string): string {
    if (typeof url !== 'string') return '';
    
    try {
      // Basic URL validation
      const parsed = new URL(url);
      
      // Only allow http, https, and relative protocols
      if (!['http:', 'https:', ''].includes(parsed.protocol)) {
        return '';
      }
      
      // Remove dangerous characters
      return parsed.toString().replace(/[<>"'`]/g, '');
    } catch {
      // If URL parsing fails, do basic sanitization
      return url.replace(/[<>"'`]/g, '').substring(0, 2048);
    }
  }

  static sanitizeInput(input: string, maxLength: number = 1000): string {
    if (typeof input !== 'string') return '';
    
    return input
      .substring(0, maxLength)
      .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
      .replace(/[<>]/g, '') // Remove HTML brackets
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
      errors.push('Email is required');
      return { isValid: false, errors, warnings };
    }
    
    // Basic email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      errors.push('Invalid email format');
    }
    
    // Length validation
    if (email.length > 254) {
      errors.push('Email address is too long');
    }
    
    // Check for suspicious patterns
    if (email.includes('+') && email.split('+').length > 2) {
      warnings.push('Multiple plus signs detected');
    }
    
    // Domain validation
    const domain = email.split('@')[1];
    if (domain && domain.length > 63) {
      errors.push('Domain name is too long');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  static password(password: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!password) {
      errors.push('Password is required');
      return { isValid: false, errors, warnings };
    }
    
    // Length requirements
    if (password.length < 10) {
      errors.push('Password must be at least 10 characters long');
    }
    
    if (password.length > 128) {
      errors.push('Password is too long');
    }
    
    // Character requirements
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain lowercase letters');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain uppercase letters');
    }
    
    if (!/\d/.test(password)) {
      errors.push('Password must contain numbers');
    }
    
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password must contain special characters');
    }
    
    // Security warnings
    if (password.toLowerCase().includes('password')) {
      warnings.push('Password should not contain the word "password"');
    }
    
    if (password.toLowerCase().includes('123456')) {
      warnings.push('Avoid using sequential numbers');
    }
    
    // Check for common patterns
    const commonPatterns = [
      /^123456/, /^password/i, /^qwerty/i, /^admin/i,
      /123456$/, /password$/i, /qwerty$/i, /admin$/
    ];
    
    if (commonPatterns.some(pattern => pattern.test(password))) {
      warnings.push('Password is too common');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  static name(name: string, fieldName: string = 'Name'): ValidationResult {
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
    if (!/^[a-zA-Z\s\-']+$/.test(name)) {
      errors.push(`${fieldName} can only contain letters, spaces, hyphens, and apostrophes`);
    }
    
    // Security checks
    if (/<script|javascript:|on\w+=/i.test(name)) {
      errors.push(`${fieldName} contains invalid characters`);
    }
    
    // Warnings
    if (name.trim() !== name) {
      warnings.push(`${fieldName} should not start or end with spaces`);
    }
    
    if (name.includes('  ')) {
      warnings.push(`${fieldName} should not contain consecutive spaces`);
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  static salary(salary: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!salary) {
      errors.push('Salary is required');
      return { isValid: false, errors, warnings };
    }
    
    // Remove common formatting characters
    const cleanSalary = salary.replace(/[$,\s]/g, '');
    
    // Check if it's a valid number
    const salaryNum = parseFloat(cleanSalary);
    if (isNaN(salaryNum)) {
      errors.push('Salary must be a valid number');
      return { isValid: false, errors, warnings };
    }
    
    // Range validation
    if (salaryNum < 0) {
      errors.push('Salary cannot be negative');
    }
    
    if (salaryNum > 10000000) {
      errors.push('Salary seems unreasonably high');
    }
    
    if (salaryNum < 15000) {
      warnings.push('Salary seems very low for professional roles');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  static phoneNumber(phone: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (!phone) {
      return { isValid: true, errors, warnings }; // Phone is often optional
    }
    
    // Remove common formatting characters
    const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
    
    // Check if it contains only numbers
    if (!/^\+?\d+$/.test(cleanPhone)) {
      errors.push('Phone number can only contain numbers and optional + prefix');
    }
    
    // Length validation
    if (cleanPhone.length < 10) {
      errors.push('Phone number is too short');
    }
    
    if (cleanPhone.length > 15) {
      errors.push('Phone number is too long');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  static validateField(value: string, rules: ValidationRule): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    // Required validation
    if (rules.required && (!value || value.trim() === '')) {
      errors.push('This field is required');
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
      errors.push('Invalid format');
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
      warnings
    };
  }
}

// Rate Limiting Protection
export class RateLimiter {
  private static attempts = new Map<string, { count: number; resetTime: number }>();
  
  static isAllowed(
    identifier: string,
    maxAttempts: number = 1,
    windowMs: number = 60000 // 1 minute
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
}

// CSRF Protection
export class CSRFProtection {
  private static readonly TOKEN_LENGTH = 32;
  private static readonly STORAGE_KEY = 'csrf_token';
  
  static generateToken(): string {
    const array = new Uint8Array(this.TOKEN_LENGTH);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
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
export class CSPHelper {
  static generateNonce(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode(...array));
  }
  
  static validateNonce(nonce: string, expectedNonce: string): boolean {
    return nonce === expectedNonce;
  }
}

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
