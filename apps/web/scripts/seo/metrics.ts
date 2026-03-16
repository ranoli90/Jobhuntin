/**
 * SEO Engine Metrics Collection
 * 
 * Comprehensive metrics system for monitoring SEO engine performance,
 * including counters, gauges, histograms, and timers with aggregation
 * and health check capabilities.
 * 
 * @module seo/metrics
 */

import { Logger } from './logger';

// ============================================================================
// Metric Types
// ============================================================================

/**
 * Types of metrics supported by the collector
 */
export enum MetricType {
    /** Counter - monotonically increasing value (e.g., total requests) */
    COUNTER = 'counter',
    /** Gauge - current value that can go up or down (e.g., queue size) */
    GAUGE = 'gauge',
    /** Histogram - distribution of values (e.g., response times) */
    HISTOGRAM = 'histogram',
    /** Timer - measures duration in milliseconds */
    TIMER = 'timer'
}

/**
 * Metric value types
 */
export type MetricValue = number;

/**
 * Base metric interface
 */
export interface BaseMetric {
    /** Unique metric name */
    name: string;
    /** Metric type */
    type: MetricType;
    /** Human-readable description */
    description?: string;
    /** Unit of measurement */
    unit?: string;
    /** Tags for metric categorization */
    tags?: Record<string, string>;
    /** Timestamp of last update */
    lastUpdated?: string;
}

/**
 * Counter metric - monotonically increasing value
 */
export interface CounterMetric extends BaseMetric {
    type: MetricType.COUNTER;
    /** Current count value */
    value: number;
    /** Optional rate (increments per second) */
    rate?: number;
}

/**
 * Gauge metric - current value that can go up or down
 */
export interface GaugeMetric extends BaseMetric {
    type: MetricType.GAUGE;
    /** Current gauge value */
    value: number;
    /** Minimum recorded value */
    min?: number;
    /** Maximum recorded value */
    max?: number;
}

/**
 * Histogram metric - distribution of values
 */
export interface HistogramMetric extends BaseMetric {
    type: MetricType.HISTOGRAM;
    /** Count of observations */
    count: number;
    /** Sum of all values */
    sum: number;
    /** Minimum value */
    min: number;
    /** Maximum value */
    max: number;
    /** Mean value */
    mean: number;
    /** Pre-calculated percentiles */
    percentiles?: {
        p50?: number;
        p75?: number;
        p90?: number;
        p95?: number;
        p99?: number;
    };
    /** Bucket counts for histogram */
    buckets?: Array<{ le: number; count: number }>;
}

/**
 * Timer metric - measures duration in milliseconds
 */
export interface TimerMetric extends BaseMetric {
    type: MetricType.TIMER;
    /** Count of timing observations */
    count: number;
    /** Total duration in milliseconds */
    sum: number;
    /** Minimum duration */
    min: number;
    /** Maximum duration */
    max: number;
    /** Mean duration */
    mean: number;
    /** Pre-calculated percentiles */
    percentiles?: {
        p50?: number;
        p75?: number;
        p90?: number;
        p95?: number;
        p99?: number;
    };
}

/**
 * Union type for all metric types
 */
export type Metric = CounterMetric | GaugeMetric | HistogramMetric | TimerMetric;

// ============================================================================
// Metric Definition
// ============================================================================

/**
 * Definition for creating a new metric
 */
export interface MetricDefinition {
    /** Unique metric name */
    name: string;
    /** Metric type */
    type: MetricType;
    /** Human-readable description */
    description?: string;
    /** Unit of measurement */
    unit?: string;
    /** Initial tags */
    tags?: Record<string, string>;
    /** For histograms: custom bucket boundaries */
    buckets?: number[];
}

// ============================================================================
// Predefined SEO Metrics
// ============================================================================

/**
 * Predefined metric names for SEO operations
 */
