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
