/**
 * Development-only logging utility
 * All console logs are stripped in production builds
 */

const isDevelopment = import.meta.env.DEV;

export const logger = {
  log: (...arguments_: unknown[]) => {
    if (isDevelopment) {
      console.log(...arguments_);
    }
  },

  warn: (...arguments_: unknown[]) => {
    if (isDevelopment) {
      console.warn(...arguments_);
    }
  },

  error: (...arguments_: unknown[]) => {
    // Always log errors, but could send to error reporting service in production
    console.error(...arguments_);
  },

  debug: (...arguments_: unknown[]) => {
    if (isDevelopment) {
      console.debug(...arguments_);
    }
  },

  info: (...arguments_: unknown[]) => {
    if (isDevelopment) {
      console.info(...arguments_);
    }
  },

  group: (label: string) => {
    if (isDevelopment) {
      console.group(label);
    }
  },

  groupEnd: () => {
    if (isDevelopment) {
      console.groupEnd();
    }
  },

  time: (label: string) => {
    if (isDevelopment) {
      console.time(label);
    }
  },

  timeEnd: (label: string) => {
    if (isDevelopment) {
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
    if (isDevelopment) {
      console.log("[Telemetry]", event, data);
    }
    // In production, this would send to an analytics service
  },

  identify: (userId: string, traits?: Record<string, unknown>) => {
    if (isDevelopment) {
      console.log("[Telemetry] Identify:", userId, traits);
    }
  },
};
