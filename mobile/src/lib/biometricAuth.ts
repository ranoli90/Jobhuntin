/**
 * Biometric authentication service for mobile app.
 *
 * Provides:
 * - Face ID / Touch ID authentication on iOS
 * - Fingerprint authentication on Android
 * - Secure credential storage
 * - Biometric prompt management
 */

import * as LocalAuthentication from 'expo-local-authentication';
import { Platform } from 'react-native';
import { secureGetItemAsync, secureSetItemAsync, secureDeleteItemAsync } from './secureStorage';
import { supabase } from './supabase';

// Storage keys
const BIOMETRIC_ENABLED_KEY = 'biometric_auth_enabled';
const BIOMETRIC_TOKEN_KEY = 'biometric_refresh_token';

export interface BiometricCapabilities {
  isAvailable: boolean;
  biometryType: BiometryType | null;
  hasEnrolledCredentials: boolean;
}

export enum BiometryType {
  FINGERPRINT = 'fingerprint',
  FACE_ID = 'faceId',
  FACE = 'face',
  IRIS = 'iris',
  NONE = 'none',
}

export interface BiometricAuthResult {
  success: boolean;
  error?: string;
}

/**
 * Check device biometric capabilities.
 */
export async function getBiometricCapabilities(): Promise<BiometricCapabilities> {
  try {
    // Check if device supports biometrics
    const compatible = await LocalAuthentication.hasHardwareAsync();
    
    if (!compatible) {
      return {
        isAvailable: false,
        biometryType: null,
        hasEnrolledCredentials: false,
      };
    }

    // Check if user has enrolled biometrics
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    
    // Get biometry type
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    let biometryType: BiometryType | null = null;
    
    if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
      biometryType = Platform.OS === 'ios' ? BiometryType.FACE_ID : BiometryType.FACE;
    } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
      biometryType = BiometryType.FINGERPRINT;
    } else if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) {
      biometryType = BiometryType.IRIS;
    }

    return {
      isAvailable: true,
      biometryType,
      hasEnrolledCredentials: enrolled,
    };
  } catch (error) {
    console.error('Error checking biometric capabilities:', error);
    return {
      isAvailable: false,
      biometryType: null,
      hasEnrolledCredentials: false,
    };
  }
}

/**
 * Check if biometric auth is enabled for the current user.
 */
export async function isBiometricAuthEnabled(): Promise<boolean> {
  try {
    const enabled = await secureGetItemAsync(BIOMETRIC_ENABLED_KEY);
    return enabled === 'true';
  } catch {
    return false;
  }
}

/**
 * Enable biometric authentication for the current user.
 * Stores a secure session identifier for later authentication.
 * SECURITY: Never stores plaintext passwords - uses Supabase session instead.
 */
export async function enableBiometricAuth(
  sessionToken?: string
): Promise<BiometricAuthResult> {
  try {
    // Check capabilities first
    const capabilities = await getBiometricCapabilities();
    if (!capabilities.isAvailable || !capabilities.hasEnrolledCredentials) {
      return {
        success: false,
        error: 'Biometric authentication is not available on this device',
      };
    }

    // Authenticate with biometrics to confirm user wants to enable
    const authResult = await authenticateWithBiometrics(
      'Enable biometric login for Sorce'
    );

    if (!authResult.success) {
      return authResult;
    }

    // Get current session if token not provided
    let token = sessionToken;
    if (!token) {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.refresh_token) {
        return {
          success: false,
          error: 'No active session to enable biometric login',
        };
      }
      token = session.refresh_token;
    }

    // Store only the refresh token securely - never the password
    await secureSetItemAsync(BIOMETRIC_TOKEN_KEY, token);
    await secureSetItemAsync(BIOMETRIC_ENABLED_KEY, 'true');

    return { success: true };
  } catch (error) {
    console.error('Error enabling biometric auth:', error);
    return {
      success: false,
      error: 'Failed to enable biometric authentication',
    };
  }
}

/**
 * Disable biometric authentication.
 */
export async function disableBiometricAuth(): Promise<void> {
  try {
    await secureDeleteItemAsync(BIOMETRIC_ENABLED_KEY);
    await secureDeleteItemAsync(BIOMETRIC_TOKEN_KEY);
  } catch (error) {
    console.error('Error disabling biometric auth:', error);
  }
}

/**
 * Authenticate with biometrics and log the user in.
 * SECURITY: Uses refresh token, never plaintext password.
 */