export const SEO_METRIC_NAMES = {
    // API Call Metrics
    GOOGLE_API_CALLS: 'seo.google_api_calls',
    GOOGLE_API_ERRORS: 'seo.google_api_errors',
    GOOGLE_API_LATENCY: 'seo.google_api_latency',

    // Content Generation Metrics
    CONTENT_GENERATED: 'seo.content_generated',
    CONTENT_FAILED: 'seo.content_failed',
    CONTENT_DUPLICATES: 'seo.content_duplicates',
    CONTENT_GENERATION_TIME: 'seo.content_generation_time',

    // URL Submission Metrics
    URLS_SUBMITTED: 'seo.urls_submitted',
    URLS_INDEXED: 'seo.urls_indexed',
    URLS_FAILED: 'seo.urls_failed',
    URL_SUBMISSION_TIME: 'seo.url_submission_time',

    // Queue Metrics
    JOBS_QUEUED: 'seo.jobs_queued',
    JOBS_PROCESSING: 'seo.jobs_processing',
    JOBS_COMPLETED: 'seo.jobs_completed',
    JOBS_FAILED: 'seo.jobs_failed',

    // Performance Metrics
    RESPONSE_TIME: 'seo.response_time',
    CONTENT_LENGTH: 'seo.content_length',
    API_RETRY_COUNT: 'seo.api_retry_count',

    // Health Metrics
    QUEUE_SIZE: 'seo.queue_size',
    ACTIVE_JOBS: 'seo.active_jobs',
    ERROR_RATE: 'seo.error_rate'
} as const;

/**
 * Predefined metric definitions for SEO
 */
export const SEO_METRIC_DEFINITIONS: MetricDefinition[] = [
    // API Call Metrics
    {
        name: SEO_METRIC_NAMES.GOOGLE_API_CALLS,
        type: MetricType.COUNTER,
        description: 'Total number of Google API calls made',
        unit: 'calls'
    },
    {
        name: SEO_METRIC_NAMES.GOOGLE_API_ERRORS,
        type: MetricType.COUNTER,
        description: 'Total number of Google API errors',
        unit: 'errors'
    },
    {
        name: SEO_METRIC_NAMES.GOOGLE_API_LATENCY,
        type: MetricType.HISTOGRAM,
        description: 'Latency of Google API calls',
        unit: 'ms',
        buckets: [10, 50, 100, 250, 500, 1000, 2500, 5000]
    },

    // Content Generation Metrics
    {
        name: SEO_METRIC_NAMES.CONTENT_GENERATED,
        type: MetricType.COUNTER,
        description: 'Total number of content pieces generated',
        unit: 'items'
    },
    {
        name: SEO_METRIC_NAMES.CONTENT_FAILED,
        type: MetricType.COUNTER,
        description: 'Total number of content generation failures',
        unit: 'items'
    },
    {
        name: SEO_METRIC_NAMES.CONTENT_DUPLICATES,
        type: MetricType.COUNTER,
        description: 'Total number of duplicate content detected',
        unit: 'items'
    },
    {
        name: SEO_METRIC_NAMES.CONTENT_GENERATION_TIME,
        type: MetricType.TIMER,
        description: 'Time taken to generate content',
        unit: 'ms'
    },

    // URL Submission Metrics
    {
        name: SEO_METRIC_NAMES.URLS_SUBMITTED,
        type: MetricType.COUNTER,
        description: 'Total number of URLs submitted for indexing',
        unit: 'urls'
    },
    {
        name: SEO_METRIC_NAMES.URLS_INDEXED,
        type: MetricType.COUNTER,
        description: 'Total number of URLs successfully indexed',
        unit: 'urls'
    },
    {
        name: SEO_METRIC_NAMES.URLS_FAILED,
        type: MetricType.COUNTER,
        description: 'Total number of URL indexing failures',
        unit: 'urls'
    },
    {
        name: SEO_METRIC_NAMES.URL_SUBMISSION_TIME,
        type: MetricType.TIMER,
        description: 'Time taken to submit URLs for indexing',
        unit: 'ms'
    },

    // Queue Metrics
    {
        name: SEO_METRIC_NAMES.JOBS_QUEUED,
        type: MetricType.COUNTER,
        description: 'Total number of jobs queued',
        unit: 'jobs'
    },
    {
        name: SEO_METRIC_NAMES.JOBS_PROCESSING,
        type: MetricType.GAUGE,
        description: 'Number of currently processing jobs',
        unit: 'jobs'
    },
    {
        name: SEO_METRIC_NAMES.JOBS_COMPLETED,
        type: MetricType.COUNTER,
        description: 'Total number of completed jobs',
        unit: 'jobs'
    },
    {
        name: SEO_METRIC_NAMES.JOBS_FAILED,
        type: MetricType.COUNTER,
        description: 'Total number of failed jobs',
        unit: 'jobs'
    },

    // Performance Metrics
    {
        name: SEO_METRIC_NAMES.RESPONSE_TIME,
        type: MetricType.HISTOGRAM,
        description: 'API response times',
        unit: 'ms',
        buckets: [50, 100, 250, 500, 1000, 2000, 5000]
    },
    {
        name: SEO_METRIC_NAMES.CONTENT_LENGTH,
        type: MetricType.HISTOGRAM,
        description: 'Generated content lengths',
        unit: 'chars',
        buckets: [500, 1000, 2000, 5000, 10000, 20000]
    },
    {
        name: SEO_METRIC_NAMES.API_RETRY_COUNT,
        type: MetricType.COUNTER,
        description: 'Total number of API retries',
        unit: 'retries'
    },

    // Health Metrics
    {
        name: SEO_METRIC_NAMES.QUEUE_SIZE,
        type: MetricType.GAUGE,
        description: 'Current size of the job queue',
        unit: 'jobs'
    },
    {
        name: SEO_METRIC_NAMES.ACTIVE_JOBS,
        type: MetricType.GAUGE,
        description: 'Number of currently active jobs',
        unit: 'jobs'
    },
    {
        name: SEO_METRIC_NAMES.ERROR_RATE,
        type: MetricType.GAUGE,
        description: 'Current error rate percentage',
        unit: 'percent'
    }
];

