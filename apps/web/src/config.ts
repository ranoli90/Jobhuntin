const appBaseUrl =
  import.meta.env.VITE_APP_BASE_URL ?? (typeof window !== "undefined" ? window.location.origin : "");

export const config = {
  appBaseUrl,
  urls: {
    homepage: appBaseUrl,
    og: appBaseUrl,
  },
  analytics: {
    gaId: import.meta.env.VITE_GA_ID,
  },
};

export function validateConfig(): string[] {
  const errors: string[] = [];
  if (import.meta.env.PROD && !appBaseUrl) {
    errors.push("VITE_APP_BASE_URL not set in production");
  }
  return errors;
}
