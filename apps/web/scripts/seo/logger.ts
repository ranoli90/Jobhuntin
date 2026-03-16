/**
 * SEO Engine Structured Logging
 * 
 * Comprehensive logging system with structured log entries, multiple log levels,
 * file-based logging with rotation, and specialized loggers for different use cases.
 * 
 * @module seo/logger
 */

import { ErrorContext, SEO_ERROR_CODES } from './errors';
import * as path from 'path';
import * as fs from 'fs';

// ============================================================================
// Log Levels
// ============================================================================

/**
 * Log severity levels in ascending order of severity
 */
export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
    FATAL = 4
}

/**
 * Human-readable log level names
 */
export const LOG_LEVEL_NAMES: Record<LogLevel, string> = {
    [LogLevel.DEBUG]: 'DEBUG',
    [LogLevel.INFO]: 'INFO',
    [LogLevel.WARN]: 'WARN',
    [LogLevel.ERROR]: 'ERROR',
    [LogLevel.FATAL]: 'FATAL'
};

// ============================================================================
// Log Entry Interface
// ============================================================================

/**
 * Structured log entry
 */
export interface LogEntry {
    /** Timestamp in ISO 8601 format */
    timestamp: string;
    /** Log severity level */
    level: LogLevel;
    /** Human-readable message */
    message: string;
    /** Operation context (e.g., 'generateContent', 'submitURL') */
    operation?: string;
    /** Additional metadata */
    metadata?: Record<string, unknown>;
    /** Error object if this is an error log */
    error?: Error;
    /** Duration in milliseconds (for operation logs) */
    duration?: number;
    /** Error code for categorized errors */
    errorCode?: SEO_ERROR_CODES;
    /** Error context for structured error reporting */
    errorContext?: ErrorContext;
}

// ============================================================================
// Logger Configuration
// ============================================================================

/**
 * Log destination types
 */
export type LogDestination = 'console' | 'file' | 'database';

/**
 * Logger configuration options
 */
export interface LoggerConfig {
    /** Minimum log level to output */
    level: LogLevel;
    /** Log destinations */
    destination: LogDestination | LogDestination[];
    /** Whether to include metadata in log output */
    includeMetadata: boolean;
    /** Whether to mask sensitive data */
    maskSensitiveData: boolean;
    /** File path for file-based logging */
    filePath?: string;
    /** Maximum file size in bytes before rotation */
    maxFileSize?: number;
    /** Maximum number of rotated log files to keep */
    maxRotatedFiles?: number;
    /** Log retention period in days */
    retentionDays?: number;
    /** Whether to enable JSON formatting */
    jsonFormat?: boolean;
    /** Custom timestamp format */
    timestampFormat?: string;
}

// ============================================================================
// Sensitive Data Patterns
// ============================================================================

/**
 * Patterns for sensitive data that should be masked
 */
