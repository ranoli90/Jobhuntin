/**
 * Part 1: Environment-specific frontend configuration.
 *
 * Reads EXPO_PUBLIC_APP_ENV to select the correct API base URL.
 * Defaults to local dev if unset.
 */

type AppEnv = "local" | "staging" | "prod";

const APP_ENV: AppEnv =
  (process.env.EXPO_PUBLIC_APP_ENV as AppEnv) ?? "local";

const API_BASE_URLS: Record<AppEnv, string> = {
  local: "http://localhost:8000",
  staging: process.env.EXPO_PUBLIC_API_URL_STAGING ?? "https://api-staging.sorce.app",
  prod: process.env.EXPO_PUBLIC_API_URL_PROD ?? "https://api.sorce.app",
};

export const API_BASE_URL: string = API_BASE_URLS[APP_ENV];
export { APP_ENV };
