/**
 * SEO Engine Database Integration
 * 
 * Comprehensive database integration with connection pooling, SEO-specific
 * operations, query builders, and migration support.
 * 
 * @module seo/database
 */

// ============================================================================
// Imports
// ============================================================================

import {
    DatabaseError,
    DatabaseConnectionError,
    DatabaseQueryError,
    SEO_ERROR_CODES,
} from './errors';

import { Logger, LogLevel, LogEntry } from './logger';

import { retryDatabase } from './retry';

import { config, SEOConfig } from './config';

// ============================================================================
// Database Configuration
// ============================================================================

/**
 * Database connection pool settings
 */
export interface DatabasePoolConfig {
    /** Maximum number of connections in the pool */
    max: number;
    /** Minimum number of connections in the pool */
    min: number;
    /** Idle timeout in milliseconds */
    idleTimeoutMs: number;
    /** Connection timeout in milliseconds */
    connectionTimeoutMs: number;
    /** Maximum lifetime of a connection in milliseconds */
    maxLifetimeMs: number;
}

/**
 * SSL configuration for database connection
 */
export interface DatabaseSSLConfig {
    /** Whether SSL is enabled */
    enabled: boolean;
    /** SSL mode */
    mode?: 'require' | 'verify-ca' | 'verify-full';
    /** Path to CA certificate file */
    ca?: string;
    /** Path to client certificate file */
    cert?: string;
    /** Path to client key file */
    key?: string;
    /** Whether to reject unauthorized certificates */
    rejectUnauthorized?: boolean;
}

/**
 * Database configuration interface
 */
export interface DatabaseConfig {
    /** Database connection string */
    connectionString: string;
    /** Connection pool settings */
    pool: DatabasePoolConfig;
    /** SSL configuration */
    ssl: DatabaseSSLConfig;
    /** Maximum number of retry attempts for connection */
    maxRetries: number;
    /** Delay between retry attempts in milliseconds */
    retryDelayMs: number;
    /** Enable query logging */
    logQueries: boolean;
    /** Query timeout in milliseconds */
    queryTimeoutMs: number;
}

/**
 * Default database pool configuration
 */
export const DEFAULT_POOL_CONFIG: DatabasePoolConfig = {
    max: 20,
    min: 2,
    idleTimeoutMs: 30000,
    connectionTimeoutMs: 10000,
    maxLifetimeMs: 3600000,
};

/**
 * Default SSL configuration
 */
export const DEFAULT_SSL_CONFIG: DatabaseSSLConfig = {
    enabled: false,
    mode: 'require',
    rejectUnauthorized: false,
};

/**
 * Get database configuration from environment variables
 * 
 * @returns DatabaseConfig object
 */
export function getDatabaseConfig(): DatabaseConfig {
    const connectionString = process.env.DATABASE_URL || config.databaseUrl;

    if (!connectionString) {
        throw new Error('DATABASE_URL environment variable is not set');
    }

    return {
        connectionString,
        pool: {
            max: parseInt(process.env.DB_POOL_MAX || '20', 10),
            min: parseInt(process.env.DB_POOL_MIN || '2', 10),
            idleTimeoutMs: parseInt(process.env.DB_IDLE_TIMEOUT_MS || '30000', 10),
            connectionTimeoutMs: parseInt(process.env.DB_CONNECTION_TIMEOUT_MS || '10000', 10),
            maxLifetimeMs: parseInt(process.env.DB_MAX_LIFETIME_MS || '3600000', 10),
        },
        ssl: {
            enabled: process.env.DB_SSL_ENABLED === 'true',
            mode: (process.env.DB_SSL_MODE as DatabaseSSLConfig['mode']) || 'require',
            ca: process.env.DB_SSL_CA,
            cert: process.env.DB_SSL_CERT,
            key: process.env.DB_SSL_KEY,
            rejectUnauthorized: process.env.DB_SSL_REJECT_UNAUTHORIZED !== 'false',
        },
        maxRetries: parseInt(process.env.DB_MAX_RETRIES || '5', 10),
        retryDelayMs: parseInt(process.env.DB_RETRY_DELAY_MS || '1000', 10),
        logQueries: process.env.DB_LOG_QUERIES === 'true',
        queryTimeoutMs: parseInt(process.env.DB_QUERY_TIMEOUT_MS || '30000', 10),
    };
}

// ============================================================================
// Database Connection Management
// ============================================================================

/**
 * Database connection state
 */
export type DatabaseConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

/**
 * Database client interface (to be implemented with actual DB driver)
 */
export interface DatabaseClient {
    /** Query method */
    query<T = any>(sql: string, params?: any[]): Promise<QueryResult<T>>;
    /** Execute method (for non-select queries) */
    execute(sql: string, params?: any[]): Promise<ExecutionResult>;
    /** Begin transaction */
    begin(): Promise<void>;
    /** Commit transaction */
    commit(): Promise<void>;
    /** Rollback transaction */
    rollback(): Promise<void>;
    /** Close connection */
    close(): Promise<void>;
}

/**
 * Query result interface
 */
export interface QueryResult<T = any> {
    /** Array of rows */
    rows: T[];
    /** Number of rows affected */
    rowCount: number;
    /** Column names */
    fields: FieldInfo[];
}

/**
 * Execution result interface
 */
export interface ExecutionResult {
    /** Number of rows affected */
    rowCount: number;
    /** Last inserted ID (if applicable) */
    lastInsertId?: string;
}

/**
 * Field information
 */
export interface FieldInfo {
    name: string;
    dataTypeID: number;
}

/**
 * Database connection manager
 */
export class DatabaseConnection {
    private config: DatabaseConfig;
    private logger: Logger;
    private state: DatabaseConnectionState = 'disconnected';
    private client: DatabaseClient | null = null;
    private reconnectAttempts = 0;

    /**
     * Create a new database connection
     * 
     * @param config - Database configuration
     * @param logger - Logger instance
     */
    constructor(config: DatabaseConfig, logger: Logger) {
        this.config = config;
        this.logger = logger;
    }

    /**
     * Get current connection state
     */
    getState(): DatabaseConnectionState {
        return this.state;
    }

    /**
     * Get the underlying client
     */
    getClient(): DatabaseClient | null {
        return this.client;
    }

