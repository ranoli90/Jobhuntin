/**
 * Development-only logging utility
 * All console logs are stripped in production builds
 */

const isDev = import.meta.env.DEV;

export const logger = {
  log: (...args: unknown[]) => {
    if (isDev) {
      console.log(...args);
    }
  },
  
  warn: (...args: unknown[]) => {
    if (isDev) {
      console.warn(...args);
    }
  },
  
  error: (...args: unknown[]) => {
    // Always log errors, but could send to error reporting service in production
    console.error(...args);
  },
  
  debug: (...args: unknown[]) => {
    if (isDev) {
      console.debug(...args);
    }
  },
  
  info: (...args: unknown[]) => {
    if (isDev) {
      console.info(...args);
    }
  },
  
  group: (label: string) => {
    if (isDev) {
      console.group(label);
    }
  },
  
  groupEnd: () => {
    if (isDev) {
      console.groupEnd();
    }
  },
  
  time: (label: string) => {
    if (isDev) {
      console.time(label);
    }
  },
  
  timeEnd: (label: string) => {
    if (isDev) {
      console.timeEnd(label);
    }
  },
};

/**
 * Telemetry logging for A/B tests and analytics
 * Only logs in development mode, but could be sent to analytics in production
 */
export const telemetry = {
  track: (event: string, data?: Record<string, unknown>) => {
    if (isDev) {
      console.log(`[Telemetry] ${event}`, data);
    }
    // In production, this would send to an analytics service
  },
  
  identify: (userId: string, traits?: Record<string, unknown>) => {
    if (isDev) {
      console.log(`[Telemetry] Identify: ${userId}`, traits);
    }
  },
};