// ============================================================================
// Health Check Types
// ============================================================================

/**
 * Health status levels
 */
export enum HealthStatus {
    HEALTHY = 'healthy',
    DEGRADED = 'degraded',
    UNHEALTHY = 'unhealthy'
}

/**
 * Alert condition definition
 */
export interface AlertCondition {
    /** Metric name to monitor */
    metricName: string;
    /** Health status when condition is met */
    status: HealthStatus;
    /** Comparison operator */
    operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
    /** Threshold value */
    threshold: number;
    /** Time window for evaluating condition (ms) */
    window?: number;
}

/**
 * Health check result
 */
export interface HealthCheckResult {
    /** Overall health status */
    status: HealthStatus;
    /** Timestamp of check */
    timestamp: string;
    /** Individual metric health statuses */
    metrics: Array<{
        name: string;
        status: HealthStatus;
        value: number;
        message?: string;
    }>;
    /** Alerts triggered */
    alerts: Array<{
        condition: AlertCondition;
        metricName: string;
        currentValue: number;
        message: string;
    }>;
}

// ============================================================================
// Metrics Aggregation
// ============================================================================

/**
 * Time window for metrics aggregation
 */
export interface TimeWindow {
    /** Window start time (ISO string) */
    start: string;
    /** Window end time (ISO string) */
    end: string;
    /** Window duration in milliseconds */
    duration: number;
}

/**
 * Aggregated metrics result
 */
export interface AggregatedMetrics {
    /** Time window */
    window: TimeWindow;
    /** Aggregated metrics */
    metrics: Record<string, Metric>;
    /** Calculated rates */
    rates?: Record<string, number>;
    /** Calculated averages */
    averages?: Record<string, number>;
    /** Calculated percentiles */
    percentiles?: Record<string, Record<string, number>>;
}

// ============================================================================
// Metrics Configuration
// ============================================================================

/**
 * Metrics collector configuration
 */
export interface MetricsCollectorConfig {
    /** Enable metrics aggregation */
    enableAggregation: boolean;
    /** Aggregation window in milliseconds */
    aggregationWindowMs: number;
    /** Maximum number of aggregated windows to keep */
    maxAggregatedWindows: number;
    /** Enable health checks */
    enableHealthChecks: boolean;
    /** Health check interval in milliseconds */
    healthCheckIntervalMs: number;
    /** Alert conditions */
    alertConditions: AlertCondition[];
    /** Metrics retention period in milliseconds */
    retentionMs: number;
    /** Export format */
    exportFormat: 'json' | 'prometheus' | 'both';
}

/**
 * Default metrics collector configuration
 */