const SENSITIVE_PATTERNS: Array<{ pattern: RegExp; replacement: string }> = [
    { pattern: /("|')(?:api[_-]?key|secret|token|password|auth)[^"'\\]*(?:"|')/gi, replacement: '****' },
    { pattern: /(?:bearer|basic|oauth)\s+[a-zA-Z0-9\-_.~+/]+=*/gi, replacement: 'Bearer ****' },
    { pattern: /(?:private[_-]?key|private_key)[^,\n]*/gi, replacement: 'private_key: ****' },
    { pattern: /(?<=(key|token|secret|password)["']?\s*[:=]\s*["']?)[a-zA-Z0-9\-_.~/=]+(?=["']?\s*[,}\n])/gi, replacement: '****' },
    { pattern: /(\"url\":\s*\"https?:\/\/)[^@]+(@.*?\")/gi, replacement: '$1****$2' },
    { pattern: /(googleusercontent\.com\/)[^?]+(\?.*)/gi, replacement: '$1****$2' },
];

// ============================================================================
// Default Configuration
// ============================================================================

/**
 * Default logger configuration
 */
export const DEFAULT_LOGGER_CONFIG: LoggerConfig = {
    level: LogLevel.INFO,
    destination: 'console',
    includeMetadata: true,
    maskSensitiveData: true,
    maxFileSize: 10 * 1024 * 1024, // 10MB
    maxRotatedFiles: 5,
    retentionDays: 30,
    jsonFormat: false,
    timestampFormat: 'ISO'
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get current timestamp in ISO 8601 format
 */
function getTimestamp(): string {
    return new Date().toISOString();
}

/**
 * Mask sensitive data in a string
 */
function maskSensitiveData(data: string): string {
    let masked = data;
    for (const { pattern, replacement } of SENSITIVE_PATTERNS) {
        masked = masked.replace(pattern, replacement);
    }
    return masked;
}

/**
 * Mask sensitive fields in an object
 */
function maskObject(obj: Record<string, unknown>): Record<string, unknown> {
    const sensitiveFields = ['apiKey', 'api_key', 'secret', 'token', 'password', 'privateKey', 'private_key', 'accessToken', 'refreshToken', 'authorization', 'credentials'];
    const masked: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(obj)) {
        const lowerKey = key.toLowerCase();
        if (sensitiveFields.some(field => lowerKey.includes(field))) {
            masked[key] = '****';
        } else if (typeof value === 'string') {
            masked[key] = maskSensitiveData(value);
        } else if (typeof value === 'object' && value !== null) {
            masked[key] = maskObject(value as Record<string, unknown>);
        } else {
            masked[key] = value;
        }
    }

    return masked;
}

/**
 * Format log entry as string
 */
function formatLogEntry(entry: LogEntry, config: LoggerConfig): string {
    const timestamp = entry.timestamp;
    const level = LOG_LEVEL_NAMES[entry.level];
    const operation = entry.operation ? `[${entry.operation}]` : '';

    let message = `${timestamp} ${level} ${operation} ${entry.message}`;

    if (config.includeMetadata && entry.metadata) {
        const metadata = config.maskSensitiveData
            ? maskObject(entry.metadata as Record<string, unknown>)
            : entry.metadata;
        message += ` | metadata: ${JSON.stringify(metadata)}`;
    }

    if (entry.error) {
        const errorInfo = config.maskSensitiveData
            ? maskSensitiveData(entry.error.message)
            : entry.error.message;
        message += ` | error: ${errorInfo}`;
        if (entry.error.stack) {
            const stack = config.maskSensitiveData
                ? maskSensitiveData(entry.error.stack)
                : entry.error.stack;
            message += `\n${stack}`;
        }
    }

    if (entry.duration !== undefined) {
        message += ` | duration: ${entry.duration}ms`;
    }

    if (entry.errorCode) {
        message += ` | code: ${entry.errorCode}`;
    }

    return message;
}

/**
 * Format log entry as JSON
 */
function formatLogEntryAsJson(entry: LogEntry, config: LoggerConfig): string {
    const logData: Record<string, unknown> = {
        timestamp: entry.timestamp,
        level: LOG_LEVEL_NAMES[entry.level],
        message: entry.message,
        operation: entry.operation,
        errorCode: entry.errorCode,
        duration: entry.duration
    };

    if (config.includeMetadata) {
        logData.metadata = config.maskSensitiveData && entry.metadata
            ? maskObject(entry.metadata as Record<string, unknown>)
            : entry.metadata;
    }

    if (entry.error) {
        logData.error = {
            name: entry.error.name,
            message: config.maskSensitiveData
                ? maskSensitiveData(entry.error.message)
                : entry.error.message,
            stack: config.maskSensitiveData
                ? maskSensitiveData(entry.error.stack || '')
                : entry.error.stack
        };
    }

    if (entry.errorContext) {
        logData.errorContext = entry.errorContext;
    }

    return JSON.stringify(logData);
}

// ============================================================================
// In-Memory Log Buffer
// ============================================================================

/**
 * In-memory buffer for batch writes
 */
class LogBuffer {
    private buffer: LogEntry[] = [];
    private maxSize: number;
    private flushCallback?: (entries: LogEntry[]) => void;

    constructor(maxSize: number = 100) {
        this.maxSize = maxSize;
    }

    /**
     * Add entry to buffer
     */
    add(entry: LogEntry): void {
        this.buffer.push(entry);
        if (this.buffer.length >= this.maxSize) {
            this.flush();
        }
    }

    /**
     * Flush buffer to destination
     */
    flush(): void {
        if (this.buffer.length > 0 && this.flushCallback) {
            this.flushCallback(this.buffer);
            this.buffer = [];
        }
    }

    /**
     * Set flush callback
     */
    onFlush(callback: (entries: LogEntry[]) => void): void {
        this.flushCallback = callback;
    }

    /**
     * Get buffer contents
     */
    getEntries(): LogEntry[] {
        return [...this.buffer];
    }

    /**
     * Clear buffer
     */
    clear(): void {
        this.buffer = [];
    }
}

// ============================================================================
// File Logger
// ============================================================================

/**
 * File-based logger with rotation support
 */
class FileLogger {
    private filePath: string;
    private maxFileSize: number;
    private maxRotatedFiles: number;
    private fsModule: typeof fs;
    private buffer: LogBuffer;

    constructor(filePath: string, maxFileSize: number = 10 * 1024 * 1024, maxRotatedFiles: number = 5) {
        this.filePath = filePath;
        this.maxFileSize = maxFileSize;
        this.maxRotatedFiles = maxRotatedFiles;
        this.fsModule = fs;
        this.buffer = new LogBuffer(50);

        this.initialize();
    }

    /**
     * Initialize log file
     */
    private initialize(): void {
        const dir = path.dirname(this.filePath);
        if (!this.fsModule.existsSync(dir)) {
            this.fsModule.mkdirSync(dir, { recursive: true });
        }
        if (!this.fsModule.existsSync(this.filePath)) {
            this.fsModule.writeFileSync(this.filePath, '');
        }
    }

    /**
     * Write log entry to file
     */
    write(entry: LogEntry, config: LoggerConfig): void {
        const formatted = config.jsonFormat
            ? formatLogEntryAsJson(entry, config)
            : formatLogEntry(entry, config);

        this.buffer.add(entry);

        // Write synchronously for important logs
        if (entry.level >= LogLevel.ERROR) {
            this.flush();
        }
    }

    /**
     * Flush buffer to file
     */
    flush(): void {
        const entries = this.buffer.getEntries();
        if (entries.length === 0) return;

        // Check file size and rotate if needed
        const stats = this.fsModule.statSync(this.filePath);
        if (stats.size >= this.maxFileSize) {
            this.rotate();
        }

        const lines = entries.map(entry =>
            formatLogEntryAsJson(entry, { ...DEFAULT_LOGGER_CONFIG, jsonFormat: true, includeMetadata: true, maskSensitiveData: true } as LoggerConfig)
        ).join('\n') + '\n';

        this.fsModule.appendFileSync(this.filePath, lines);
        this.buffer.clear();
    }

    /**
     * Rotate log files
     */
    private rotate(): void {
        // Remove oldest rotated file
        const rotatedPath = `${this.filePath}.${this.maxRotatedFiles}`;
        if (this.fsModule.existsSync(rotatedPath)) {
            this.fsModule.unlinkSync(rotatedPath);
        }

        // Shift existing rotated files
        for (let i = this.maxRotatedFiles - 1; i >= 1; i--) {
            const oldPath = `${this.filePath}.${i}`;
            const newPath = `${this.filePath}.${i + 1}`;
            if (this.fsModule.existsSync(oldPath)) {
                this.fsModule.renameSync(oldPath, newPath);
            }
        }

        // Rotate current file
        this.fsModule.renameSync(this.filePath, `${this.filePath}.1`);

        // Create new log file
        this.fsModule.writeFileSync(this.filePath, '');
    }

    /**
     * Clean up old log files based on retention policy
     */
    cleanup(retentionDays: number): void {
        const now = Date.now();
        const retentionMs = retentionDays * 24 * 60 * 60 * 1000;

        // Check rotated files
        for (let i = 1; i <= this.maxRotatedFiles; i++) {
            const rotatedPath = `${this.filePath}.${i}`;
            if (this.fsModule.existsSync(rotatedPath)) {
                const stats = this.fsModule.statSync(rotatedPath);
                if (now - stats.mtimeMs > retentionMs) {
                    this.fsModule.unlinkSync(rotatedPath);
                }
            }
        }
    }

    /**
     * Close file logger
     */
    close(): void {
        this.flush();
    }
}

// ============================================================================
// Main Logger Class
// ============================================================================

/**
 * Main Logger class for SEO engine
 */
export class Logger {
    protected config: LoggerConfig;
    protected fileLogger?: FileLogger;
    protected operationStartTimes: Map<string, number> = new Map();

    /**
     * Create a new Logger instance
     */
    constructor(config: Partial<LoggerConfig> = {}) {
        this.config = { ...DEFAULT_LOGGER_CONFIG, ...config };

        // Initialize file logger if destination includes file
        const destinations = Array.isArray(this.config.destination)
            ? this.config.destination
            : [this.config.destination];

        if (destinations.includes('file') && this.config.filePath) {
            this.fileLogger = new FileLogger(
                this.config.filePath,
                this.config.maxFileSize,
                this.config.maxRotatedFiles
            );
        }
    }

    /**
     * Log a debug message
     */
    debug(message: string, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: getTimestamp(),
            level: LogLevel.DEBUG,
            message,
            metadata
        });
    }

    /**
     * Log an info message
     */
    info(message: string, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: getTimestamp(),
            level: LogLevel.INFO,
            message,
            metadata
        });
    }

    /**
     * Log a warning message
     */
    warn(message: string, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: getTimestamp(),
            level: LogLevel.WARN,
            message,
            metadata
        });
    }

    /**
     * Log an error message
     */
    error(message: string, error?: Error, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: getTimestamp(),
            level: LogLevel.ERROR,
            message,
            error,
            metadata
        });
    }

    /**
     * Log a fatal error message
     */
    fatal(message: string, error?: Error, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: getTimestamp(),
            level: LogLevel.FATAL,
            message,
            error,
            metadata
        });
    }

    /**
     * Log with error context
     */
    logWithContext(context: ErrorContext, metadata?: Record<string, unknown>): void {
        this.log({
            timestamp: context.timestamp,
            level: LogLevel.ERROR,
            message: context.message,
            operation: context.operation,
            metadata: { ...context.metadata, ...metadata },
            error: context.originalError,
            errorCode: context.code,
            errorContext: context
        });
    }

    /**
     * Core logging method (public for external access)
     */
    public log(entry: LogEntry): void {
        // Skip if below minimum log level
        if (entry.level < this.config.level) {
            return;
        }

        const destinations = Array.isArray(this.config.destination)
            ? this.config.destination
            : [this.config.destination];

        for (const destination of destinations) {
            switch (destination) {
                case 'console':
                    this.writeToConsole(entry);
                    break;
                case 'file':
                    this.writeToFile(entry);
                    break;
                case 'database':
                    // Database logging would be implemented with actual DB connection
                    this.writeToDatabase(entry);
                    break;
            }
        }
    }

    /**
     * Write to console
     */
    protected writeToConsole(entry: LogEntry): void {
        const formatted = this.config.jsonFormat
            ? formatLogEntryAsJson(entry, this.config)
            : formatLogEntry(entry, this.config);

        switch (entry.level) {
            case LogLevel.DEBUG:
                console.debug(formatted);
                break;
            case LogLevel.INFO:
                console.info(formatted);
                break;
            case LogLevel.WARN:
                console.warn(formatted);
                break;
            case LogLevel.ERROR:
            case LogLevel.FATAL:
                console.error(formatted);
                break;
        }
    }

    /**
     * Write to file
     */
    protected writeToFile(entry: LogEntry): void {
        if (this.fileLogger) {
            this.fileLogger.write(entry, this.config);
        }
    }

    /**
     * Write to database (placeholder for actual implementation)
     */
    protected writeToDatabase(entry: LogEntry): void {
        // This would integrate with database logging
        // For now, we log to console as fallback
        console.info('[DB] Would log:', formatLogEntryAsJson(entry, this.config));
    }

    /**
     * Set log level
     */
    setLevel(level: LogLevel): void {
        this.config.level = level;
    }

    /**
     * Get current log level
     */
    getLevel(): LogLevel {
        return this.config.level;
    }

    /**
     * Update configuration
     */
    updateConfig(config: Partial<LoggerConfig>): void {
        this.config = { ...this.config, ...config };
    }

    /**
     * Cleanup old log files
     */
    cleanup(retentionDays?: number): void {
        if (this.fileLogger) {
            this.fileLogger.cleanup(retentionDays || this.config.retentionDays || 30);
        }
    }

    /**
     * Close logger
     */
    close(): void {
        if (this.fileLogger) {
            this.fileLogger.close();
        }
    }

    /**
     * Create a child logger with additional context
     */
    child(context: Record<string, unknown>): Logger {
        const childLogger = new Logger(this.config);
        const originalLog = childLogger.log.bind(childLogger);

        (childLogger as unknown as { log: (entry: LogEntry) => void }).log = (entry: LogEntry) => {
            originalLog({
                ...entry,
                metadata: { ...context, ...entry.metadata }
            });
        };

        return childLogger;
    }
}