export async function loginWithBiometrics(): Promise<BiometricAuthResult> {
  try {
    // Check if biometric auth is enabled
    const enabled = await isBiometricAuthEnabled();
    if (!enabled) {
      return {
        success: false,
        error: 'Biometric authentication is not enabled',
      };
    }

    // Get stored refresh token
    const refreshToken = await secureGetItemAsync(BIOMETRIC_TOKEN_KEY);
    if (!refreshToken) {
      return {
        success: false,
        error: 'No stored session found. Please log in with email and password.',
      };
    }

    // Authenticate with biometrics
    const authResult = await authenticateWithBiometrics(
      'Authenticate to access Sorce'
    );

    if (!authResult.success) {
      return authResult;
    }

    // Use refresh token to get new session (pass string directly, not object)
    const { error } = await supabase.auth.refreshSession(refreshToken);

    if (error) {
      // Clear stored token if it's invalid
      await secureDeleteItemAsync(BIOMETRIC_TOKEN_KEY);
      await secureDeleteItemAsync(BIOMETRIC_ENABLED_KEY);
      return {
        success: false,
        error: 'Session expired. Please log in with email and password.',
      };
    }

    return { success: true };
  } catch (error) {
    console.error('Error logging in with biometrics:', error);
    return {
      success: false,
      error: 'Biometric login failed',
    };
  }
}

/**
 * Show biometric authentication prompt.
 */
export async function authenticateWithBiometrics(
  promptMessage: string = 'Authenticate to continue'
): Promise<BiometricAuthResult> {
  try {
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage,
      fallbackLabel: 'Use passcode',
      cancelLabel: 'Cancel',
      disableDeviceFallback: false,
    });

    if (result.success) {
      return { success: true };
    }

    // Handle specific errors
    let errorMessage = 'Authentication failed';
    
    if (result.error === 'not_enrolled') {
      errorMessage = 'No biometrics enrolled. Please set up biometrics in device settings.';
    } else if (result.error === 'locked_out') {
      errorMessage = 'Too many failed attempts. Please try again later.';
    } else if (result.error === 'user_cancel') {
      errorMessage = 'Authentication was cancelled';
    } else if (result.error === 'user_fallback') {
      errorMessage = 'User chose to use passcode';
    }

    return {
      success: false,
      error: errorMessage,
    };
  } catch (error) {
    console.error('Error during biometric authentication:', error);
    return {
      success: false,
      error: 'Authentication failed',
    };
  }
}

/**
 * Update stored session token (call when session is refreshed).
 * SECURITY: Updates refresh token, never handles passwords.
 */
export async function updateBiometricCredentials(
  newRefreshToken?: string
): Promise<void> {
  try {
    const enabled = await isBiometricAuthEnabled();
    if (!enabled) return;

    let token = newRefreshToken;
    if (!token) {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.refresh_token) {
        // No valid session, clear biometric auth
        await disableBiometricAuth();
        return;
      }
      token = session.refresh_token;
    }

    await secureSetItemAsync(BIOMETRIC_TOKEN_KEY, token);
  } catch (error) {
    console.error('Error updating biometric credentials:', error);
  }
}

/**
 * Get biometry type display name.
 */
export function getBiometryDisplayName(type: BiometryType | null): string {
  switch (type) {
    case BiometryType.FACE_ID:
      return 'Face ID';
    case BiometryType.FACE:
      return 'Face Recognition';
    case BiometryType.FINGERPRINT:
      return Platform.OS === 'ios' ? 'Touch ID' : 'Fingerprint';
    case BiometryType.IRIS:
      return 'Iris Scanner';
    default:
      return 'Biometric';
  }
}

/**
 * Hook for biometric authentication state.
 */
import { useState, useEffect } from 'react';

export interface BiometricState {
  isLoading: boolean;
  isAvailable: boolean;
  isEnabled: boolean;
  biometryType: BiometryType | null;
  biometryDisplayName: string;
}

export function useBiometricAuth(): BiometricState & {
  enable: (email: string, password: string) => Promise<BiometricAuthResult>;
  disable: () => Promise<void>;
  login: () => Promise<BiometricAuthResult>;
  authenticate: () => Promise<BiometricAuthResult>;
} {
  const [state, setState] = useState<BiometricState>({
    isLoading: true,
    isAvailable: false,
    isEnabled: false,
    biometryType: null,
    biometryDisplayName: 'Biometric',
  });

  useEffect(() => {
    async function loadState() {
      const capabilities = await getBiometricCapabilities();
      const enabled = await isBiometricAuthEnabled();

      setState({
        isLoading: false,
        isAvailable: capabilities.isAvailable && capabilities.hasEnrolledCredentials,
        isEnabled: enabled,
        biometryType: capabilities.biometryType,
        biometryDisplayName: getBiometryDisplayName(capabilities.biometryType),
      });
    }

    loadState();
  }, []);

  const enable = async (sessionToken?: string) => {
    const result = await enableBiometricAuth(sessionToken);
    if (result.success) {
      setState((prev) => ({ ...prev, isEnabled: true }));
    }
    return result;
  };

  const disable = async () => {
    await disableBiometricAuth();
    setState((prev) => ({ ...prev, isEnabled: false }));
  };

  const login = async () => {
    return loginWithBiometrics();
  };

  const authenticate = async () => {
    return authenticateWithBiometrics();
  };

  return {
    ...state,
    enable,
    disable,
    login,
    authenticate,
  };
}

export default {
  getBiometricCapabilities,
  isBiometricAuthEnabled,
  enableBiometricAuth,
  disableBiometricAuth,
  loginWithBiometrics,
  authenticateWithBiometrics,
  updateBiometricCredentials,
  getBiometryDisplayName,
  useBiometricAuth,
};
