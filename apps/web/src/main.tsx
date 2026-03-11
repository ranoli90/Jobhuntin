import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { HelmetProvider } from "react-helmet-async";
import * as Sentry from "@sentry/react";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AppProvider } from "./context/AppContext";
import { AuthProvider } from "./context/AuthContext";
import { validateConfig } from "./config";
import "./index.css";

// Initialize Sentry for frontend error tracking (H4: Frontend Error Tracking)
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
if (sentryDsn) {
  try {
    Sentry.init({
      dsn: sentryDsn,
      environment: import.meta.env.MODE || "production",
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      // Performance Monitoring
      tracesSampleRate: import.meta.env.PROD ? 0.1 : 1, // 10% in prod, 100% in dev
      // Session Replay
      replaysSessionSampleRate: import.meta.env.PROD ? 0.1 : 1, // 10% in prod
      replaysOnErrorSampleRate: 1, // 100% of sessions with errors
      // Filter out sensitive data
      beforeSend(
        event: Parameters<
          NonNullable<Parameters<typeof Sentry.init>[0]["beforeSend"]>
        >[0],
        _hint: Parameters<
          NonNullable<Parameters<typeof Sentry.init>[0]["beforeSend"]>
        >[1],
      ) {
        // Remove PII from error messages
        if (event.request?.url) {
          // Remove query params that might contain sensitive data
          try {
            const url = new URL(event.request.url);
            url.search = "";
            event.request.url = url.toString();
          } catch {
            // Ignore URL parsing errors
          }
        }
        // Remove user email from contexts if present
        if (event.user?.email) {
          event.user.email = "[REDACTED]";
        }
        return event;
      },
    });
    if (import.meta.env.DEV) {
      console.log("[Sentry] Initialized for error tracking (DEV mode)");
    }
  } catch (error) {
    console.error("[Sentry] Failed to initialize:", error);
  }
}
// Don't log Sentry warning in dev mode - it's expected when DSN is not set

// Service Worker Registration
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        console.log("[SW] Service Worker registered:", registration);

        // Check for updates
        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "installed" &&
                navigator.serviceWorker.controller && // New version available, show update notification
                window.confirm(
                  "A new version of JobHuntin is available. Would you like to update?",
                )
              ) {
                newWorker.postMessage({ type: "SKIP_WAITING" });
                window.location.reload();
              }
            });
          }
        });
      })
      .catch((error) => {
        console.error("[SW] Service Worker registration failed:", error);
      });
  });
}

const configErrors = validateConfig();
if (configErrors.length > 0) {
  if (import.meta.env.PROD) {
    // Block render in production when config is invalid
    const root = document.querySelector("#root");
    if (root) {
      root.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:2rem;font-family:system-ui,sans-serif;text-align:center;">
          <h1 style="color:#dc2626;font-size:1.5rem;margin-bottom:1rem;">Configuration Error</h1>
          <p style="color:#6b7280;margin-bottom:1rem;">The application cannot start due to configuration issues:</p>
          <ul style="list-style:none;padding:0;color:#374151;">
            ${configErrors.map((e) => `<li style="margin:0.5rem 0;">• ${e}</li>`).join("")}
          </ul>
          <p style="color:#9ca3af;font-size:0.875rem;margin-top:1rem;">Please contact support or check your deployment configuration.</p>
        </div>
      `;
    }
    throw new Error(`[Config] Validation failed: ${configErrors.join("; ")}`);
  }
  console.warn("[Config] Validation issues:", configErrors);
}

const queryClient = new QueryClient();

ReactDOM.createRoot(document.querySelector("#root")!).render(
  <React.StrictMode>
    <HelmetProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <AppProvider>
              <AuthProvider>
                <App />
              </AuthProvider>
            </AppProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </ErrorBoundary>
    </HelmetProvider>
  </React.StrictMode>,
);
