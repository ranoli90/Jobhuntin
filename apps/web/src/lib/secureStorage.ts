import { telemetry } from "./telemetry";

interface SecureStorageOptions {
  ttl?: number; // Time to live in milliseconds
  encrypt?: boolean; // Whether to encrypt the data
}

interface StoredData<T = unknown> {
  data: T;
  timestamp: number;
  ttl?: number;
  encrypted?: boolean;
}

/**
 * Secure storage utility that uses session storage with optional encryption and TTL
 * Uses Web Crypto API for encryption when enabled
 */
class SecureStorage {
  private encryptionKey: CryptoKey | null = null;
  private readonly DEFAULT_TTL = 24 * 60 * 60 * 1000; // 24 hours

  constructor() {
    this.initEncryptionKey();
  }

  private async initEncryptionKey(): Promise<void> {
    try {
      // Generate or retrieve encryption key from session storage
      const storedKey = sessionStorage.getItem("secure_storage_key");
      if (storedKey) {
        const keyData = new Uint8Array(JSON.parse(storedKey));
        this.encryptionKey = await crypto.subtle.importKey(
          "raw",
          keyData,
          { name: "AES-GCM" },
          false,
          ["encrypt", "decrypt"],
        );
      } else {
        // Generate new key
        this.encryptionKey = await crypto.subtle.generateKey(
          { name: "AES-GCM", length: 256 },
          true,
          ["encrypt", "decrypt"],
        );
        const exportedKey = await crypto.subtle.exportKey(
          "raw",
          this.encryptionKey,
        );
        sessionStorage.setItem(
          "secure_storage_key",
          JSON.stringify([...new Uint8Array(exportedKey)]),
        );
      }
    } catch (error) {
      console.error("[SecureStorage] Failed to initialize encryption:", error);
      telemetry.track("Secure Storage Error", {
        error: "encryption_init_failed",
      });
    }
  }

  private async encrypt(
    data: string,
  ): Promise<{ encrypted: string; iv: string }> {
    if (!this.encryptionKey) {
      throw new Error("Encryption key not initialized");
    }

    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const iv = crypto.getRandomValues(new Uint8Array(12));

    const encrypted = await crypto.subtle.encrypt(
      { name: "AES-GCM", iv },
      this.encryptionKey,
      dataBuffer,
    );

    return {
      encrypted: this.arrayBufferToBase64(encrypted),
      iv: this.arrayBufferToBase64(iv.buffer),
    };
  }

  private async decrypt(encryptedData: string, iv: string): Promise<string> {
    if (!this.encryptionKey) {
      throw new Error("Encryption key not initialized");
    }

    const encryptedBuffer = this.base64ToArrayBuffer(encryptedData);
    const ivBuffer = this.base64ToArrayBuffer(iv);

    const decrypted = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: ivBuffer },
      this.encryptionKey,
      encryptedBuffer,
    );

    return new TextDecoder().decode(decrypted);
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    return btoa(String.fromCharCode(...bytes));
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index++) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes.buffer;
  }

  private isExpired(timestamp: number, ttl?: number): boolean {
    const expiryTime = timestamp + (ttl || this.DEFAULT_TTL);
    return Date.now() > expiryTime;
  }

  /**
   * Store data securely in session storage
   */
  async setItem<T>(
    key: string,
    data: T,
    options: SecureStorageOptions = {},
  ): Promise<void> {
    try {
      const { ttl = this.DEFAULT_TTL, encrypt = true } = options;
      const timestamp = Date.now();

      let processedData: unknown = data;
      let encrypted = false;

      if (encrypt && typeof data === "object") {
        const jsonString = JSON.stringify(data);
        const { encrypted: encryptedData, iv } = await this.encrypt(jsonString);
        processedData = { encrypted: encryptedData, iv } as unknown;
        encrypted = true;
      }

      const storedData: StoredData = {
        data: processedData,
        timestamp,
        ttl,
        encrypted,
      };

      sessionStorage.setItem(key, JSON.stringify(storedData));

      telemetry.track("Secure Storage Set", {
        key: key.replaceAll(/pii|contact|email|name/gi, "***"),
        encrypted,
        ttl,
      });
    } catch (error) {
      console.error("[SecureStorage] Failed to set item:", error);
      telemetry.track("Secure Storage Error", { error: "set_failed", key });
      throw error;
    }
  }

  /**
   * Retrieve data from secure storage
   */
  async getItem<T = any>(key: string): Promise<T | null> {
    try {
      const stored = sessionStorage.getItem(key);
      if (!stored) return null;

      const storedData: StoredData = JSON.parse(stored);

      // Check expiration
      if (this.isExpired(storedData.timestamp, storedData.ttl)) {
        sessionStorage.removeItem(key);
        telemetry.track("Secure Storage Expired", {
          key: key.replaceAll(/pii|contact|email|name/gi, "***"),
        });
        return null;
      }

      let data = storedData.data;

      // Decrypt if needed
      if (
        storedData.encrypted &&
        data != undefined &&
        typeof data === "object"
      ) {
        const encObject = data as Record<string, string>;
        if (encObject.encrypted && encObject.iv) {
          const decrypted = await this.decrypt(
            encObject.encrypted,
            encObject.iv,
          );
          data = JSON.parse(decrypted);
        }
      }

      return data as T;
    } catch (error) {
      console.error("[SecureStorage] Failed to get item:", error);
      telemetry.track("Secure Storage Error", { error: "get_failed", key });
      // Remove corrupted data
      sessionStorage.removeItem(key);
      return null;
    }
  }

  /**
   * Remove an item from secure storage
   */
  removeItem(key: string): void {
    sessionStorage.removeItem(key);
  }

  /**
   * Clear all secure storage data
   */
  clear(): void {
    // Only remove items that were stored using SecureStorage
    const keys = Object.keys(sessionStorage);
    for (const key of keys) {
      if (
        key.startsWith("secure_") ||
        key.includes("pii") ||
        key.includes("contact")
      ) {
        sessionStorage.removeItem(key);
      }
    }
    // Also remove encryption key
    sessionStorage.removeItem("secure_storage_key");
  }

  /**
   * Check if a key exists and is not expired
   */
  async hasValidItem(key: string): Promise<boolean> {
    const item = await this.getItem(key);
    return item !== null;
  }
}

// Export singleton instance
export const secureStorage = new SecureStorage();

// Helper functions for common use cases
export const securePIIStorage = {
  set: async <T>(key: string, data: T, ttl?: number) => {
    return secureStorage.setItem(`pii_${key}`, data, {
      ttl: ttl || 4 * 60 * 60 * 1000, // 4 hours for PII
      encrypt: true,
    });
  },
  get: <T = unknown>(key: string) => secureStorage.getItem<T>(`pii_${key}`),
  remove: (key: string) => secureStorage.removeItem(`pii_${key}`),
  clear: () => {
    // Clear all PII-related items
    const keys = Object.keys(sessionStorage);
    for (const key of keys) {
      if (key.startsWith("pii_")) {
        sessionStorage.removeItem(key);
      }
    }
  },
};
