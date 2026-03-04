import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Sanitize HTML content to prevent XSS attacks.
 * NOTE: This is a basic sanitization. For production use, consider DOMPurify.
 * 
 * Removes script tags, event handlers, and dangerous URLs while preserving safe HTML.
 */
export function sanitizeHtml(html: string): string {
  if (!html) return "";
  
  return html
    // Remove script tags and their content
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
    // Remove event handlers (onclick, onload, onerror, etc.)
    .replace(/\s*on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]*)/gi, "")
    // Remove javascript: URLs (case insensitive, with variations)
    .replace(/javascript:/gi, "")
    // Remove vbscript: URLs
    .replace(/vbscript:/gi, "")
    // Remove data:text/html URLs (base64 encoded XSS)
    .replace(/data:text\/html[^;]*;base64,[^"'>\s]*/gi, "")
    // Remove iframe tags
    .replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, "")
    // Remove frame tags
    .replace(/<frame[^>]*>[\s\S]*?<\/frame>/gi, "")
    // Remove object/embed tags
    .replace(/<(object|embed)[^>]*>[\s\S]*?<\/\1>/gi, "")
    // Remove style tags (could contain XSS)
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
    // Remove SVG on* handlers
    .replace(/<svg[^>]*on\w+\s*=/gi, "<svg")
    // Remove meta refresh redirects
    .replace(/<meta[^>]*http-equiv=["']?refresh["']?[^>]*>/gi, "")
    // Remove base64 encoded scripts in images
    .replace(/<img[^>]*src=["']?javascript:/gi, "<img src=\"#\"");
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
