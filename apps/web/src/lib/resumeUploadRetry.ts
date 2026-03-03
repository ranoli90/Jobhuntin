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

  /**
   * Save resume metadata for offline retry
   */
  async saveResumeMetadata(file: File, error?: string): Promise<void> {
    const metadata: ResumeUploadMetadata = {
      file,
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

    // Store file as base64 for persistence
    const fileBase64 = await this.fileToBase64(file);
    await this.cacheService.set('resume_upload_metadata', {
      ...metadata,
      fileBase64,
    });
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
    const canRetry = metadata.uploadAttempts < MAX_RETRIES && 
                      metadata.nextRetryTime <= now &&
                      navigator.onLine;

    return {
      isUploading: false,
      canRetry,
      retryCount: metadata.uploadAttempts,
      nextRetryIn: Math.max(0, metadata.nextRetryTime - now),
      error: metadata.error,
      isOffline: !navigator.onLine,
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
   * Update metadata after failed attempt
   */
  async updateAfterFailure(error: string): Promise<void> {
    const metadata = await this.cacheService.get<ResumeUploadMetadata>('resume_upload_metadata');
    if (!metadata) return;

    const nextBackoff = this.calculateBackoff(metadata.uploadAttempts + 1);
    const updatedMetadata: ResumeUploadMetadata = {
      ...metadata,
      uploadAttempts: metadata.uploadAttempts + 1,
      lastAttemptTime: Date.now(),
      nextRetryTime: Date.now() + nextBackoff,
      error,
      backoffMs: nextBackoff,
    };

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
    const byteString = atob(base64.split(',')[1]);
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
   * Get retry guidance message
   */
  async getRetryMessage(): Promise<string> {
    const state = await this.getUploadState();
    
    if (!navigator.onLine) {
      return "You're offline. The resume will be automatically uploaded when you reconnect.";
    }
    
    if (state.retryCount >= MAX_RETRIES) {
      return "Maximum retry attempts reached. Please try uploading again or contact support.";
    }
    
    if (state.nextRetryIn > 0) {
      const minutes = Math.ceil(state.nextRetryIn / 60000);
      return `Retrying in ${minutes} minute${minutes !== 1 ? 's' : ''}...`;
    }
    
    return "Ready to retry.";
  }
}

// Singleton instance
export const resumeUploadRetry = new ResumeUploadRetryManager();
