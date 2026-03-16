/**
 * SEO Engine Persistence Layer
 *
 * High-level persistence functions for SEO runtime scripts, providing
 * a clean API for persisting logs, metrics, progress, and URL tracking
 * through the shared database layer.
 *
 * @module seo/persistence
 */

import {
    closeSharedDatabaseConnection,
    getSharedSEODatabase,
    SEODatabase,
    SEOJob,
    SEOJobType,
    SEOLogLevel,
} from './database';
import { Logger } from './logger';
import { Metric, MetricType, MetricsCollector } from './metrics';

// ============================================================================
// Utility Types
// ============================================================================

interface PersistSEOLogParams {
    logger: Logger;
    level: SEOLogLevel;
    message: string;
    operation?: string;
    metadata?: Record<string, unknown>;
    jobId?: string;
}

interface PersistMetricsSnapshotParams {
    collector: MetricsCollector;
    logger: Logger;
    metadata?: Record<string, unknown>;
    jobId?: string;
    onlyMetricNames?: string[];
}

interface CreatePersistedSEOJobTrackerParams {
    script: string;
    logger: Logger;
    payload?: Record<string, unknown>;
    priority?: number;
    type?: SEOJobType;
}

// ============================================================================
// Utility Functions
// ============================================================================

function toErrorMessage(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
}

function serializeError(error: unknown): Record<string, unknown> | undefined {
    if (!error) {
        return undefined;
    }

    if (error instanceof Error) {
        return {
            name: error.name,
            message: error.message,
            stack: error.stack,
        };
    }

    return {
        message: String(error),
    };
}

function getMetricValue(metric: Metric): number {
    switch (metric.type) {
        case MetricType.COUNTER:
        case MetricType.GAUGE:
            return metric.value;
        case MetricType.HISTOGRAM:
        case MetricType.TIMER:
            return metric.mean;
        default:
            return 0;
    }
}

function getMetricMetadata(metric: Metric, metadata?: Record<string, unknown>): Record<string, unknown> {
    const base = {
        metricType: metric.type,
        tags: metric.tags,
        lastUpdated: metric.lastUpdated,
        ...metadata,
    };

    if (metric.type === MetricType.HISTOGRAM || metric.type === MetricType.TIMER) {
        return {
            ...base,
            count: metric.count,
            sum: metric.sum,
            min: metric.min,
            max: metric.max,
            mean: metric.mean,
            percentiles: metric.percentiles,
        };
    }

    if (metric.type === MetricType.GAUGE) {
        return {
            ...base,
            min: metric.min,
            max: metric.max,
        };
    }

    return base;
}

async function getDatabase(logger: Logger): Promise<SEODatabase> {
    return getSharedSEODatabase(logger);
}

// ============================================================================
// Core Persistence Functions
// ============================================================================

/**
 * Persist a log entry to the database.
 *
 * @param params - Log persistence parameters
 */
export async function persistSEOLog(params: PersistSEOLogParams): Promise<void> {
    try {
        const database = await getDatabase(params.logger);
        await database.createLog({
            job_id: params.jobId,
            level: params.level,
            message: params.message,
            operation: params.operation,
            metadata: params.metadata,
        });
    } catch (error) {
        params.logger.warn('Failed to persist SEO log entry', {
            message: params.message,
            operation: params.operation,
            persistenceError: toErrorMessage(error),
        });
    }
}

/**
 * Persist a snapshot of metrics to the database.
 *
 * @param params - Metrics snapshot parameters
 */
export async function persistMetricsSnapshot(params: PersistMetricsSnapshotParams): Promise<void> {
    try {
        const database = await getDatabase(params.logger);
        const metricEntries = Array.from(params.collector.getAllMetrics().values())
            .filter(metric => !params.onlyMetricNames || params.onlyMetricNames.includes(metric.name))
            .map(metric => ({
                job_id: params.jobId,
                metric_name: metric.name,
                metric_value: getMetricValue(metric),
                metric_unit: metric.unit,
                metadata: getMetricMetadata(metric, params.metadata),
                recorded_at: new Date().toISOString(),
            }));

        if (metricEntries.length > 0) {
            await database.createMetricsBatch(metricEntries);
        }
    } catch (error) {
        params.logger.warn('Failed to persist SEO metrics snapshot', {
            persistenceError: toErrorMessage(error),
            metricCount: params.collector.getAllMetrics().size,
        });
    }
}

// ============================================================================
// Persisted SEO Job Tracker
// ============================================================================

/**
 * A class that tracks SEO job progress with database persistence.
 * This provides a high-level API for scripts to track their progress,
 * log events, and record metrics throughout their execution.
 */
export class PersistedSEOJobTracker {
    private readonly database: SEODatabase;
    private readonly logger: Logger;
    private readonly script: string;
    private job: SEOJob;

    private constructor(database: SEODatabase, logger: Logger, script: string, job: SEOJob) {
        this.database = database;
        this.logger = logger;
        this.script = script;
        this.job = job;
    }

    /**
     * Create a new persisted job tracker.
     *
     * @param params - Tracker creation parameters
     * @returns A new PersistedSEOJobTracker instance
     */
    static async create(params: CreatePersistedSEOJobTrackerParams): Promise<PersistedSEOJobTracker> {
        const database = await getDatabase(params.logger);
        const now = new Date().toISOString();
        const job = await database.createJob({
            type: params.type || 'indexing_submission',
            status: 'running',
            priority: params.priority ?? 0,
            payload: {
                script: params.script,
                ...(params.payload || {}),
            },
            started_at: now,
        });

        return new PersistedSEOJobTracker(database, params.logger, params.script, job);
    }

    /**
     * Get the job ID.
     */
    getJobId(): string {
        return this.job.id;
    }

