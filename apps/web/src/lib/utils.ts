import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import DOMPurify from "dompurify";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Sanitize HTML content to prevent XSS attacks using DOMPurify.
 * This is production-grade sanitization that removes all dangerous content
 * while preserving safe HTML tags and attributes.
 */
export function sanitizeHtml(html: string): string {
  if (!html) return "";

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del',
      'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
      'span', 'div', 'img'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'target', 'rel',
      'src', 'alt', 'width', 'height',
      'class', 'id'
    ],
    ALLOW_DATA_ATTR: false,
    SANITIZE_DOM: true,
    // Force all links to open in new tab with no opener
    FORBID_ATTR: ['onerror', 'onload', 'onclick'],
    // Only allow safe URI schemes (blocks javascript:, vbscript:, data: etc.)
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i,
  });
}

/**
 * Escape HTML special characters to prevent XSS.
 * Use this when rendering plain text that might contain HTML.
 * Works in both browser and Node.js environments.
 */
export function escapeHtml(text: string): string {
  if (!text) return "";

  const htmlEscapes: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };

  return text.replace(/[&<>"']/g, (char) => htmlEscapes[char] || char);
}

/** Check if error is QuotaExceededError (localStorage full) */
function isQuotaExceeded(e: unknown): boolean {
  if (e instanceof DOMException) return e.name === "QuotaExceededError" || e.code === 22;
  return false;
}

/**
 * Safely set item in localStorage. On QuotaExceededError, tries sessionStorage fallback.
 * Per coding standards: handle QuotaExceededError; fallback to sessionStorage.
 * @returns true if stored successfully, false otherwise
 */
export function safeSetStorage(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (e) {
    if (isQuotaExceeded(e)) {
      try {
        localStorage.removeItem(key);
        localStorage.setItem(key, value);
        return true;
      } catch {
        try {
          sessionStorage.setItem(key, value);
          return true;
        } catch {
          if (import.meta.env.DEV) console.warn("[safeStorage] QuotaExceeded recovery failed");
          return false;
        }
      }
    }
    throw e;
  }
}

/**
 * Safely get item - tries localStorage first, then sessionStorage (for fallback case).
 */
export function safeGetStorage(key: string): string | null {
  try {
    return localStorage.getItem(key) ?? sessionStorage.getItem(key);
  } catch {
    return null;
  }
}