    /**
     * Connect to the database
     */
    async connect(): Promise<void> {
        if (this.state === 'connected' && this.client) {
            return;
        }

        this.state = 'connecting';
        this.logger.info('Connecting to database', {
            operation: 'database:connect',
            metadata: {
                host: this.getHostFromConnectionString(),
            },
        });

        try {
            // In a real implementation, this would use pg or another database driver
            // For now, we create a mock client that can be replaced with actual implementation
            this.client = await this.createClient();

            // Test the connection
            await this.healthCheck();

            this.state = 'connected';
            this.reconnectAttempts = 0;

            this.logger.info('Database connected successfully', {
                operation: 'database:connect',
                metadata: {
                    host: this.getHostFromConnectionString(),
                },
            });
        } catch (error) {
            this.state = 'error';
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';

            this.logger.error(`Database connection failed: ${errorMessage}`, {
                operation: 'database:connect',
                error: error as Error,
            });

            throw new DatabaseConnectionError(
                `Failed to connect to database: ${errorMessage}`,
                { originalError: error as Error }
            );
        }
    }

    /**
     * Disconnect from the database
     */
    async disconnect(): Promise<void> {
        if (!this.client) {
            return;
        }

        try {
            await this.client.close();
            this.client = null;
            this.state = 'disconnected';

            this.logger.info('Database disconnected', {
                operation: 'database:disconnect',
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';

            this.logger.error(`Error disconnecting from database: ${errorMessage}`, {
                operation: 'database:disconnect',
                error: error as Error,
            });

            throw new DatabaseConnectionError(
                `Error disconnecting from database: ${errorMessage}`,
                { originalError: error as Error }
            );
        }
    }

    /**
     * Perform health check on the database connection
     */
    async healthCheck(): Promise<boolean> {
        if (!this.client) {
            throw new DatabaseConnectionError('No active database connection');
        }

        try {
            const result = await this.client.query('SELECT 1 as health_check');
            return result.rows.length > 0 && result.rows[0].health_check === 1;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';

            this.logger.error(`Database health check failed: ${errorMessage}`, {
                operation: 'database:health-check',
                error: error as Error,
            });

            return false;
        }
    }

    /**
     * Attempt to reconnect to the database
     */
    async reconnect(): Promise<void> {
        if (this.reconnectAttempts >= this.config.maxRetries) {
            throw new DatabaseConnectionError(
                `Maximum reconnection attempts (${this.config.maxRetries}) exceeded`
            );
        }

        this.reconnectAttempts++;

        this.logger.warn(`Attempting to reconnect (attempt ${this.reconnectAttempts}/${this.config.maxRetries})`, {
            operation: 'database:reconnect',
            metadata: {
                attempt: this.reconnectAttempts,
                maxAttempts: this.config.maxRetries,
            },
        });

        await this.disconnect();

        // Wait before reconnecting
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelayMs));

        await this.connect();
    }

    /**
     * Execute a query with retry logic
     */
    async query<T = any>(sql: string, params?: any[]): Promise<QueryResult<T>> {
        if (!this.client) {
            await this.connect();
        }

        const startTime = Date.now();

        try {
            // Use retry logic for database operations
            const result = await retryDatabase(
                async () => {
                    if (!this.client) {
                        throw new DatabaseConnectionError('No active database connection');
                    }
                    return this.client.query<T>(sql, params);
                },
                {
                    maxRetries: 3,
                },
                'database:query'
            );

            const duration = Date.now() - startTime;

            if (this.config.logQueries) {
                this.logger.debug(`Query executed`, {
                    operation: 'database:query',
                    metadata: {
                        sql: this.sanitizeSql(sql),
                        params: this.sanitizeParams(params),
                        duration,
                        rowCount: result.rowCount,
                    },
                });
            }

            return result;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            const duration = Date.now() - startTime;

            this.logger.error(`Query failed: ${errorMessage}`, {
                operation: 'database:query',
                error: error as Error,
                metadata: {
                    sql: this.sanitizeSql(sql),
                    params: this.sanitizeParams(params),
                    duration,
                },
            });

            throw new DatabaseQueryError(
                `Query failed: ${errorMessage}`,
                {
                    sql: this.sanitizeSql(sql),
                    retryable: this.isRetryableError(error),
                }
            );
        }
    }

    /**
     * Execute a non-select query
     */
    async execute(sql: string, params?: any[]): Promise<ExecutionResult> {
        if (!this.client) {
            await this.connect();
        }

        const startTime = Date.now();

        try {
            const result = await retryDatabase(
                async () => {
                    if (!this.client) {
                        throw new DatabaseConnectionError('No active database connection');
                    }
                    return this.client.execute(sql, params);
                },
                {
                    maxRetries: 3,
                },
                'database:execute'
            );

            const duration = Date.now() - startTime;

            if (this.config.logQueries) {
                this.logger.debug(`Execute completed`, {
                    operation: 'database:execute',
                    metadata: {
                        sql: this.sanitizeSql(sql),
                        params: this.sanitizeParams(params),
                        duration,
                        rowCount: result.rowCount,
                    },
                });
            }

            return result;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            const duration = Date.now() - startTime;

            this.logger.error(`Execute failed: ${errorMessage}`, {
                operation: 'database:execute',
                error: error as Error,
                metadata: {
                    sql: this.sanitizeSql(sql),
                    params: this.sanitizeParams(params),
                    duration,
                },
            });

            throw new DatabaseQueryError(
                `Execute failed: ${errorMessage}`,
                {
                    sql: this.sanitizeSql(sql),
                    retryable: this.isRetryableError(error),
                }
            );
        }
    }

    /**
     * Execute a transaction
     */
    async transaction<T>(fn: () => Promise<T>): Promise<T> {
        if (!this.client) {
            await this.connect();
        }

        if (!this.client) {
            throw new DatabaseConnectionError('No active database connection');
        }

        try {
            await this.client.begin();

            const result = await fn();

            await this.client.commit();

            return result;
        } catch (error) {
            await this.client.rollback();

            const errorMessage = error instanceof Error ? error.message : 'Unknown error';

            this.logger.error(`Transaction failed: ${errorMessage}`, {
                operation: 'database:transaction',
                error: error as Error,
            });

            throw new DatabaseError(
                `Transaction failed: ${errorMessage}`,
                {
                    operation: 'transaction',
                    retryable: this.isRetryableError(error),
                }
            );
        }
    }