export const DEFAULT_METRICS_CONFIG: MetricsCollectorConfig = {
    enableAggregation: true,
    aggregationWindowMs: 60000, // 1 minute
    maxAggregatedWindows: 60, // Keep 1 hour of data
    enableHealthChecks: true,
    healthCheckIntervalMs: 30000, // 30 seconds
    alertConditions: [
        {
            metricName: SEO_METRIC_NAMES.ERROR_RATE,
            status: HealthStatus.UNHEALTHY,
            operator: 'gt',
            threshold: 10 // > 10% error rate
        },
        {
            metricName: SEO_METRIC_NAMES.GOOGLE_API_ERRORS,
            status: HealthStatus.DEGRADED,
            operator: 'gt',
            threshold: 5,
            window: 60000 // Last minute
        },
        {
            metricName: SEO_METRIC_NAMES.JOBS_PROCESSING,
            status: HealthStatus.UNHEALTHY,
            operator: 'gt',
            threshold: 100 // > 100 concurrent jobs
        }
    ],
    retentionMs: 3600000, // 1 hour
    exportFormat: 'json'
};

// ============================================================================
// Metrics Collector Class
// ============================================================================

/**
 * Metrics Collector for SEO engine
 * 
 * Provides methods to record different types of metrics with support for
 * aggregation, health checks, and multiple export formats.
 */
export class MetricsCollector {
    private metrics: Map<string, Metric> = new Map();
    private metricHistory: Map<string, Array<{ timestamp: string; value: number }>> = new Map();
    private config: MetricsCollectorConfig;
    private logger: Logger;
    private aggregationInterval?: NodeJS.Timeout;
    private healthCheckInterval?: NodeJS.Timeout;
    private currentWindowStart: Date = new Date();

    /**
     * Create a new MetricsCollector instance
     */
    constructor(config: Partial<MetricsCollectorConfig> = {}, logger?: Logger) {
        this.config = { ...DEFAULT_METRICS_CONFIG, ...config };
        this.logger = logger || new Logger({ level: 1, destination: 'console' }); // INFO level

        // Initialize predefined SEO metrics
        this.initializeMetrics();

        // Start aggregation if enabled
        if (this.config.enableAggregation) {
            this.startAggregation();
        }

        // Start health checks if enabled
        if (this.config.enableHealthChecks) {
            this.startHealthChecks();
        }
    }

    /**
     * Initialize predefined SEO metrics
     */
    private initializeMetrics(): void {
        for (const definition of SEO_METRIC_DEFINITIONS) {
            this.createMetric(definition);
        }
        this.logger.info('SEO metrics initialized', {
            metricCount: SEO_METRIC_DEFINITIONS.length
        });
    }

    /**
     * Create a new metric
     */
    createMetric(definition: MetricDefinition): Metric | undefined {
        const { name, type, description, unit, tags, buckets } = definition;

        let metric: Metric;
        const base = {
            name,
            type,
            description,
            unit,
            tags,
            lastUpdated: new Date().toISOString()
        };

        switch (type) {
            case MetricType.COUNTER:
                metric = {
                    ...base,
                    type: MetricType.COUNTER,
                    value: 0
                } as CounterMetric;
                break;

            case MetricType.GAUGE:
                metric = {
                    ...base,
                    type: MetricType.GAUGE,
                    value: 0,
                    min: undefined,
                    max: undefined
                } as GaugeMetric;
                break;

            case MetricType.HISTOGRAM:
                metric = {
                    ...base,
                    type: MetricType.HISTOGRAM,
                    count: 0,
                    sum: 0,
                    min: Infinity,
                    max: -Infinity,
                    mean: 0,
                    buckets: buckets ? buckets.map(le => ({ le, count: 0 })) : undefined
                } as HistogramMetric;
                break;

            case MetricType.TIMER:
                metric = {
                    ...base,
                    type: MetricType.TIMER,
                    count: 0,
                    sum: 0,
                    min: Infinity,
                    max: -Infinity,
                    mean: 0
                } as TimerMetric;
                break;

            default:
                this.logger.warn('Unknown metric type', { type });
                return undefined;
        }

        this.metrics.set(name, metric);
        this.metricHistory.set(name, []);

        return metric;
    }

    /**
     * Get a metric by name
     */
    getMetric(name: string): Metric | undefined {
        return this.metrics.get(name);
    }

    /**
     * Get all metrics
     */
    getAllMetrics(): Map<string, Metric> {
        return new Map(this.metrics);
    }

