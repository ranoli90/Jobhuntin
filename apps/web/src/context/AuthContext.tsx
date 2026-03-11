import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import { apiGet, getApiBase } from "../lib/api";
import { pushToast } from "../lib/toast";

/* eslint-disable @typescript-eslint/no-explicit-any */

// Session warning threshold (5 minutes before expiry)
const SESSION_WARNING_THRESHOLD_MS = 5 * 60 * 1000;

// Session TTL must match backend SESSION_TTL_SECONDS (7 days)
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export interface User {
  id: string;
  email: string;
  has_completed_onboarding: boolean;
  resume_url?: string;
  preferences?: Record<string, any>;
  contact?: Record<string, any>;
  headline?: string;
  bio?: string;
  role?: "user" | "admin" | "superadmin";
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithMagicLink: (
    email: string,
    returnTo?: string,
  ) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signInWithMagicLink: async () => ({ error: null }),
  signOut: async () => {},
  updateUser: () => {},
  refreshUser: async () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const sessionExpiryReference = useRef<number | null>(null);
  const warningShownReference = useRef(false);
  const verifyRedirectingReference = useRef(false);

  // Helper to fetch user profile
  const fetchUser = useCallback(async (isInitialLoad = false) => {
    try {
      let profile: User;

      if (isInitialLoad) {
        // On initial load, use a direct fetch that does NOT dispatch auth:unauthorized
        // on 401. apiGet() dispatches the event BEFORE the error reaches this catch block,
        // causing an unwanted redirect + "session expired" toast on first visit.
        try {
          const base = getApiBase();
          const resp = await fetch(`${base.replace(/\/$/, "")}/me/profile`, {
            method: "GET",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          });
          if (!resp.ok) {
            // Silently handle 401 on initial load — user simply isn't logged in yet
            // 401 is expected for unauthenticated users, not an error condition
            // Note: Browser will still log 401 as network error, but we handle it gracefully
            if (resp.status === 401) {
              setUser(null);
              sessionExpiryReference.current = null;
              return;
            }
            // For other errors, log but don't throw
            if (import.meta.env.DEV) {
              console.log("[AUTH] Profile check returned", resp.status);
            }
            setUser(null);
            sessionExpiryReference.current = null;
            return;
          }
          profile = await resp.json();
        } catch (error) {
          // Network errors (including 401) are expected for unauthenticated users
          // Only log unexpected errors
          if (
            import.meta.env.DEV &&
            error instanceof Error &&
            !error.message.includes("401") &&
            !error.message.includes("Failed to fetch")
          ) {
            console.error("[AUTH] Profile fetch failed:", error);
          }
          setUser(null);
          return;
        }
      } else {
        // Subsequent calls (e.g. refreshUser) — use apiGet which has retry + error handling
        profile = await apiGet<User>("me/profile");
      }

      setUser(profile);
      if (import.meta.env.DEV)
        console.log("[AUTH] User profile loaded:", {
          id: profile.id,
          email: profile.email,
          has_completed_onboarding: profile.has_completed_onboarding,
        });

      // Sync extension session state
      localStorage.setItem(
        "jobhuntin-session",
        JSON.stringify({
          logged_in: true,
          ts: Date.now(),
        }),
      );

      // Session expiry matches the 7-day session JWT issued by backend
      sessionExpiryReference.current = Date.now() + SESSION_TTL_MS;
      warningShownReference.current = false;
    } catch (error) {
      console.error("[AUTH] Failed to fetch user profile:", error);
      setUser(null);
      sessionExpiryReference.current = null;

      const error_ = error as Error & { status?: number };
      const is401 = error_?.status === 401;
      const isLoginPage = window.location.pathname === "/login";
      if (!isInitialLoad && !isLoginPage && !is401) {
        const message =
          error_ instanceof Error ? error_.message : "Your session has expired";
        pushToast({
          title: "Session expired",
          description: `${message}. Please sign in again.`,
          tone: "error",
        });
        const returnTo = window.location.pathname + window.location.search;
        sessionStorage.setItem("returnTo", returnTo);
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
      }
    }
  }, []);

  const ensureCsrfCookie = useCallback(async () => {
    try {
      const base = getApiBase();
      if (!base) return;
      await fetch(`${base.replace(/\/$/, "")}/csrf/prepare`, {
        credentials: "include",
      });
    } catch (error) {
      console.warn("CSRF cookie preflight failed", error);
    }
  }, []);

  // Session expiration warning
  useEffect(() => {
    const checkSessionExpiry = () => {
      if (!sessionExpiryReference.current || warningShownReference.current)
        return;

      const timeUntilExpiry = sessionExpiryReference.current - Date.now();

      if (timeUntilExpiry <= 0) {
        warningShownReference.current = true;
        pushToast({
          title: "Session expired",
          description: "Your session has expired. Please sign in again.",
          tone: "error",
        });
      } else if (timeUntilExpiry <= SESSION_WARNING_THRESHOLD_MS) {
        warningShownReference.current = true;
        const minutesLeft = Math.ceil(timeUntilExpiry / 60_000);
        pushToast({
          title: "Session expiring soon",
          description: `Your session will expire in ${minutesLeft} minute${minutesLeft > 1 ? "s" : ""}. Save any work and sign in again to continue.`,
          tone: "warning",
        });
      }
    };

    const interval = setInterval(checkSessionExpiry, 60_000);
    const handleActivity = () => checkSessionExpiry();
    window.addEventListener("click", handleActivity);
    window.addEventListener("keypress", handleActivity);

    return () => {
      clearInterval(interval);
      window.removeEventListener("click", handleActivity);
      window.removeEventListener("keypress", handleActivity);
    };
  }, []);

  // Initialize auth
  useEffect(() => {
    const initAuth = async () => {
      try {
        console.log("[AUTH] Starting initAuth...");

        // 1. Check for token in URL (legacy magic link flow — used when API_PUBLIC_URL is not set)
        //    When API_PUBLIC_URL IS set, the backend redirects the user BEFORE they hit the
        //    frontend, so the token will NOT appear in the URL. The cookie is set by the
        //    backend's /auth/verify-magic redirect response.
        const parameters = new URLSearchParams(window.location.search);
        const tokenFromUrl = parameters.get("token");

        if (tokenFromUrl) {
          if (verifyRedirectingReference.current) {
            if (import.meta.env.DEV)
              console.log(
                "[AUTH] Verify redirect already in progress, skipping duplicate",
              );
            return;
          }
          verifyRedirectingReference.current = true;

          if (import.meta.env.DEV)
            console.log(
              "[AUTH] Token found in URL, redirecting to backend verify...",
            );

          const base = getApiBase();
          const returnTo =
            parameters.get("returnTo") ||
            sessionStorage.getItem("returnTo") ||
            "/app/dashboard";
          if (base) {
            const verifyUrl = `${base.replace(/\/$/, "")}/auth/verify-magic?token=${encodeURIComponent(tokenFromUrl)}&returnTo=${encodeURIComponent(returnTo)}`;
            if (import.meta.env.DEV)
              console.log("[AUTH] Navigating to verify-magic:", verifyUrl);
            window.location.href = verifyUrl;
            return;
          }
        }

        // 2. Check for existing session via httpOnly cookie
        // Note: httpOnly cookies aren't accessible via JavaScript, so we need to make the request
        // The 401 response is expected for unauthenticated users and is handled gracefully
        if (import.meta.env.DEV)
          console.log("[AUTH] Checking for existing session...");
        await ensureCsrfCookie();
        await fetchUser(true);
        if (import.meta.env.DEV)
          console.log("[AUTH] Auth initialization complete");
      } catch (error) {
        console.error("[AUTH] Auth initialization failed:", error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    const handleUnauthorized = (event: Event) => {
      if (import.meta.env.DEV)
        console.log("[AUTH] Unauthorized event received, clearing session");
      const detail = (event as CustomEvent<{ returnTo?: string }>).detail;
      setUser(null);
      sessionExpiryReference.current = null;
      sessionStorage.setItem("session_expired", "true");
      if (window.location.pathname === "/login") return;
      const returnTo =
        detail?.returnTo ??
        encodeURIComponent(window.location.pathname + window.location.search);
      // A6/A4: Flush onboarding state before redirect when on onboarding
      if (window.location.pathname.startsWith("/app/onboarding")) {
        import("../hooks/useOnboarding")
          .then(({ flushOnboardingBeforeRedirect }) => {
            flushOnboardingBeforeRedirect?.();
            import("../lib/toast")
              .then(({ pushToast }) => {
                pushToast({
                  title: "Session expired",
                  description:
                    "Your progress has been saved. Sign in again to continue.",
                  tone: "info",
                });
              })
              .catch(() => {});
            setTimeout(() => {
              window.location.href = `/login?returnTo=${returnTo}`;
            }, 100);
          })
          .catch(() => {
            window.location.href = `/login?returnTo=${returnTo}`;
          });
        return;
      }
      window.location.href = `/login?returnTo=${returnTo}`;
    };

    window.addEventListener(
      "auth:unauthorized",
      handleUnauthorized as EventListener,
    );
    initAuth();

    return () => {
      window.removeEventListener(
        "auth:unauthorized",
        handleUnauthorized as EventListener,
      );
    };
  }, [ensureCsrfCookie, fetchUser]);

  const signInWithMagicLink = async (
    email: string,
    returnTo = "/app/onboarding",
  ) => {
    try {
      const { magicLinkService } = await import("../services/magicLinkService");
      const res = await magicLinkService.sendMagicLink(email, returnTo);
      if (!res.success) {
        return { error: new Error(res.error || "Failed to send magic link") };
      }
      return { error: null };
    } catch (error) {
      return { error: error as Error };
    }
  };

  const signOut = async () => {
    setUser(null);
    sessionExpiryReference.current = null;
    localStorage.removeItem("jobhuntin-session");
    // Redirect to API logout to clear httpOnly cookie server-side, then to /login
    const base = getApiBase();
    window.location.href = base
      ? `${base.replace(/\/$/, "")}/auth/logout`
      : "/login";
  };

  const updateUser = (updates: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updates });
    }
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithMagicLink,
        signOut,
        updateUser,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => useContext(AuthContext);