    /**
     * Create a database client
     */
    private async createClient(): Promise<DatabaseClient> {
        const ssl = this.config.ssl.enabled
            ? {
                rejectUnauthorized: this.config.ssl.rejectUnauthorized ?? false,
                ...(this.config.ssl.ca ? { ca: this.config.ssl.ca } : {}),
                ...(this.config.ssl.cert ? { cert: this.config.ssl.cert } : {}),
                ...(this.config.ssl.key ? { key: this.config.ssl.key } : {}),
            }
            : undefined;

        const pool = new Pool({
            connectionString: this.config.connectionString,
            max: this.config.pool.max,
            min: this.config.pool.min,
            idleTimeoutMillis: this.config.pool.idleTimeoutMs,
            connectionTimeoutMillis: this.config.pool.connectionTimeoutMs,
            maxLifetimeSeconds: Math.max(1, Math.floor(this.config.pool.maxLifetimeMs / 1000)),
            statement_timeout: this.config.queryTimeoutMs,
            ssl,
        });

        let transactionClient: PoolClient | null = null;

        const query = async <T>(sql: string, params?: any[]): Promise<QueryResult<T>> => {
            const result = transactionClient
                ? await transactionClient.query<T>(sql, params)
                : await pool.query<T>(sql, params);

            return {
                rows: result.rows,
                rowCount: result.rowCount ?? result.rows.length,
                fields: result.fields.map(field => ({
                    name: field.name,
                    dataTypeID: field.dataTypeID,
                })),
            };
        };

        return {
            query,
            execute: async (sql: string, params?: any[]): Promise<ExecutionResult> => {
                const result = transactionClient
                    ? await transactionClient.query(sql, params)
                    : await pool.query(sql, params);

                return {
                    rowCount: result.rowCount ?? 0,
                };
            },
            begin: async (): Promise<void> => {
                if (transactionClient) {
                    return;
                }

                transactionClient = await pool.connect();
                await transactionClient.query('BEGIN');
            },
            commit: async (): Promise<void> => {
                if (!transactionClient) {
                    return;
                }

                try {
                    await transactionClient.query('COMMIT');
                } finally {
                    transactionClient.release();
                    transactionClient = null;
                }
            },
            rollback: async (): Promise<void> => {
                if (!transactionClient) {
                    return;
                }

                try {
                    await transactionClient.query('ROLLBACK');
                } finally {
                    transactionClient.release();
                    transactionClient = null;
                }
            },
            close: async (): Promise<void> => {
                if (transactionClient) {
                    try {
                        await transactionClient.query('ROLLBACK');
                    } catch {
                        // Ignore rollback errors during shutdown.
                    } finally {
                        transactionClient.release();
                        transactionClient = null;
                    }
                }

                await pool.end();
            },
        };
    }

    /**
     * Extract host from connection string
     */
    private getHostFromConnectionString(): string {
        try {
            const url = new URL(this.config.connectionString);
            return url.hostname;
        } catch {
            return 'unknown';
        }
    }

    /**
     * Sanitize SQL for logging (remove sensitive parts)
     */
    private sanitizeSql(sql: string): string {
        // Remove potentially sensitive content
        return sql
            .replace(/password\s*=\s*'[^']*'/gi, "password='***'")
            .replace(/password\s*=\s*[^&\s]*/gi, 'password=***')
            .substring(0, 500); // Limit length
    }

    /**
     * Sanitize parameters for logging
     */
    private sanitizeParams(params?: any[]): any[] | undefined {
        if (!params) {
            return undefined;
        }

        return params.map(param => {
            if (typeof param === 'string' && param.length > 100) {
                return param.substring(0, 100) + '...';
            }
            return param;
        });
    }

    /**
     * Check if error is retryable
     */
    private isRetryableError(error: unknown): boolean {
        if (error instanceof Error) {
            const retryablePatterns = [
                'connection',
                'timeout',
                'network',
                'ECONNREFUSED',
                'ETIMEDOUT',
            ];

            return retryablePatterns.some(pattern =>
                error.message.toLowerCase().includes(pattern.toLowerCase())
            );
        }

        return false;
    }
}

// ============================================================================
// SEO-Specific Database Operations
// ============================================================================

/**
 * SEO Job status
 */
export type SEOJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * SEO Job type
 */
export type SEOJobType = 'content_generation' | 'indexing_submission' | 'ranking_check' | 'competitor_analysis' | 'audit';

/**
 * SEO Job record
 */
export interface SEOJob {
    id: string;
    type: SEOJobType;
    status: SEOJobStatus;
    priority: number;
    payload: Record<string, any>;
    result?: Record<string, any>;
    error?: string;
    started_at?: string;
    completed_at?: string;
    created_at: string;
    updated_at: string;
}

/**
 * SEO Progress record
 */
export interface SEOProgress {
    id: string;
    job_id: string;
    stage: string;
    progress: number;
    message?: string;
    metadata?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

/**
 * SEO Log level
 */
export type SEOLogLevel = 'debug' | 'info' | 'warn' | 'error';

/**
 * SEO Log record
 */
export interface SEOLog {
    id: string;
    job_id?: string;
    level: SEOLogLevel;
    message: string;
    operation?: string;
    metadata?: Record<string, any>;
    created_at: string;
}

/**
 * SEO Metrics record
 */
export interface SEOMetrics {
    id: string;
    job_id?: string;
    metric_name: string;
    metric_value: number;
    metric_unit?: string;
    metadata?: Record<string, any>;
    recorded_at: string;
}

/**
 * URL tracking record
 */
export interface URLRecord {
    id: string;
    url: string;
    status: 'pending' | 'submitted' | 'indexed' | 'error';
    last_checked?: string;
    index_status?: string;
    metadata?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

/**
 * SEO Database operations
 */
export class SEODatabase {
    private connection: DatabaseConnection;
    private logger: Logger;

    /**
     * Create SEO database operations instance
     * 
     * @param connection - Database connection
     * @param logger - Logger instance
     */
    constructor(connection: DatabaseConnection, logger: Logger) {
        this.connection = connection;
        this.logger = logger;
    }