    /**
     * Increment a counter metric
     */
    incrementCounter(name: string, value: number = 1, tags?: Record<string, string>): void {
        const metric = this.metrics.get(name);

        if (!metric || metric.type !== MetricType.COUNTER) {
            this.logger.warn('Invalid counter metric', { name, expectedType: MetricType.COUNTER });
            return;
        }

        const counterMetric = metric as CounterMetric;
        counterMetric.value += value;
        counterMetric.lastUpdated = new Date().toISOString();

        // Update tags if provided
        if (tags) {
            counterMetric.tags = { ...counterMetric.tags, ...tags };
        }

        // Record history
        this.recordHistory(name, counterMetric.value);

        this.logger.debug('Counter incremented', { name, value: counterMetric.value });
    }

    /**
     * Set a gauge metric value
     */
    setGauge(name: string, value: number, tags?: Record<string, string>): void {
        const metric = this.metrics.get(name);

        if (!metric || metric.type !== MetricType.GAUGE) {
            this.logger.warn('Invalid gauge metric', { name, expectedType: MetricType.GAUGE });
            return;
        }

        const gaugeMetric = metric as GaugeMetric;
        gaugeMetric.value = value;

        // Track min/max
        if (gaugeMetric.min === undefined || value < gaugeMetric.min) {
            gaugeMetric.min = value;
        }
        if (gaugeMetric.max === undefined || value > gaugeMetric.max) {
            gaugeMetric.max = value;
        }

        gaugeMetric.lastUpdated = new Date().toISOString();

        // Update tags if provided
        if (tags) {
            gaugeMetric.tags = { ...gaugeMetric.tags, ...tags };
        }

        // Record history
        this.recordHistory(name, value);

        this.logger.debug('Gauge set', { name, value });
    }

    /**
     * Record a histogram value
     */
    recordHistogram(name: string, value: number, tags?: Record<string, string>): void {
        const metric = this.metrics.get(name);

        if (!metric || metric.type !== MetricType.HISTOGRAM) {
            this.logger.warn('Invalid histogram metric', { name, expectedType: MetricType.HISTOGRAM });
            return;
        }

        const histogramMetric = metric as HistogramMetric;
        histogramMetric.count++;
        histogramMetric.sum += value;
        histogramMetric.min = Math.min(histogramMetric.min, value);
        histogramMetric.max = Math.max(histogramMetric.max, value);
        histogramMetric.mean = histogramMetric.sum / histogramMetric.count;
        histogramMetric.lastUpdated = new Date().toISOString();

        // Update bucket counts
        if (histogramMetric.buckets) {
            for (const bucket of histogramMetric.buckets) {
                if (value <= bucket.le) {
                    bucket.count++;
                }
            }
        }

        // Update tags if provided
        if (tags) {
            histogramMetric.tags = { ...histogramMetric.tags, ...tags };
        }

        // Record history
        this.recordHistory(name, value);

        this.logger.debug('Histogram recorded', { name, value, count: histogramMetric.count });
    }

    /**
     * Record a timer value (convenience method for histograms in ms)
     */
    recordTimer(name: string, durationMs: number, tags?: Record<string, string>): void {
        const metric = this.metrics.get(name);

        if (metric && metric.type === MetricType.TIMER) {
            const timerMetric = metric as TimerMetric;
            timerMetric.count++;
            timerMetric.sum += durationMs;
            timerMetric.min = Math.min(timerMetric.min, durationMs);
            timerMetric.max = Math.max(timerMetric.max, durationMs);
            timerMetric.mean = timerMetric.sum / timerMetric.count;
            timerMetric.lastUpdated = new Date().toISOString();

            // Update tags if provided
            if (tags) {
                timerMetric.tags = { ...timerMetric.tags, ...tags };
            }

            // Record history
            this.recordHistory(name, durationMs);

            this.logger.debug('Timer recorded', { name, durationMs, count: timerMetric.count });
        } else {
            // Fall back to histogram if timer doesn't exist
            this.recordHistogram(name, durationMs, tags);
        }
    }

    /**
     * Convenience method to time a function execution
     */
    time<T>(name: string, fn: () => T, tags?: Record<string, string>): T {
        const start = Date.now();
        try {
            return fn();
        } finally {
            const duration = Date.now() - start;
            this.recordTimer(name, duration, tags);
        }
    }

