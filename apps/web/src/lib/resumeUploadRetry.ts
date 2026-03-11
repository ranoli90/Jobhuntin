import { BrowserCacheService } from './browserCache';

export interface ResumeUploadMetadata {
  file: File;
  fileName: string;
  fileSize: number;
  fileType: string;
  fileBase64?: string;
  lastModified: number;
  uploadAttempts: number;
  lastAttemptTime: number;
  nextRetryTime: number;
  error?: string;
  backoffMs: number;
}

export interface ResumeUploadState {
  isUploading: boolean;
  canRetry: boolean;
  retryCount: number;
  nextRetryIn: number;
  error?: string;
  isOffline: boolean;
  /** R5: True when file was too large to store; re-upload required */
  requiresReupload?: boolean;
}

const MAX_RETRIES = 3;
const BASE_DELAY = 1000; // 1 second
const MAX_DELAY = 30000; // 30 seconds

export class ResumeUploadRetryManager {
  private cacheService: BrowserCacheService;
  private retryTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    this.cacheService = BrowserCacheService.getInstance();
  }

  /** R1: Avoid localStorage QuotaExceeded - files >4MB (~5.3MB base64) skip persistence */
  private static readonly MAX_STORABLE_SIZE = 4 * 1024 * 1024;

  /**
   * Save resume metadata for offline retry.
   * Large files (>4MB) are not stored to avoid localStorage QuotaExceeded; retry will require re-upload.
   */
  async saveResumeMetadata(file: File, error?: string): Promise<void> {
    const metadata: Omit<ResumeUploadMetadata, 'file'> & { fileBase64?: string } = {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      lastModified: file.lastModified,
      uploadAttempts: 1,
      lastAttemptTime: Date.now(),
      nextRetryTime: Date.now() + BASE_DELAY,
      error,
      backoffMs: BASE_DELAY,
    };

    if (file.size <= ResumeUploadRetryManager.MAX_STORABLE_SIZE) {
      try {
        const fileBase64 = await this.fileToBase64(file);
        (metadata as Record<string, unknown>).fileBase64 = fileBase64;
      } catch {
        // fileToBase64 failed; save without file for retry
      }
    }
    // Omit file (not serializable); only fileBase64 is stored
    await this.cacheService.set('resume_upload_metadata', metadata);
  }

  /**
   * Get current upload state
   */
  async getUploadState(): Promise<ResumeUploadState> {
    const metadata = await this.cacheService.get<ResumeUploadMetadata>('resume_upload_metadata');
    
    if (!metadata) {
      return {
        isUploading: false,
        canRetry: false,
        retryCount: 0,
        nextRetryIn: 0,
        isOffline: !navigator.onLine,
      };
    }

    const now = Date.now();
    const hasFileData = !!(metadata as ResumeUploadMetadata & { fileBase64?: string }).fileBase64;
    const canRetry = hasFileData &&
                      metadata.uploadAttempts < MAX_RETRIES &&
                      metadata.nextRetryTime <= now &&
                      navigator.onLine;

    return {
      isUploading: false,
      canRetry,
      retryCount: metadata.uploadAttempts,
      nextRetryIn: Math.max(0, metadata.nextRetryTime - now),
      error: metadata.error,
      isOffline: !navigator.onLine,
      requiresReupload: !hasFileData && metadata.uploadAttempts > 0,
    };
  }

  /**
   * Calculate next retry time with exponential backoff
   */
  private calculateBackoff(attempt: number): number {
    const delay = Math.min(BASE_DELAY * Math.pow(2, attempt - 1), MAX_DELAY);
    // Add jitter to prevent thundering herd
    return delay + Math.random() * 1000;
  }

  /**
   * Update metadata after failed attempt.
   * Preserves fileBase64 if present; does not re-add (file not available in this context).
   */
  async updateAfterFailure(error: string): Promise<void> {
    const metadata = await this.cacheService.get<ResumeUploadMetadata & { fileBase64?: string }>('resume_upload_metadata');
    if (!metadata) return;

    const nextBackoff = this.calculateBackoff(metadata.uploadAttempts + 1);
    const updatedMetadata: Record<string, unknown> = {
      ...metadata,
      uploadAttempts: metadata.uploadAttempts + 1,
      lastAttemptTime: Date.now(),
      nextRetryTime: Date.now() + nextBackoff,
      error,
      backoffMs: nextBackoff,
    };
    delete updatedMetadata.file; // Not serializable
    await this.cacheService.set('resume_upload_metadata', updatedMetadata);
  }

  /**
   * Clear metadata after successful upload
   */
  async clearMetadata(): Promise<void> {
    await this.cacheService.del('resume_upload_metadata');
    this.clearRetryTimer();
  }

  /**
   * Get stored file from metadata
   */
  async getStoredFile(): Promise<File | null> {
    const metadata = await this.cacheService.get<ResumeUploadMetadata>('resume_upload_metadata');
    if (!metadata?.fileBase64) return null;

    return this.base64ToFile(metadata.fileBase64, metadata.fileName, metadata.fileType);
  }

  /**
   * Convert file to base64
   */
  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Convert base64 back to File
   */
  private base64ToFile(base64: string, fileName: string, fileType: string): File {
    const dataPart = base64.split(',')[1];
    if (!dataPart) throw new Error("Invalid base64 data URL: missing data part");
    const byteString = atob(dataPart);
    const arrayBuffer = new ArrayBuffer(byteString.length);
    const uint8Array = new Uint8Array(arrayBuffer);
    
    for (let i = 0; i < byteString.length; i++) {
      uint8Array[i] = byteString.charCodeAt(i);
    }
    
    return new File([arrayBuffer], fileName, { type: fileType });
  }

  /**
   * Set up automatic retry timer
   */
  setupRetryTimer(onRetry: () => void): void {
    this.clearRetryTimer();
    
    this.cacheService.get<ResumeUploadMetadata>('resume_upload_metadata').then((metadata: ResumeUploadMetadata | null) => {
      if (!metadata || metadata.uploadAttempts >= MAX_RETRIES) return;
      
      const delay = Math.max(0, metadata.nextRetryTime - Date.now());
      
      const timer = setTimeout(() => {
        if (navigator.onLine) {
          onRetry();
        }
      }, delay);
      
      this.retryTimers.set('resume_upload', timer);
    });
  }

  /**
   * Clear retry timer
   */
  clearRetryTimer(): void {
    const timer = this.retryTimers.get('resume_upload');
    if (timer) {
      clearTimeout(timer);
      this.retryTimers.delete('resume_upload');
    }
  }

  /**
   * Check if retry is possible
   */
  async canRetry(): Promise<boolean> {
    const state = await this.getUploadState();
    return state.canRetry;
  }

  /**
   * Get retry guidance message (legacy, returns English)
   */
  async getRetryMessage(): Promise<string> {
    const { key, params } = await this.getRetryMessageI18n();
    if (key === "resumeRetry.offline") return "You're offline. The resume will be automatically uploaded when you reconnect.";
    if (key === "resumeRetry.maxReached") return "Maximum retry attempts reached. Please try uploading again or contact support.";
    if (key === "resumeRetry.retryingIn") {
      const minutes = params?.minutes ?? 1;
      return `Retrying in ${minutes} minute${minutes !== 1 ? "s" : ""}...`;
    }
    return "Ready to retry.";
  }

  /**
   * Get retry message as i18n key + params for component translation (I2)
   */
  async getRetryMessageI18n(): Promise<{ key: string; params?: Record<string, string | number> }> {
    const state = await this.getUploadState();
    if (!navigator.onLine) return { key: "resumeRetry.offline" };
    if (state.retryCount >= MAX_RETRIES) return { key: "resumeRetry.maxReached" };
    if (state.nextRetryIn > 0) {
      const minutes = Math.ceil(state.nextRetryIn / 60000);
      return { key: "resumeRetry.retryingIn", params: { minutes } };
    }
    return { key: "resumeRetry.ready" };
  }
}

// Singleton instance
export const resumeUploadRetry = new ResumeUploadRetryManager();