    // =========================================================================
    // SEO Job Operations
    // =========================================================================

    /**
     * Create a new SEO job
     * 
     * @param job - Job data
     * @returns Created job
     */
    async createJob(job: Omit<SEOJob, 'id' | 'created_at' | 'updated_at'>): Promise<SEOJob> {
        const id = this.generateId();
        const now = new Date().toISOString();

        const sql = `
            INSERT INTO seo_jobs (id, type, status, priority, payload, result, error, started_at, completed_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        `;

        const params = [
            id,
            job.type,
            job.status,
            job.priority,
            JSON.stringify(job.payload),
            job.result ? JSON.stringify(job.result) : null,
            job.error || null,
            job.started_at || null,
            job.completed_at || null,
            now,
            now,
        ];

        const result = await this.connection.query<SEOJob>(sql, params);

        this.logger.debug('SEO job created', {
            operation: 'seo:create-job',
            metadata: { jobId: id, type: job.type },
        });

        return result.rows[0];
    }

    /**
     * Get SEO job by ID
     * 
     * @param id - Job ID
     * @returns Job or null if not found
     */
    async getJob(id: string): Promise<SEOJob | null> {
        const sql = 'SELECT * FROM seo_jobs WHERE id = $1';
        const result = await this.connection.query<SEOJob>(sql, [id]);

        return result.rows[0] || null;
    }

    /**
     * Get jobs by status
     * 
     * @param status - Job status
     * @param limit - Maximum number of jobs to return
     * @returns Array of jobs
     */
    async getJobsByStatus(status: SEOJobStatus, limit: number = 100): Promise<SEOJob[]> {
        const sql = `
            SELECT * FROM seo_jobs 
            WHERE status = $1 
            ORDER BY priority DESC, created_at ASC 
            LIMIT $2
        `;

        const result = await this.connection.query<SEOJob>(sql, [status, limit]);

        return result.rows;
    }

    /**
     * Get pending jobs
     * 
     * @param limit - Maximum number of jobs to return
     * @param types - Optional job types to filter
     * @returns Array of pending jobs
     */
    async getPendingJobs(limit: number = 10, types?: SEOJobType[]): Promise<SEOJob[]> {
        let sql = `
            SELECT * FROM seo_jobs 
            WHERE status = 'pending'
        `;

        const params: any[] = [];

        if (types && types.length > 0) {
            sql += ` AND type = ANY($${params.length + 1})`;
            params.push(types);
        }

        sql += ` ORDER BY priority DESC, created_at ASC LIMIT $${params.length + 1}`;
        params.push(limit);

        const result = await this.connection.query<SEOJob>(sql, params);

        return result.rows;
    }

    /**
     * Update SEO job
     * 
     * @param id - Job ID
     * @param updates - Fields to update
     * @returns Updated job
     */
    async updateJob(id: string, updates: Partial<SEOJob>): Promise<SEOJob> {
        const fields: string[] = [];
        const values: any[] = [];
        let paramIndex = 1;

        if (updates.status !== undefined) {
            fields.push(`status = $${paramIndex++}`);
            values.push(updates.status);
        }

        if (updates.result !== undefined) {
            fields.push(`result = $${paramIndex++}`);
            values.push(JSON.stringify(updates.result));
        }

        if (updates.error !== undefined) {
            fields.push(`error = $${paramIndex++}`);
            values.push(updates.error);
        }

        if (updates.started_at !== undefined) {
            fields.push(`started_at = $${paramIndex++}`);
            values.push(updates.started_at);
        }

        if (updates.completed_at !== undefined) {
            fields.push(`completed_at = $${paramIndex++}`);
            values.push(updates.completed_at);
        }

        fields.push(`updated_at = $${paramIndex++}`);
        values.push(new Date().toISOString());

        values.push(id);

        const sql = `
            UPDATE seo_jobs 
            SET ${fields.join(', ')}
            WHERE id = $${paramIndex}
            RETURNING *
        `;

        const result = await this.connection.query<SEOJob>(sql, values);

        if (result.rows.length === 0) {
            throw new DatabaseQueryError(`Job not found: ${id}`, { table: 'seo_jobs' });
        }

        return result.rows[0];
    }

    /**
     * Delete SEO job
     * 
     * @param id - Job ID
     */
    async deleteJob(id: string): Promise<void> {
        const sql = 'DELETE FROM seo_jobs WHERE id = $1';
        await this.connection.execute(sql, [id]);

        this.logger.debug('SEO job deleted', {
            operation: 'seo:delete-job',
            metadata: { jobId: id },
        });
    }

    // =========================================================================
    // SEO Progress Operations
    // =========================================================================

    /**
     * Create progress record
     * 
     * @param progress - Progress data
     * @returns Created progress record
     */
    async createProgress(progress: Omit<SEOProgress, 'id' | 'created_at' | 'updated_at'>): Promise<SEOProgress> {
        const id = this.generateId();
        const now = new Date().toISOString();

        const sql = `
            INSERT INTO seo_progress (id, job_id, stage, progress, message, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        `;

        const params = [
            id,
            progress.job_id,
            progress.stage,
            progress.progress,
            progress.message || null,
            progress.metadata ? JSON.stringify(progress.metadata) : null,
            now,
            now,
        ];

        const result = await this.connection.query<SEOProgress>(sql, params);

        return result.rows[0];
    }

    /**
     * Get progress by job ID
     * 
     * @param jobId - Job ID
     * @returns Array of progress records
     */
    async getProgressByJob(jobId: string): Promise<SEOProgress[]> {
        const sql = `
            SELECT * FROM seo_progress 
            WHERE job_id = $1 
            ORDER BY created_at ASC
        `;

        const result = await this.connection.query<SEOProgress>(sql, [jobId]);

        return result.rows;
    }

