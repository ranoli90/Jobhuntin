import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Sanitize HTML content to prevent XSS attacks.
 * Removes script tags and event handlers while preserving safe HTML.
 */
export function sanitizeHtml(html: string): string {
  if (!html) return "";
  
  return html
    // Remove script tags and their content
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
    // Remove event handlers
    .replace(/\s*on\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]*)/gi, "")
    // Remove javascript: URLs
    .replace(/javascript:/gi, "")
    // Remove data URLs that could execute code
    .replace(/data:text\/html[^;]*;base64,[^"'>\s]*/gi, "")
    // Remove iframe tags
    .replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, "")
    // Remove object/embed tags
    .replace(/<(object|embed)[^>]*>[\s\S]*?<\/\1>/gi, "")
    // Remove style tags (could contain XSS)
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "");
}

/**
 * Escape HTML special characters to prevent XSS.
 * Use this when rendering plain text that might contain HTML.
 */
export function escapeHtml(text: string): string {
  if (!text) return "";
  
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
