/**
 * Atomic State Manager
 * 
 * Provides thread-safe state management with file locking to prevent
 * race conditions when multiple instances run simultaneously.
 */

import { promises as fs } from 'fs';
import path from 'path';

/**
 * Atomic state manager with file locking
 */
export class AtomicStateManager<T> {
  private stateFile: string;
  private lockFile: string;
  private lockTimeout: number;
  private lockCheckInterval: number;

  constructor(
    stateFile: string,
    lockTimeout: number = 30000,
    lockCheckInterval: number = 100
  ) {
    this.stateFile = stateFile;
    this.lockFile = `${stateFile}.lock`;
    this.lockTimeout = lockTimeout;
    this.lockCheckInterval = lockCheckInterval;
  }

  /**
   * Acquire exclusive lock
   */
  private async acquireLock(): Promise<void> {
    const startTime = Date.now();

    while (true) {
      try {
        // Try to create lock file exclusively (fails if exists)
        const fd = await fs.open(this.lockFile, 'wx');
        await fd.close();
        return;
      } catch (e: any) {
        if (e.code !== 'EEXIST') {
          throw e;
        }

        // Check if lock is stale
        const elapsed = Date.now() - startTime;
        if (elapsed > this.lockTimeout) {
          // Force remove stale lock
          try {
            await fs.unlink(this.lockFile);
          } catch {
            // Ignore if already deleted
          }
          continue;
        }

        // Wait before retrying
        await new Promise(r => setTimeout(r, this.lockCheckInterval));
      }
    }
  }

  /**
   * Release lock
   */
  private async releaseLock(): Promise<void> {
    try {
      await fs.unlink(this.lockFile);
    } catch {
      // Ignore if already deleted
    }
  }

  /**
   * Load state from file
   */
  async load(defaultValue: T): Promise<T> {
    try {
      const content = await fs.readFile(this.stateFile, 'utf-8');
      return JSON.parse(content);
    } catch (e: unknown) {
      const error = e as NodeJS.ErrnoException;
      if (error.code === 'ENOENT') {
        // File doesn't exist, return default
        return defaultValue;
      }
      // For other errors, log and return default
      const errorMessage = error instanceof Error ? error.message : String(e);
      console.warn(`Failed to load state from ${this.stateFile}:`, errorMessage);
      return defaultValue;
    }
  }

  /**
   * Save state to file atomically
   */
  async save(state: T): Promise<void> {
    await this.acquireLock();

    try {
      // Ensure directory exists
      const dir = path.dirname(this.stateFile);
      await fs.mkdir(dir, { recursive: true });

      // Write to temporary file first
      const tmpFile = `${this.stateFile}.tmp`;
      await fs.writeFile(tmpFile, JSON.stringify(state, null, 2), 'utf-8');

      // Atomically rename temp file to actual file
      await fs.rename(tmpFile, this.stateFile);
    } finally {
      await this.releaseLock();
    }
  }

  /**
   * Update state with a function
   */
  async update(updater: (state: T) => T, defaultValue: T): Promise<T> {
    await this.acquireLock();

    try {
      // Load current state
      const current = await this.load(defaultValue);

      // Update state
      const updated = updater(current);

      // Save updated state
      const dir = path.dirname(this.stateFile);
      await fs.mkdir(dir, { recursive: true });

      const tmpFile = `${this.stateFile}.tmp`;
      await fs.writeFile(tmpFile, JSON.stringify(updated, null, 2), 'utf-8');
      await fs.rename(tmpFile, this.stateFile);

      return updated;
    } finally {
      await this.releaseLock();
    }
  }

  /**
   * Check if state file exists
   */
  async exists(): Promise<boolean> {
    try {
      await fs.access(this.stateFile);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Delete state file
   */
  async delete(): Promise<void> {
    await this.acquireLock();

    try {
      await fs.unlink(this.stateFile);
    } catch (e: unknown) {
      const error = e as NodeJS.ErrnoException;
      if (error.code !== 'ENOENT') {
        throw e;
      }
    } finally {
      await this.releaseLock();
    }
  }

  /**
   * Get file modification time
   */
  async getModificationTime(): Promise<Date | null> {
    try {
      const stats = await fs.stat(this.stateFile);
      return new Date(stats.mtime);
    } catch {
      return null;
    }
  }
}

/**
 * Create state manager for a specific file
 */
export function createStateManager<T>(stateFile: string): AtomicStateManager<T> {
  return new AtomicStateManager<T>(stateFile);
}