    /**
     * Update progress
     * 
     * @param jobId - Job ID
     * @param stage - Stage name
     * @param progress - Progress percentage (0-100)
     * @param message - Optional message
     * @param metadata - Optional metadata
     * @returns Updated progress record
     */
    async updateProgress(
        jobId: string,
        stage: string,
        progress: number,
        message?: string,
        metadata?: Record<string, any>
    ): Promise<SEOProgress> {
        const now = new Date().toISOString();

        // Try to update existing record
        const updateSql = `
            UPDATE seo_progress 
            SET progress = $1, message = $2, metadata = $3, updated_at = $4
            WHERE job_id = $5 AND stage = $6
            RETURNING *
        `;

        let result = await this.connection.query<SEOProgress>(updateSql, [
            progress,
            message || null,
            metadata ? JSON.stringify(metadata) : null,
            now,
            jobId,
            stage,
        ]);

        // If no record exists, create one
        if (result.rows.length === 0) {
            return this.createProgress({ job_id: jobId, stage, progress, message, metadata });
        }

        return result.rows[0];
    }

    // =========================================================================
    // SEO Log Operations
    // =========================================================================

    /**
     * Create log entry
     * 
     * @param log - Log data
     * @returns Created log entry
     */
    async createLog(log: Omit<SEOLog, 'id' | 'created_at'>): Promise<SEOLog> {
        const id = this.generateId();
        const now = new Date().toISOString();

        const sql = `
            INSERT INTO seo_logs (id, job_id, level, message, operation, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        `;

        const params = [
            id,
            log.job_id || null,
            log.level,
            log.message,
            log.operation || null,
            log.metadata ? JSON.stringify(log.metadata) : null,
            now,
        ];

        const result = await this.connection.query<SEOLog>(sql, params);

        return result.rows[0];
    }

    /**
     * Get logs by job ID
     * 
     * @param jobId - Job ID
     * @param limit - Maximum number of logs to return
     * @returns Array of log entries
     */
    async getLogsByJob(jobId: string, limit: number = 1000): Promise<SEOLog[]> {
        const sql = `
            SELECT * FROM seo_logs 
            WHERE job_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        `;

        const result = await this.connection.query<SEOLog>(sql, [jobId, limit]);

        return result.rows;
    }

    /**
     * Get logs by level
     * 
     * @param level - Log level
     * @param limit - Maximum number of logs to return
     * @param since - Optional start time
     * @returns Array of log entries
     */
    async getLogsByLevel(
        level: SEOLogLevel,
        limit: number = 1000,
        since?: string
    ): Promise<SEOLog[]> {
        let sql = `
            SELECT * FROM seo_logs 
            WHERE level = $1
        `;

        const params: any[] = [level];

        if (since) {
            sql += ` AND created_at >= $2`;
            params.push(since);
        }

        sql += ` ORDER BY created_at DESC LIMIT $${params.length + 1}`;
        params.push(limit);

        const result = await this.connection.query<SEOLog>(sql, params);

        return result.rows;
    }

    // =========================================================================
    // SEO Metrics Operations
    // =========================================================================

    /**
     * Create metrics record
     * 
     * @param metrics - Metrics data
     * @returns Created metrics record
     */
    async createMetrics(metrics: Omit<SEOMetrics, 'id'>): Promise<SEOMetrics> {
        const id = this.generateId();

        const sql = `
            INSERT INTO seo_metrics (id, job_id, metric_name, metric_value, metric_unit, metadata, recorded_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        `;

        const params = [
            id,
            metrics.job_id || null,
            metrics.metric_name,
            metrics.metric_value,
            metrics.metric_unit || null,
            metrics.metadata ? JSON.stringify(metrics.metadata) : null,
            metrics.recorded_at,
        ];

        const result = await this.connection.query<SEOMetrics>(sql, params);

        return result.rows[0];
    }

    /**
     * Create multiple metrics in batch
     * 
     * @param metrics - Array of metrics data
     * @returns Number of records created
     */
    async createMetricsBatch(metrics: Omit<SEOMetrics, 'id'>[]): Promise<number> {
        if (metrics.length === 0) {
            return 0;
        }

        const values: string[] = [];
        const params: any[] = [];
        let paramIndex = 1;

        for (const metric of metrics) {
            const id = this.generateId();

            values.push(
                `($${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++})`
            );

            params.push(
                id,
                metric.job_id || null,
                metric.metric_name,
                metric.metric_value,
                metric.metric_unit || null,
                metric.metadata ? JSON.stringify(metric.metadata) : null,
                metric.recorded_at
            );
        }

        const sql = `
            INSERT INTO seo_metrics (id, job_id, metric_name, metric_value, metric_unit, metadata, recorded_at)
            VALUES ${values.join(', ')}
        `;

        const result = await this.connection.execute(sql, params);

        return result.rowCount;
    }

    /**
     * Get metrics by job ID
     * 
     * @param jobId - Job ID
     * @returns Array of metrics records
     */
    async getMetricsByJob(jobId: string): Promise<SEOMetrics[]> {
        const sql = `
            SELECT * FROM seo_metrics 
            WHERE job_id = $1 
            ORDER BY recorded_at DESC
        `;

        const result = await this.connection.query<SEOMetrics>(sql, [jobId]);

        return result.rows;
    }

    /**
     * Get metrics by name
     * 
     * @param metricName - Metric name
     * @param since - Optional start time
     * @param until - Optional end time
     * @returns Array of metrics records
     */
    async getMetricsByName(
        metricName: string,
        since?: string,
        until?: string
    ): Promise<SEOMetrics[]> {
        let sql = `
            SELECT * FROM seo_metrics 
            WHERE metric_name = $1
        `;

        const params: any[] = [metricName];

        if (since) {
            sql += ` AND recorded_at >= $${params.length + 1}`;
            params.push(since);
        }

        if (until) {
            sql += ` AND recorded_at <= $${params.length + 1}`;
            params.push(until);
        }

        sql += ` ORDER BY recorded_at DESC`;

        const result = await this.connection.query<SEOMetrics>(sql, params);

        return result.rows;
    }

    // =========================================================================
    // URL Tracking Operations
    // =========================================================================

    /**
     * Create URL record
     * 
     * @param url - URL data
     * @returns Created URL record
     */
    async createURL(url: Omit<URLRecord, 'id' | 'created_at' | 'updated_at'>): Promise<URLRecord> {
        const id = this.generateId();
        const now = new Date().toISOString();

        const sql = `
            INSERT INTO seo_urls (id, url, status, last_checked, index_status, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        `;

        const params = [
            id,
            url.url,
            url.status,
            url.last_checked || null,
            url.index_status || null,
            url.metadata ? JSON.stringify(url.metadata) : null,
            now,
            now,
        ];

        const result = await this.connection.query<URLRecord>(sql, params);

        this.logger.debug('URL record created', {
            operation: 'seo:create-url',
            metadata: { url: url.url },
        });

        return result.rows[0];
    }

