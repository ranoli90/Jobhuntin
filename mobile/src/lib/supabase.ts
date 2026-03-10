/**
 * Authentication utilities for the mobile app using the Render API backend.
 *
 * Uses direct API calls to the Render backend (no Supabase).
 * All auth tokens are stored securely using expo-secure-store.
 *
 * NOTE: reCAPTCHA Enterprise Mobile SDK integration required for production.
 * See: https://cloud.google.com/recaptcha-enterprise/docs/instrument-mobile-apps
 */

import * as SecureStore from 'expo-secure-store';
import { API_BASE_URL } from './config';

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_ID_KEY = 'user_id';

export interface Session {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
  };
}

/**
 * Get the current auth token from secure storage.
 */
export async function getAuthToken(): Promise<string | null> {
  return SecureStore.getItemAsync(AUTH_TOKEN_KEY);
}

/**
 * Get the current session including user info.
 */
export async function getSession(): Promise<{ session: Session | null }> {
  const token = await getAuthToken();
  const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  const userId = await SecureStore.getItemAsync(USER_ID_KEY);
  
  if (!token || !userId) {
    return { session: null };
  }
  
  // Get user info from API
  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      return { session: null };
    }
    
    const user = await response.json();
    
    return {
      session: {
        access_token: token,
        refresh_token: refreshToken || '',
        user: {
          id: userId,
          email: user.email || '',
        },
      },
    };
  } catch {
    return { session: null };
  }
}

/**
 * Sign in with magic link.
 * 
 * TODO: Implement reCAPTCHA Enterprise Mobile SDK before production deployment.
 * The backend now requires CAPTCHA in production. Without it, this will fail.
 * 
 * Installation:
 *   npm install @google-cloud/recaptcha-enterprise-react-native
 * 
 * Implementation:
 *   1. Initialize reCAPTCHA client with your site key
 *   2. Execute reCAPTCHA before calling this function
 *   3. Pass the obtained token as captchaToken
 */
export async function signInWithMagicLink(
  email: string,
  captchaToken?: string
): Promise<{ error: Error | null; captchaRequired?: boolean }> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/magic-link`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        email,
        // Pass CAPTCHA token if provided
        captcha_token: captchaToken,
      }),
    });
    
    if (response.status === 400) {
      const errorData = await response.json().catch(() => ({}));
      // Check if CAPTCHA is required
      if (errorData.detail?.includes('CAPTCHA') || errorData.detail?.includes('captcha')) {
        return { error: new Error('CAPTCHA verification required'), captchaRequired: true };
      }
    }
    
    if (!response.ok) {
      const error = await response.text();
      return { error: new Error(error) };
    }
    
    return { error: null };
  } catch (error) {
    return { error: error as Error };
  }
}

/**
 * Request magic link with CAPTCHA token.
 * This is the production-ready version that includes bot protection.
 */
export async function signInWithMagicLinkAndCaptcha(
  email: string,
  captchaToken: string
): Promise<{ error: Error | null }> {
  return signInWithMagicLink(email, captchaToken);
}

/**
 * Sign in with email and password (for testing).
 */
export async function signInWithPassword(email: string, password: string): Promise<{ data: { session: Session } | null; error: Error | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      return { data: null, error: new Error(error) };
    }
    
    const data = await response.json();
    
    // Store tokens securely
    await SecureStore.setItemAsync(AUTH_TOKEN_KEY, data.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, data.refresh_token);
    await SecureStore.setItemAsync(USER_ID_KEY, data.user.id);
    
    return {
      data: {
        session: {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          user: {
            id: data.user.id,
            email: data.user.email,
          },
        },
      },
      error: null,
    };
  } catch (error) {
    return { data: null, error: error as Error };
  }
}

/**
 * Sign out the current user.
 */
export async function signOut(): Promise<{ error: Error | null }> {
  try {
    const token = await getAuthToken();
    
    if (token) {
      await fetch(`${API_BASE_URL}/auth/signout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
    
    // Clear stored tokens
    await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_ID_KEY);
    
    return { error: null };
  } catch (error) {
    return { error: error as Error };
  }
}

/**
 * Refresh the current session.
 */
export async function refreshSession(refreshToken: string): Promise<{ data: { session: Session } | null; error: Error | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      return { data: null, error: new Error(error) };
    }
    
    const data = await response.json();
    
    // Store new tokens
    await SecureStore.setItemAsync(AUTH_TOKEN_KEY, data.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, data.refresh_token);
    
    return {
      data: {
        session: {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          user: {
            id: data.user?.id || '',
            email: data.user?.email || '',
          },
        },
      },
      error: null,
    };
  } catch (error) {
    return { data: null, error: error as Error };
  }
}

/**
 * Handle magic link deep link.
 * 
 * TODO: Implement deep link handling for magic links.
 * Currently, magic links open in browser. To open in app:
 * 
 * 1. Configure iOS Universal Links: https://jobhuntin.com/.well-known/apple-app-site-association
 * 2. Configure Android App Links: https://jobhuntin.com/.well-known/assetlinks.json
 * 3. Use expo-linking to handle incoming URLs
 * 
 * Example implementation:
 * ```
 * import * as Linking from 'expo-linking';
 * 
 * Linking.addEventListener('url', ({ url }) => {
 *   if (url.includes('/auth/verify-magic')) {
 *     const token = new URL(url).searchParams.get('token');
 *     // Exchange token for session via API
 *   }
 * });
 * ```
 */
export function handleMagicLinkDeepLink(url: string): { token: string | null; returnTo: string | null } {
  try {
    const parsedUrl = new URL(url);
    const token = parsedUrl.searchParams.get('token');
    const returnTo = parsedUrl.searchParams.get('returnTo');
    return { token, returnTo };
  } catch {
    return { token: null, returnTo: null };
  }
}

/**
 * Get current user from session (for compatibility with code expecting supabase.auth.getUser).
 */
export async function getUser(): Promise<{ data: { user: { id: string; email: string } | null }; error: null }> {
  const result = await getSession();
  const session = result.session;
  if (!session) {
    return { data: { user: null }, error: null };
  }
  return {
    data: {
      user: {
        id: session.user.id,
        email: session.user.email,
      },
    },
    error: null,
  };
}

/** No-op channel for compatibility - Render backend has no realtime; use refreshApplication/polling. */
function noopChannel() {
  return {
    on: () => ({ subscribe: () => ({}) }),
  };
}

/** Auth + compatibility shims. Render backend (no Supabase). Kept as 'supabase' for minimal import changes. */
export const supabase = {
  auth: {
    getSession,
    getUser,
    signInWithMagicLink,
    signInWithMagicLinkAndCaptcha,
    signInWithPassword,
    signOut,
    refreshSession,
    handleMagicLinkDeepLink,
  },
  channel: noopChannel,
  removeChannel: () => {},
};

export default supabase;