    /**
     * Convenience method to time an async function execution
     */
    async timeAsync<T>(name: string, fn: () => Promise<T>, tags?: Record<string, string>): Promise<T> {
        const start = Date.now();
        try {
            return await fn();
        } finally {
            const duration = Date.now() - start;
            this.recordTimer(name, duration, tags);
        }
    }

    /**
     * Record history for a metric
     */
    private recordHistory(name: string, value: number): void {
        const history = this.metricHistory.get(name);
        if (!history) return;

        history.push({
            timestamp: new Date().toISOString(),
            value
        });

        // Trim old history based on retention
        const cutoff = Date.now() - this.config.retentionMs;
        while (history.length > 0) {
            const oldest = history[0];
            if (new Date(oldest.timestamp).getTime() < cutoff) {
                history.shift();
            } else {
                break;
            }
        }
    }

    /**
     * Calculate percentiles from histogram data
     */
    calculatePercentiles(values: number[]): Record<string, number> {
        if (values.length === 0) {
            return { p50: 0, p75: 0, p90: 0, p95: 0, p99: 0 };
        }

        const sorted = [...values].sort((a, b) => a - b);
        const n = sorted.length;

        const getPercentile = (p: number): number => {
            const index = Math.ceil(p * n) - 1;
            return sorted[Math.max(0, Math.min(index, n - 1))];
        };

        return {
            p50: getPercentile(0.50),
            p75: getPercentile(0.75),
            p90: getPercentile(0.90),
            p95: getPercentile(0.95),
            p99: getPercentile(0.99)
        };
    }

    /**
     * Update percentile values for histogram/timer metrics
     */
    updatePercentiles(name: string): void {
        const history = this.metricHistory.get(name);
        if (!history || history.length === 0) return;

        const values = history.map(h => h.value);
        const percentiles = this.calculatePercentiles(values);

        const metric = this.metrics.get(name);
        if (!metric) return;

        if (metric.type === MetricType.HISTOGRAM) {
            (metric as HistogramMetric).percentiles = percentiles;
        } else if (metric.type === MetricType.TIMER) {
            (metric as TimerMetric).percentiles = percentiles;
        }
    }

    /**
     * Start periodic aggregation
     */
    private startAggregation(): void {
        this.aggregationInterval = setInterval(() => {
            this.aggregateMetrics();
        }, this.config.aggregationWindowMs);

        this.logger.info('Metrics aggregation started', {
            intervalMs: this.config.aggregationWindowMs
        });
    }

    /**
     * Aggregate metrics for the current window
     */
    aggregateMetrics(): AggregatedMetrics {
        const now = new Date();
        const window: TimeWindow = {
            start: this.currentWindowStart.toISOString(),
            end: now.toISOString(),
            duration: now.getTime() - this.currentWindowStart.getTime()
        };

        const aggregatedMetrics: Record<string, Metric> = {};
        const rates: Record<string, number> = {};
        const averages: Record<string, number> = {};
        const percentiles: Record<string, Record<string, number>> = {};

        // Calculate rates and averages for counters
        for (const [name, metric] of this.metrics) {
            if (metric.type === MetricType.COUNTER) {
                const counterMetric = metric as CounterMetric;
                rates[name] = counterMetric.value / (window.duration / 1000);
                aggregatedMetrics[name] = { ...counterMetric };
            } else if (metric.type === MetricType.HISTOGRAM || metric.type === MetricType.TIMER) {
                this.updatePercentiles(name);
                percentiles[name] = this.calculatePercentiles(
                    this.metricHistory.get(name)?.map(h => h.value) || []
                );

                // Calculate average
                const history = this.metricHistory.get(name);
                if (history && history.length > 0) {
                    const sum = history.reduce((acc, h) => acc + h.value, 0);
                    averages[name] = sum / history.length;
                }

                aggregatedMetrics[name] = { ...metric };
            } else {
                aggregatedMetrics[name] = { ...metric };
            }
        }

        this.currentWindowStart = now;

        this.logger.debug('Metrics aggregated', {
            window: window.start,
            metricCount: Object.keys(aggregatedMetrics).length
        });

        return {
            window,
            metrics: aggregatedMetrics,
            rates,
            averages,
            percentiles
        };
    }