    /**
     * Get URL by ID
     * 
     * @param id - URL ID
     * @returns URL record or null
     */
    async getURL(id: string): Promise<URLRecord | null> {
        const sql = 'SELECT * FROM seo_urls WHERE id = $1';
        const result = await this.connection.query<URLRecord>(sql, [id]);

        return result.rows[0] || null;
    }

    /**
     * Get URL by address
     * 
     * @param url - URL address
     * @returns URL record or null
     */
    async getURLByAddress(url: string): Promise<URLRecord | null> {
        const sql = 'SELECT * FROM seo_urls WHERE url = $1';
        const result = await this.connection.query<URLRecord>(sql, [url]);

        return result.rows[0] || null;
    }

    /**
     * Get URLs by status
     * 
     * @param status - URL status
     * @param limit - Maximum number of URLs to return
     * @returns Array of URL records
     */
    async getURLsByStatus(status: URLRecord['status'], limit: number = 100): Promise<URLRecord[]> {
        const sql = `
            SELECT * FROM seo_urls 
            WHERE status = $1 
            ORDER BY created_at ASC 
            LIMIT $2
        `;

        const result = await this.connection.query<URLRecord>(sql, [status, limit]);

        return result.rows;
    }

    /**
     * Update URL record
     * 
     * @param id - URL ID
     * @param updates - Fields to update
     * @returns Updated URL record
     */
    async updateURL(id: string, updates: Partial<URLRecord>): Promise<URLRecord> {
        const fields: string[] = [];
        const values: any[] = [];
        let paramIndex = 1;

        if (updates.status !== undefined) {
            fields.push(`status = $${paramIndex++}`);
            values.push(updates.status);
        }

        if (updates.last_checked !== undefined) {
            fields.push(`last_checked = $${paramIndex++}`);
            values.push(updates.last_checked);
        }

        if (updates.index_status !== undefined) {
            fields.push(`index_status = $${paramIndex++}`);
            values.push(updates.index_status);
        }

        if (updates.metadata !== undefined) {
            fields.push(`metadata = $${paramIndex++}`);
            values.push(JSON.stringify(updates.metadata));
        }

        fields.push(`updated_at = $${paramIndex++}`);
        values.push(new Date().toISOString());

        values.push(id);

        const sql = `
            UPDATE seo_urls 
            SET ${fields.join(', ')}
            WHERE id = $${paramIndex}
            RETURNING *
        `;

        const result = await this.connection.query<URLRecord>(sql, values);

        if (result.rows.length === 0) {
            throw new DatabaseQueryError(`URL not found: ${id}`, { table: 'seo_urls' });
        }

        return result.rows[0];
    }

    /**
     * Delete URL record
     * 
     * @param id - URL ID
     */
    async deleteURL(id: string): Promise<void> {
        const sql = 'DELETE FROM seo_urls WHERE id = $1';
        await this.connection.execute(sql, [id]);
    }

    /**
     * Create or update a URL record by URL address.
     *
     * @param url - URL data
     * @returns Upserted URL record
     */
    async upsertURL(url: Omit<URLRecord, 'id' | 'created_at' | 'updated_at'>): Promise<URLRecord> {
        const existing = await this.getURLByAddress(url.url);

        if (!existing) {
            return this.createURL(url);
        }

        return this.updateURL(existing.id, {
            status: url.status,
            last_checked: url.last_checked ?? existing.last_checked,
            index_status: url.index_status ?? existing.index_status,
            metadata: {
                ...(existing.metadata || {}),
                ...(url.metadata || {}),
            },
        });
    }

    // =========================================================================
    // Helper Methods
    // =========================================================================

    /**
     * Generate unique ID
     */
    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    }
}

// ============================================================================
// Query Builders
// ============================================================================

/**
 * Query builder for safe SQL construction
 */
export class QueryBuilder {
    private tableName: string;
    private conditions: string[] = [];
    private params: any[] = [];
    private orderBy: string[] = [];
    private limitValue?: number;
    private offsetValue?: number;
    private selectedFields: string[] = ['*'];

    /**
     * Create a new query builder
     * 
     * @param tableName - Table name
     */
    constructor(tableName: string) {
        this.tableName = this.sanitizeIdentifier(tableName);
    }

    /**
     * Select fields
     * 
     * @param fields - Field names
     */
    select(fields: string[]): this {
        this.selectedFields = fields.map(f => this.sanitizeIdentifier(f));
        return this;
    }

    /**
     * Add WHERE condition
     * 
     * @param condition - Condition string
     * @param params - Parameters for the condition
     */
    where(condition: string, params?: any[]): this {
        this.conditions.push(condition);
        if (params) {
            this.params.push(...params);
        }
        return this;
    }

    /**
     * Add equals condition
     * 
     * @param field - Field name
     * @param value - Value
     */
    equals(field: string, value: any): this {
        const paramIndex = this.params.length + 1;
        this.conditions.push(`${this.sanitizeIdentifier(field)} = $${paramIndex}`);
        this.params.push(value);
        return this;
    }

    /**
     * Add IN condition
     * 
     * @param field - Field name
     * @param values - Array of values
     */
    in(field: string, values: any[]): this {
        if (values.length === 0) {
            return this;
        }

        const placeholders = values.map((_, i) => `$${this.params.length + i + 1}`).join(', ');
        this.conditions.push(`${this.sanitizeIdentifier(field)} IN (${placeholders})`);
        this.params.push(...values);
        return this;
    }

    /**
     * Add LIKE condition
     * 
     * @param field - Field name
     * @param pattern - Pattern
     */
    like(field: string, pattern: string): this {
        const paramIndex = this.params.length + 1;
        this.conditions.push(`${this.sanitizeIdentifier(field)} LIKE $${paramIndex}`);
        this.params.push(pattern);
        return this;
    }