// ============================================================================
// Operation Logger - For tracking operation start/end with duration
// ============================================================================

/**
 * Specialized logger for tracking operation start/end with duration
 */
export class OperationLogger {
    private logger: Logger;
    private operation: string;
    private startTime?: number;

    /**
     * Create a new OperationLogger
     */
    constructor(logger: Logger, operation: string) {
        this.logger = logger;
        this.operation = operation;
    }

    /**
     * Start the operation
     */
    start(metadata?: Record<string, unknown>): void {
        this.startTime = Date.now();
        this.logger.info(`Starting operation: ${this.operation}`, metadata);
    }

    /**
     * Complete the operation successfully
     */
    complete(metadata?: Record<string, unknown>): void {
        const duration = this.startTime ? Date.now() - this.startTime : undefined;
        this.logger.info(`Completed operation: ${this.operation}`, {
            ...metadata,
            duration,
            status: 'success'
        });
    }

    /**
     * Fail the operation
     */
    fail(error: Error, metadata?: Record<string, unknown>): void {
        const duration = this.startTime ? Date.now() - this.startTime : undefined;
        this.logger.error(`Failed operation: ${this.operation}`, error, {
            ...metadata,
            duration,
            status: 'failed'
        });
    }

    /**
     * Warn during operation
     */
    warn(message: string, metadata?: Record<string, unknown>): void {
        this.logger.warn(`[${this.operation}] ${message}`, metadata);
    }

