/**
 * Authentication utilities for the mobile app using the Render API backend.
 * 
 * This replaces Supabase Auth with direct API calls to the Render backend.
 * All auth tokens are stored securely using expo-secure-store.
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
 */
export async function signInWithMagicLink(email: string): Promise<{ error: Error | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/magic-link`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
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

// Mock supabase object for compatibility with existing code
export const supabase = {
  auth: {
    getSession,
    signInWithMagicLink,
    signInWithPassword,
    signOut,
    refreshSession,
  },
};

export default supabase;