    /**
     * Add ORDER BY clause
     * 
     * @param field - Field name
     * @param direction - Sort direction
     */
    orderByField(field: string, direction: 'ASC' | 'DESC' = 'ASC'): this {
        this.orderBy.push(`${this.sanitizeIdentifier(field)} ${direction}`);
        return this;
    }

    /**
     * Add LIMIT
     * 
     * @param limit - Limit value
     */
    limit(limit: number): this {
        this.limitValue = limit;
        return this;
    }

    /**
     * Add OFFSET
     * 
     * @param offset - Offset value
     */
    offset(offset: number): this {
        this.offsetValue = offset;
        return this;
    }

    /**
     * Build SELECT query
     */
    toSelect(): { sql: string; params: any[] } {
        let sql = `SELECT ${this.selectedFields.join(', ')} FROM ${this.tableName}`;

        if (this.conditions.length > 0) {
            sql += ` WHERE ${this.conditions.join(' AND ')}`;
        }

        if (this.orderBy.length > 0) {
            sql += ` ORDER BY ${this.orderBy.join(', ')}`;
        }

        if (this.limitValue !== undefined) {
            sql += ` LIMIT $${this.params.length + 1}`;
            this.params.push(this.limitValue);
        }

        if (this.offsetValue !== undefined) {
            sql += ` OFFSET $${this.params.length + 1}`;
            this.params.push(this.offsetValue);
        }

        return { sql, params: this.params };
    }

    /**
     * Build COUNT query
     */
    toCount(): { sql: string; params: any[] } {
        let sql = `SELECT COUNT(*) as count FROM ${this.tableName}`;

        if (this.conditions.length > 0) {
            sql += ` WHERE ${this.conditions.join(' AND ')}`;
        }

        return { sql, params: this.params };
    }

    /**
     * Sanitize identifier to prevent SQL injection
     */
    private sanitizeIdentifier(identifier: string): string {
        // Only allow alphanumeric characters, underscores, and dots (for table.field)
        if (!/^[a-zA-Z_][a-zA-Z0-9_.*]*$/.test(identifier)) {
            throw new Error(`Invalid identifier: ${identifier}`);
        }
        return identifier;
    }
}

/**
 * Create a safe parameterized query
 * 
 * @param sql - SQL template
 * @param params - Parameters
 * @returns Object with sql and params
 */
export function createParameterizedQuery(sql: string, params: any[]): { sql: string; params: any[] } {
    return { sql, params };
}

// ============================================================================
// Migration Support
// ============================================================================

/**
 * Schema version record
 */
export interface SchemaVersion {
    version: string;
    applied_at: string;
    description: string;
}

/**
 * Migration runner
 */
export class MigrationRunner {
    private connection: DatabaseConnection;
    private logger: Logger;

    /**
     * Create migration runner
     * 
     * @param connection - Database connection
     * @param logger - Logger instance
     */
    constructor(connection: DatabaseConnection, logger: Logger) {
        this.connection = connection;
        this.logger = logger;
    }

    /**
     * Get current schema version
     * 
     * @returns Current version or null if not initialized
     */
    async getCurrentVersion(): Promise<string | null> {
        try {
            const sql = 'SELECT version FROM schema_versions ORDER BY applied_at DESC LIMIT 1';
            const result = await this.connection.query<SchemaVersion>(sql);

            return result.rows[0]?.version || null;
        } catch (error) {
            // Table might not exist
            return null;
        }
    }

    /**
     * Apply migration
     * 
     * @param version - Version string
     * @param description - Migration description
     * @param sql - Migration SQL
     */
    async applyMigration(version: string, description: string, sql: string): Promise<void> {
        this.logger.info(`Applying migration: ${version}`, {
            operation: 'migration:apply',
            metadata: { version, description },
        });

        await this.connection.transaction(async () => {
            // Execute migration SQL
            await this.connection.execute(sql);

            // Record the migration
            const insertSql = `
                INSERT INTO schema_versions (version, applied_at, description)
                VALUES ($1, $2, $3)
            `;

            await this.connection.execute(insertSql, [version, new Date().toISOString(), description]);
        });

        this.logger.info(`Migration applied: ${version}`, {
            operation: 'migration:apply',
            metadata: { version },
        });
    }

    /**
     * Run all pending migrations
     * 
     * @param migrations - Array of migration definitions
     */
    async runMigrations(migrations: MigrationDefinition[]): Promise<void> {
        const currentVersion = await this.getCurrentVersion();

        for (const migration of migrations) {
            if (!currentVersion || this.compareVersions(migration.version, currentVersion) > 0) {
                await this.applyMigration(migration.version, migration.description, migration.sql);
            }
        }
    }