    /**
     * Debug during operation
     */
    debug(message: string, metadata?: Record<string, unknown>): void {
        this.logger.debug(`[${this.operation}] ${message}`, metadata);
    }

    /**
     * Get elapsed time in milliseconds
     */
    getElapsedTime(): number | undefined {
        return this.startTime ? Date.now() - this.startTime : undefined;
    }
}

// ============================================================================
// Error Logger - For structured error logging with context
// ============================================================================

/**
 * Specialized logger for structured error logging with context
 */
export class ErrorLogger {
    private logger: Logger;

    /**
     * Create a new ErrorLogger
     */
    constructor(logger: Logger) {
        this.logger = logger;
    }

    /**
     * Log an error with full context
     */
    log(errorContext: ErrorContext): void {
        const metadata = {
            ...errorContext.context,
            errorId: errorContext.errorId,
            retryable: errorContext.retryable,
            retryCount: errorContext.retryCount,
            operation: errorContext.operation,
            ...errorContext.metadata
        };

        const level = errorContext.retryable && errorContext.retryCount && errorContext.retryCount > 3
            ? LogLevel.ERROR
            : LogLevel.WARN;

        this.logger.log({
            timestamp: errorContext.timestamp,
            level,
            message: errorContext.message,
            operation: errorContext.operation,
            metadata,
            error: errorContext.originalError,
            errorCode: errorContext.code,
            errorContext
        });
    }