    /**
     * Start periodic health checks
     */
    private startHealthChecks(): void {
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, this.config.healthCheckIntervalMs);

        this.logger.info('Health checks started', {
            intervalMs: this.config.healthCheckIntervalMs
        });
    }

    /**
     * Perform a health check
     */
    performHealthCheck(): HealthCheckResult {
        const result: HealthCheckResult = {
            status: HealthStatus.HEALTHY,
            timestamp: new Date().toISOString(),
            metrics: [],
            alerts: []
        };

        for (const condition of this.config.alertConditions) {
            const metric = this.metrics.get(condition.metricName);

            if (!metric) {
                continue;
            }

            let value: number;
            switch (metric.type) {
                case MetricType.COUNTER:
                    value = (metric as CounterMetric).value;
                    break;
                case MetricType.GAUGE:
                    value = (metric as GaugeMetric).value;
                    break;
                case MetricType.HISTOGRAM:
                    value = (metric as HistogramMetric).mean;
                    break;
                case MetricType.TIMER:
                    value = (metric as TimerMetric).mean;
                    break;
                default:
                    continue;
            }

            // Evaluate condition
            let isTriggered = false;
            switch (condition.operator) {
                case 'gt':
                    isTriggered = value > condition.threshold;
                    break;
                case 'lt':
                    isTriggered = value < condition.threshold;
                    break;
                case 'eq':
                    isTriggered = value === condition.threshold;
                    break;
                case 'gte':
                    isTriggered = value >= condition.threshold;
                    break;
                case 'lte':
                    isTriggered = value <= condition.threshold;
                    break;
            }

            const metricStatus = isTriggered ? condition.status : HealthStatus.HEALTHY;

            result.metrics.push({
                name: condition.metricName,
                status: metricStatus,
                value,
                message: isTriggered
                    ? `Value ${value} ${condition.operator} ${condition.threshold}`
                    : undefined
            });

            if (isTriggered) {
                result.alerts.push({
                    condition,
                    metricName: condition.metricName,
                    currentValue: value,
                    message: `Alert: ${condition.metricName} is ${metricStatus} (${value} ${condition.operator} ${condition.threshold})`
                });

                // Update overall status
                if (condition.status === HealthStatus.UNHEALTHY) {
                    result.status = HealthStatus.UNHEALTHY;
                } else if (condition.status === HealthStatus.DEGRADED && result.status === HealthStatus.HEALTHY) {
                    result.status = HealthStatus.DEGRADED;
                }
            }
        }

        if (result.alerts.length > 0) {
            this.logger.warn('Health check alerts', {
                alerts: result.alerts.map(a => a.message)
            });
        }

        return result;
    }

    /**
     * Export metrics in JSON format
     */
    exportJson(): string {
        const exportData: Record<string, unknown> = {
            timestamp: new Date().toISOString(),
            metrics: {}
        };

        for (const [name, metric] of this.metrics) {
            exportData.metrics[name] = {
                ...metric,
                historyLength: this.metricHistory.get(name)?.length || 0
            };
        }

        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Export metrics in Prometheus format
     */
    exportPrometheus(): string {
        const lines: string[] = ['# SEO Engine Metrics'];

        for (const [name, metric] of this.metrics) {
            const help = metric.description || name;
            const type = metric.type.toUpperCase();

            // Add help and type hints
            lines.push(`# HELP ${name} ${help}`);
            lines.push(`# TYPE ${name} ${type === 'TIMER' ? 'HISTOGRAM' : type.toLowerCase()}`);

            // Add metric values
            switch (metric.type) {
                case MetricType.COUNTER:
                    lines.push(`${name} ${(metric as CounterMetric).value}`);
                    break;

                case MetricType.GAUGE:
                    lines.push(`${name} ${(metric as GaugeMetric).value}`);
                    break;

                case MetricType.HISTOGRAM:
                    const histogram = metric as HistogramMetric;
                    lines.push(`${name}_count ${histogram.count}`);
                    lines.push(`${name}_sum ${histogram.sum}`);
                    lines.push(`${name}_mean ${histogram.mean}`);
                    if (histogram.buckets) {
                        for (const bucket of histogram.buckets) {
                            lines.push(`${name}_bucket{le="${bucket.le}"} ${bucket.count}`);
                        }
                        lines.push(`${name}_bucket{le="+Inf"} ${histogram.count}`);
                    }
                    break;

                case MetricType.TIMER:
                    const timer = metric as TimerMetric;
                    lines.push(`${name}_count ${timer.count}`);
                    lines.push(`${name}_sum ${timer.sum}`);
                    lines.push(`${name}_mean ${timer.mean}`);
                    lines.push(`${name}_min ${timer.min}`);
                    lines.push(`${name}_max ${timer.max}`);
                    break;
            }
        }

        return lines.join('\n');
    }

    /**
     * Export metrics based on configured format
     */
    export(): string {
        switch (this.config.exportFormat) {
            case 'json':
                return this.exportJson();
            case 'prometheus':
                return this.exportPrometheus();
            case 'both':
                return JSON.stringify({
                    json: JSON.parse(this.exportJson()),
                    prometheus: this.exportPrometheus()
                }, null, 2);
            default:
                return this.exportJson();
        }
    }

    /**
     * Reset all metrics
     */
    reset(): void {
        this.metrics.clear();
        this.metricHistory.clear();
        this.initializeMetrics();
        this.logger.info('Metrics reset');
    }

    /**
     * Stop the collector (clear intervals)
     */
    stop(): void {
        if (this.aggregationInterval) {
            clearInterval(this.aggregationInterval);
            this.aggregationInterval = undefined;
        }

        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = undefined;
        }

        this.logger.info('Metrics collector stopped');
    }

    /**
     * Get metric history
     */
    getHistory(name: string): Array<{ timestamp: string; value: number }> {
        return this.metricHistory.get(name) || [];
    }

    /**
     * Get metrics by type
     */
    getMetricsByType(type: MetricType): Metric[] {
        const result: Metric[] = [];
        for (const metric of this.metrics.values()) {
            if (metric.type === type) {
                result.push(metric);
            }
        }
        return result;
    }
}