    /**
     * Compare semantic versions
     * 
     * @param a - Version A
     * @param b - Version B
     * @returns 1 if A > B, -1 if A < B, 0 if equal
     */
    private compareVersions(a: string, b: string): number {
        const partsA = a.split('.').map(Number);
        const partsB = b.split('.').map(Number);

        for (let i = 0; i < Math.max(partsA.length, partsB.length); i++) {
            const partA = partsA[i] || 0;
            const partB = partsB[i] || 0;

            if (partA > partB) return 1;
            if (partA < partB) return -1;
        }

        return 0;
    }
}

/**
 * Migration definition
 */
export interface MigrationDefinition {
    version: string;
    description: string;
    sql: string;
}

/**
 * Get SEO engine migrations
 * 
 * @returns Array of migration definitions
 */
export function getSEOMigrations(): MigrationDefinition[] {
    return [
        {
            version: '001',
            description: 'Create SEO tables',
            sql: `
                -- SEO Jobs table
                CREATE TABLE IF NOT EXISTS seo_jobs (
                    id VARCHAR(255) PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    priority INTEGER NOT NULL DEFAULT 0,
                    payload JSONB NOT NULL,
                    result JSONB,
                    error TEXT,
                    started_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- SEO Progress table
                CREATE TABLE IF NOT EXISTS seo_progress (
                    id VARCHAR(255) PRIMARY KEY,
                    job_id VARCHAR(255) NOT NULL REFERENCES seo_jobs(id) ON DELETE CASCADE,
                    stage VARCHAR(100) NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- SEO Logs table
                CREATE TABLE IF NOT EXISTS seo_logs (
                    id VARCHAR(255) PRIMARY KEY,
                    job_id VARCHAR(255) REFERENCES seo_jobs(id) ON DELETE SET NULL,
                    level VARCHAR(10) NOT NULL,
                    message TEXT NOT NULL,
                    operation VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- SEO Metrics table
                CREATE TABLE IF NOT EXISTS seo_metrics (
                    id VARCHAR(255) PRIMARY KEY,
                    job_id VARCHAR(255) REFERENCES seo_jobs(id) ON DELETE SET NULL,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value NUMERIC NOT NULL,
                    metric_unit VARCHAR(50),
                    metadata JSONB,
                    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- SEO URLs table
                CREATE TABLE IF NOT EXISTS seo_urls (
                    id VARCHAR(255) PRIMARY KEY,
                    url TEXT NOT NULL UNIQUE,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    last_checked TIMESTAMPTZ,
                    index_status VARCHAR(50),
                    metadata JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                -- Schema versions table
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    description TEXT NOT NULL
                );
                
                -- Indexes
                CREATE INDEX IF NOT EXISTS idx_seo_jobs_status ON seo_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_seo_jobs_type ON seo_jobs(type);
                CREATE INDEX IF NOT EXISTS idx_seo_jobs_priority ON seo_jobs(priority DESC);
                CREATE INDEX IF NOT EXISTS idx_seo_progress_job_id ON seo_progress(job_id);
                CREATE INDEX IF NOT EXISTS idx_seo_logs_job_id ON seo_logs(job_id);
                CREATE INDEX IF NOT EXISTS idx_seo_logs_level ON seo_logs(level);
                CREATE INDEX IF NOT EXISTS idx_seo_logs_created_at ON seo_logs(created_at);
                CREATE INDEX IF NOT EXISTS idx_seo_metrics_job_id ON seo_metrics(job_id);
                CREATE INDEX IF NOT EXISTS idx_seo_metrics_name ON seo_metrics(metric_name);
                CREATE INDEX IF NOT EXISTS idx_seo_metrics_recorded_at ON seo_metrics(recorded_at);
                CREATE INDEX IF NOT EXISTS idx_seo_urls_status ON seo_urls(status);
                CREATE INDEX IF NOT EXISTS idx_seo_urls_created_at ON seo_urls(created_at);
            `,
        },
    ];
}

// ============================================================================
// Factory Functions
// ============================================================================

/**
 * Create database connection
 * 
 * @param config - Optional database config (uses environment if not provided)
 * @param logger - Optional logger (creates default if not provided)
 * @returns DatabaseConnection instance
 */
export async function createDatabaseConnection(
    config?: DatabaseConfig,
    logger?: Logger
): Promise<DatabaseConnection> {
    const dbConfig = config || getDatabaseConfig();
    const dbLogger = logger || new Logger({ destination: 'console', level: LogLevel.INFO });

    const connection = new DatabaseConnection(dbConfig, dbLogger);
    await connection.connect();

    return connection;
}

let sharedDatabaseConnectionPromise: Promise<DatabaseConnection> | null = null;
let sharedDatabasePromise: Promise<SEODatabase> | null = null;

/**
 * Get a shared runtime database connection.
 *
 * @param logger - Optional logger instance
 * @returns Shared database connection
 */
export async function getSharedDatabaseConnection(logger?: Logger): Promise<DatabaseConnection> {
    if (!sharedDatabaseConnectionPromise) {
        sharedDatabaseConnectionPromise = createDatabaseConnection(undefined, logger).catch((error) => {
            sharedDatabaseConnectionPromise = null;
            throw error;
        });
    }

    return sharedDatabaseConnectionPromise;
}

/**
 * Get shared SEO database operations.
 *
 * @param logger - Optional logger instance
 * @returns Shared SEO database wrapper
 */
export async function getSharedSEODatabase(logger?: Logger): Promise<SEODatabase> {
    if (!sharedDatabasePromise) {
        sharedDatabasePromise = getSharedDatabaseConnection(logger)
            .then((connection) => createSEODatabase(connection, logger || new Logger({ destination: 'console', level: LogLevel.INFO })))
            .catch((error) => {
                sharedDatabasePromise = null;
                throw error;
            });
    }

    return sharedDatabasePromise;
}

/**
 * Close the shared runtime database connection.
 */
export async function closeSharedDatabaseConnection(): Promise<void> {
    const connectionPromise = sharedDatabaseConnectionPromise;

    sharedDatabaseConnectionPromise = null;
    sharedDatabasePromise = null;

    if (!connectionPromise) {
        return;
    }

    const connection = await connectionPromise.catch(() => null);
    if (connection) {
        await connection.disconnect();
    }
}

/**
 * Create SEO database operations
 * 
 * @param connection - Database connection
 * @param logger - Logger instance
 * @returns SEODatabase instance
 */
export function createSEODatabase(
    connection: DatabaseConnection,
    logger: Logger
): SEODatabase {
    return new SEODatabase(connection, logger);
}

/**
 * Create migration runner
 * 
 * @param connection - Database connection
 * @param logger - Logger instance
 * @returns MigrationRunner instance
 */
export function createMigrationRunner(
    connection: DatabaseConnection,
    logger: Logger
): MigrationRunner {
    return new MigrationRunner(connection, logger);
}

// ============================================================================
// Exports
// ============================================================================

export type {
    DatabaseClient,
    QueryResult,
    ExecutionResult,
    FieldInfo,
};

export {
    DatabasePoolConfig,
    DatabaseSSLConfig,
    DatabaseConfig,
    DEFAULT_POOL_CONFIG,
    DEFAULT_SSL_CONFIG,
    getDatabaseConfig,
    DatabaseConnection,
    DatabaseConnectionState,
    SEODatabase,
    SEOJob,
    SEOJobStatus,
    SEOJobType,
    SEOProgress,
    SEOLog,
    SEOLogLevel,
    SEOMetrics,
    URLRecord,
    QueryBuilder,
    createParameterizedQuery,
    MigrationRunner,
    MigrationDefinition,
    SchemaVersion,
    getSEOMigrations,
    createDatabaseConnection,
    getSharedDatabaseConnection,
    getSharedSEODatabase,
    closeSharedDatabaseConnection,
    createSEODatabase,
    createMigrationRunner,
};