    /**
     * Log a simple error
     */
    logError(message: string, error: Error, operation?: string, metadata?: Record<string, unknown>): void {
        this.logger.error(message, error, { operation, ...metadata });
    }

    /**
     * Log a fatal error
     */
    logFatal(message: string, error: Error, operation?: string, metadata?: Record<string, unknown>): void {
        this.logger.fatal(message, error, { operation, ...metadata });
    }
}

// ============================================================================
// API Logger - For API request/response logging
// ============================================================================

/**
 * Specialized logger for API request/response logging
 */
export class APILogger {
    private logger: Logger;
    private operation: string;

    /**
     * Create a new APILogger
     */
    constructor(logger: Logger, operation: string) {
        this.logger = logger;
        this.operation = operation;
    }

    /**
     * Log an API request
     */
    logRequest(url: string, method: string, headers?: Record<string, string>, body?: unknown): void {
        this.logger.debug(`API Request: ${method} ${url}`, {
            type: 'api_request',
            method,
            url,
            headers: this.maskHeaders(headers),
            body: this.maskBody(body)
        });
    }

    /**
     * Log an API response
     */
    logResponse(url: string, status: number, statusText: string, duration: number, body?: unknown): void {
        const level = status >= 400 ? LogLevel.WARN : LogLevel.INFO;

        this.logger.log({
            timestamp: getTimestamp(),
            level,
            message: `API Response: ${status} ${statusText}`,
            operation: this.operation,
            metadata: {
                type: 'api_response',
                url,
                status,
                statusText,
                duration,
                body: this.maskBody(body)
            },
            duration
        });
    }