// ============================================================================
// Pre-configured Collectors
// ============================================================================

/**
 * Default metrics collector instance
 */
let defaultCollector: MetricsCollector | undefined;

/**
 * Get or create the default metrics collector
 */
export function getMetricsCollector(config?: Partial<MetricsCollectorConfig>, logger?: Logger): MetricsCollector {
    if (!defaultCollector) {
        defaultCollector = new MetricsCollector(config, logger);
    }
    return defaultCollector;
}

/**
 * Reset the default metrics collector
 */
export function resetDefaultCollector(): void {
    if (defaultCollector) {
        defaultCollector.stop();
        defaultCollector = undefined;
    }
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Increment a counter on the default collector
 */
export function incrementCounter(name: string, value?: number, tags?: Record<string, string>): void {
    getMetricsCollector().incrementCounter(name, value, tags);
}

/**
 * Set a gauge on the default collector
 */
export function setGauge(name: string, value: number, tags?: Record<string, string>): void {
    getMetricsCollector().setGauge(name, value, tags);
}

/**
 * Record a histogram value on the default collector
 */
export function recordHistogram(name: string, value: number, tags?: Record<string, string>): void {
    getMetricsCollector().recordHistogram(name, value, tags);
}

/**
 * Record a timer value on the default collector
 */
export function recordTimer(name: string, durationMs: number, tags?: Record<string, string>): void {
    getMetricsCollector().recordTimer(name, durationMs, tags);
}

/**
 * Time a function on the default collector
 */
export function time<T>(name: string, fn: () => T, tags?: Record<string, string>): T {
    return getMetricsCollector().time(name, fn, tags);
}

/**
 * Time an async function on the default collector
 */
export function timeAsync<T>(name: string, fn: () => Promise<T>, tags?: Record<string, string>): Promise<T> {
    return getMetricsCollector().timeAsync(name, fn, tags);
}

// ============================================================================
// Export all types and classes
// ============================================================================

export {
    MetricsCollector,
    MetricType,
    Metric,
    BaseMetric,
    CounterMetric,
    GaugeMetric,
    HistogramMetric,
    TimerMetric,
    MetricDefinition,
    MetricValue,
    SEO_METRIC_NAMES,
    SEO_METRIC_DEFINITIONS,
    HealthStatus,
    AlertCondition,
    HealthCheckResult,
    TimeWindow,
    AggregatedMetrics,
    MetricsCollectorConfig,
    DEFAULT_METRICS_CONFIG
};