    /**
     * Update job progress.
     *
     * @param stage - The current stage name
     * @param progress - Progress percentage (0-100)
     * @param message - Optional progress message
     * @param metadata - Optional metadata
     */
    async progress(
        stage: string,
        progress: number,
        message?: string,
        metadata?: Record<string, unknown>
    ): Promise<void> {
        try {
            await this.database.updateProgress(this.job.id, stage, progress, message, {
                script: this.script,
                ...(metadata || {}),
            });
        } catch (error) {
            this.logger.warn('Failed to persist SEO progress update', {
                jobId: this.job.id,
                stage,
                progress,
                persistenceError: toErrorMessage(error),
            });
        }
    }

    /**
     * Log an info message.
     *
     * @param message - Log message
     * @param metadata - Optional metadata
     * @param operation - Optional operation context
     */
    async info(message: string, metadata?: Record<string, unknown>, operation?: string): Promise<void> {
        await persistSEOLog({
            logger: this.logger,
            jobId: this.job.id,
            level: 'info',
            message,
            operation,
            metadata: {
                script: this.script,
                ...(metadata || {}),
            },
        });
    }

    /**
     * Log a warning message.
     *
     * @param message - Log message
     * @param metadata - Optional metadata
     * @param operation - Optional operation context
     */
    async warn(message: string, metadata?: Record<string, unknown>, operation?: string): Promise<void> {
        await persistSEOLog({
            logger: this.logger,
            jobId: this.job.id,
            level: 'warn',
            message,
            operation,
            metadata: {
                script: this.script,
                ...(metadata || {}),
            },
        });
    }

    /**
     * Log an error message.
     *
     * @param message - Log message
     * @param error - Optional error object
     * @param metadata - Optional metadata
     * @param operation - Optional operation context
     */
    async error(message: string, error?: unknown, metadata?: Record<string, unknown>, operation?: string): Promise<void> {
        await persistSEOLog({
            logger: this.logger,
            jobId: this.job.id,
            level: 'error',
            message,
            operation,
            metadata: {
                script: this.script,
                ...(metadata || {}),
                error: serializeError(error),
            },
        });
    }

    /**
     * Record a metric.
     *
     * @param name - Metric name
     * @param value - Metric value
     * @param unit - Optional unit
     * @param metadata - Optional metadata
     */
    async metric(name: string, value: number, unit?: string, metadata?: Record<string, unknown>): Promise<void> {
        try {
            await this.database.createMetrics({
                job_id: this.job.id,
                metric_name: name,
                metric_value: value,
                metric_unit: unit,
                metadata: {
                    script: this.script,
                    ...(metadata || {}),
                },
                recorded_at: new Date().toISOString(),
            });
        } catch (error) {
            this.logger.warn('Failed to persist SEO metric', {
                jobId: this.job.id,
                metricName: name,
                persistenceError: toErrorMessage(error),
            });
        }
    }

    /**
     * Take a snapshot of all current metrics.
     *
     * @param collector - The metrics collector to snapshot
     * @param metadata - Optional metadata to include
     */
    async snapshotMetrics(collector: MetricsCollector, metadata?: Record<string, unknown>): Promise<void> {
        await persistMetricsSnapshot({
            collector,
            logger: this.logger,
            jobId: this.job.id,
            metadata: {
                script: this.script,
                ...(metadata || {}),
            },
        });
    }

    /**
     * Track a URL submission result.
     *
     * @param url - The URL that was submitted
     * @param status - Submission status
     * @param metadata - Optional metadata
     */
    async trackUrl(
        url: string,
        status: 'success' | 'error',
        metadata?: Record<string, unknown>
    ): Promise<void> {
        try {
            await this.database.upsertURL({
                url,
                status: status === 'success' ? 'submitted' : 'error',
                last_checked: new Date().toISOString(),
                index_status: status === 'success' ? 'pending' : 'error',
                metadata: {
                    script: this.script,
                    jobId: this.job.id,
                    status,
                    ...(metadata || {}),
                },
            });
        } catch (error) {
            this.logger.warn('Failed to persist SEO URL status', {
                jobId: this.job.id,
                url,
                status,
                persistenceError: toErrorMessage(error),
            });
        }
    }

    /**
     * Mark the job as completed.
     *
     * @param result - Optional result data
     */
    async complete(result?: Record<string, unknown>): Promise<void> {
        try {
            this.job = await this.database.updateJob(this.job.id, {
                status: 'completed',
                result,
                completed_at: new Date().toISOString(),
            });
            await this.progress('completed', 100, 'Completed', result);
            await this.info('SEO job completed', result, 'seo-job:complete');
        } catch (error) {
            this.logger.warn('Failed to finalize SEO job completion', {
                jobId: this.job.id,
                persistenceError: toErrorMessage(error),
            });
        }
    }

    /**
     * Mark the job as failed.
     *
     * @param error - The error that caused the failure
     * @param metadata - Optional metadata
     */
    async fail(error: unknown, metadata?: Record<string, unknown>): Promise<void> {
        const message = toErrorMessage(error);

        try {
            this.job = await this.database.updateJob(this.job.id, {
                status: 'failed',
                error: message,
                completed_at: new Date().toISOString(),
                result: {
                    ...(metadata || {}),
                    error: serializeError(error),
                },
            });
            await this.progress('failed', 100, message, metadata);
            await this.error('SEO job failed', error, metadata, 'seo-job:fail');
        } catch (persistenceError) {
            this.logger.warn('Failed to persist SEO job failure', {
                jobId: this.job.id,
                persistenceError: toErrorMessage(persistenceError),
                originalError: message,
            });
        }
    }
}

// Re-export for convenience
export { closeSharedDatabaseConnection };