    /**
     * Log an API error
     */
    logError(url: string, error: Error, metadata?: Record<string, unknown>): void {
        this.logger.error(`API Error: ${url}`, error, {
            type: 'api_error',
            url,
            ...metadata
        });
    }

    /**
     * Log rate limiting
     */
    logRateLimit(url: string, retryAfter?: number): void {
        this.logger.warn(`Rate limited: ${url}`, {
            type: 'rate_limit',
            url,
            retryAfter
        });
    }

    /**
     * Log retry attempt
     */
    logRetry(url: string, attempt: number, maxAttempts: number): void {
        this.logger.warn(`Retrying request: ${url}`, {
            type: 'retry',
            url,
            attempt,
            maxAttempts
        });
    }

    /**
     * Mask sensitive headers
     */
    private maskHeaders(headers?: Record<string, string>): Record<string, string> | undefined {
        if (!headers) return undefined;

        const sensitiveHeaders = ['authorization', 'x-api-key', 'cookie'];
        const masked: Record<string, string> = {};

        for (const [key, value] of Object.entries(headers)) {
            if (sensitiveHeaders.includes(key.toLowerCase())) {
                masked[key] = '****';
            } else {
                masked[key] = value;
            }
        }

        return masked;
    }

    /**
     * Mask sensitive data in request/response body
     */
    private maskBody(body?: unknown): unknown {
        if (!body) return undefined;

        if (typeof body === 'string') {
            return maskSensitiveData(body);
        }

        if (typeof body === 'object' && body !== null) {
            return maskObject(body as Record<string, unknown>);
        }

        return body;
    }
}

// ============================================================================
// Default Logger Instance
// ============================================================================

/**
 * Default logger instance for SEO engine
 */
export const seoLogger = new Logger({
    level: LogLevel.INFO,
    destination: ['console', 'file'],
    filePath: process.env.SEO_LOG_FILE || './logs/seo-engine.log',
    includeMetadata: true,
    maskSensitiveData: true,
    maxFileSize: 10 * 1024 * 1024,
    maxRotatedFiles: 5,
    retentionDays: 30,
    jsonFormat: process.env.SEO_LOG_JSON === 'true'
});

/**
 * Create a new operation logger
 */
export function createOperationLogger(operation: string): OperationLogger {
    return new OperationLogger(seoLogger, operation);
}

/**
 * Create a new error logger
 */
export function createErrorLogger(): ErrorLogger {
    return new ErrorLogger(seoLogger);
}

/**
 * Create a new API logger
 */
export function createAPILogger(operation: string): APILogger {
    return new APILogger(seoLogger, operation);
}

// ============================================================================
// Export all types and classes
// ============================================================================

export default {
    LogLevel,
    LOG_LEVEL_NAMES,
    Logger,
    OperationLogger,
    ErrorLogger,
    APILogger,
    seoLogger,
    createOperationLogger,
    createErrorLogger,
    createAPILogger,
    DEFAULT_LOGGER_CONFIG
};
