/**
 * Secure storage abstraction — platform-aware.
 *
 * - iOS/Android: expo-secure-store (encrypted, keychain/keystore)
 * - Web: AsyncStorage (expo-secure-store is not available on web)
 *
 * Use for auth tokens and other sensitive data.
 */

import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import AsyncStorage from "@react-native-async-storage/async-storage";

const isSecure = Platform.OS === "ios" || Platform.OS === "android";

export async function secureGetItemAsync(key: string): Promise<string | null> {
  if (isSecure) {
    return SecureStore.getItemAsync(key);
  }
  return AsyncStorage.getItem(key);
}

export async function secureSetItemAsync(key: string, value: string): Promise<void> {
  if (isSecure) {
    await SecureStore.setItemAsync(key, value);
  } else {
    await AsyncStorage.setItem(key, value);
  }
}

export async function secureDeleteItemAsync(key: string): Promise<void> {
  if (isSecure) {
    await SecureStore.deleteItemAsync(key);
  } else {
    await AsyncStorage.removeItem(key);
  }
}
