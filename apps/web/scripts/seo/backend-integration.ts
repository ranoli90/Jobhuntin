/**
 * backend-integration.ts
 * 
 * Integrates the SEO ranking engine with your backend deployment
 * This script starts automatically when your backend runs on Render
 * 
 * Features:
 * - Starts automatically with backend deployment
 * - Runs 24/7 in background
 * - Monitors and submits new content to Google
 * - Integrates with existing backend without conflicts
 * 
 * Usage in your backend (add to your main server file):
 *   import './scripts/seo/backend-integration';
 * 
 * Or run manually:
 *   npx tsx scripts/seo/backend-integration.ts
 */

import { spawn, ChildProcess } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { seoLogger } from './logger';
import { MetricsCollector, MetricType, HealthStatus, SEO_METRIC_NAMES } from './metrics';
import { persistMetricsSnapshot, persistSEOLog } from './persistence';
import { loadAndValidateConfig } from './config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const healthLogger = seoLogger.child({ component: 'seo-health' });

console.log("🚀 Starting SEO Backend Integration...");

// Configuration
const CONFIG = {
    // How often to check for new content (in minutes)
    CHECK_INTERVAL: 60, // 1 hour

    // Maximum URLs to submit per day (Google limit: 200)
    MAX_DAILY_SUBMISSIONS: 200,

    // Time between submissions (in seconds)
    SUBMISSION_DELAY: 30,

    // Log file paths
    LOG_DIR: path.resolve(__dirname, '../../logs'),
    ENGINE_LOG: path.resolve(__dirname, '../../logs/seo-engine.log'),
    SUBMISSION_LOG: path.resolve(__dirname, '../../logs/google-indexing-submissions.json'),

    // Process tracking
    PID_FILE: path.resolve(__dirname, '../../logs/seo-engine.pid'),

    // Environment check
    REQUIRED_ENV_VARS: ['GOOGLE_SERVICE_ACCOUNT_KEY', 'GOOGLE_SEARCH_CONSOLE_SITE']
};

const SEO_HEALTH_METRIC_NAMES = {
    CONFIG_READY: 'seo.health.config_ready',
    GENERATION_READY: 'seo.health.generation_ready',
    SUBMISSION_READY: 'seo.health.submission_ready',
    LAST_SUBMISSION_AGE_HOURS: 'seo.health.last_submission_age_hours'
} as const;

const HEALTH_WINDOW_HOURS = 24;
const STALE_SUBMISSION_HOURS = 24;
const UNKNOWN_SUBMISSION_AGE_HOURS = 999;

const healthMetrics = new MetricsCollector({
    enableAggregation: false,
    enableHealthChecks: false,
    alertConditions: [
        {
            metricName: SEO_METRIC_NAMES.ACTIVE_JOBS,
            status: HealthStatus.UNHEALTHY,
            operator: 'lte',
            threshold: 0
        },
        {
            metricName: SEO_METRIC_NAMES.ERROR_RATE,
            status: HealthStatus.UNHEALTHY,
            operator: 'gt',
            threshold: 50
        },
        {
            metricName: SEO_METRIC_NAMES.ERROR_RATE,
            status: HealthStatus.DEGRADED,
            operator: 'gt',
            threshold: 20
        },
        {
            metricName: SEO_HEALTH_METRIC_NAMES.CONFIG_READY,
            status: HealthStatus.UNHEALTHY,
            operator: 'lte',
            threshold: 0
        },
        {
            metricName: SEO_HEALTH_METRIC_NAMES.GENERATION_READY,
            status: HealthStatus.DEGRADED,
            operator: 'lte',
            threshold: 0
        },
        {
            metricName: SEO_HEALTH_METRIC_NAMES.SUBMISSION_READY,
            status: HealthStatus.DEGRADED,
            operator: 'lte',
            threshold: 0
        },
        {
            metricName: SEO_HEALTH_METRIC_NAMES.LAST_SUBMISSION_AGE_HOURS,
            status: HealthStatus.DEGRADED,
            operator: 'gt',
            threshold: STALE_SUBMISSION_HOURS
        }
    ]
}, healthLogger);

healthMetrics.createMetric({
    name: SEO_HEALTH_METRIC_NAMES.CONFIG_READY,
    type: MetricType.GAUGE,
    description: 'Whether core SEO configuration is ready',
    unit: 'boolean'
});
healthMetrics.createMetric({
    name: SEO_HEALTH_METRIC_NAMES.GENERATION_READY,
    type: MetricType.GAUGE,
    description: 'Whether content generation pipeline configuration is ready',
    unit: 'boolean'
});
healthMetrics.createMetric({
    name: SEO_HEALTH_METRIC_NAMES.SUBMISSION_READY,
    type: MetricType.GAUGE,
    description: 'Whether Google submission pipeline configuration is ready',
    unit: 'boolean'
});
healthMetrics.createMetric({
    name: SEO_HEALTH_METRIC_NAMES.LAST_SUBMISSION_AGE_HOURS,
    type: MetricType.GAUGE,
    description: 'Age of the most recent submission log entry',
    unit: 'hours'
});

let lastHealthFingerprint: string | null = null;

interface SubmissionLogEntry {
    timestamp?: string;
    successCount?: number;
    errorCount?: number;
}

interface SEOHealthCheck {
    name: string;
    status: HealthStatus;
    reason: string;
    details?: Record<string, unknown>;
}

function getMissingEnvironmentVariables(requiredEnvVars: string[]): string[] {
    return requiredEnvVars.filter(env => !process.env[env]);
}

function getOverallHealthStatus(statuses: HealthStatus[]): HealthStatus {
    if (statuses.includes(HealthStatus.UNHEALTHY)) {
        return HealthStatus.UNHEALTHY;
    }

    if (statuses.includes(HealthStatus.DEGRADED)) {
        return HealthStatus.DEGRADED;
    }

    return HealthStatus.HEALTHY;
}

function readSubmissionLogs(): SubmissionLogEntry[] {
    try {
        if (!fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            return [];
        }

        const parsed = JSON.parse(fs.readFileSync(CONFIG.SUBMISSION_LOG, 'utf8'));
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function getHoursSince(timestamp?: string | null): number | null {
    if (!timestamp) {
        return null;
    }

    const parsed = new Date(timestamp).getTime();
    if (!Number.isFinite(parsed)) {
        return null;
    }

    return (Date.now() - parsed) / (1000 * 60 * 60);
}

function summarizeSubmissionLogs(logs: SubmissionLogEntry[]): {
    recentLogs: SubmissionLogEntry[];
    recentSuccess: number;
    recentError: number;
    recentAttempts: number;
    recentFailureRate: number;
    lastSubmission: SubmissionLogEntry | null;
    lastSubmissionAgeHours: number | null;
} {
    const now = Date.now();
    const recentWindowMs = HEALTH_WINDOW_HOURS * 60 * 60 * 1000;

    const recentLogs = logs.filter((log) => {
        if (!log.timestamp) {
            return false;
        }

        const parsed = new Date(log.timestamp).getTime();
        return Number.isFinite(parsed) && (now - parsed) <= recentWindowMs;
    });

    const recentSuccess = recentLogs.reduce((sum, log) => sum + (log.successCount || 0), 0);
    const recentError = recentLogs.reduce((sum, log) => sum + (log.errorCount || 0), 0);
    const recentAttempts = recentSuccess + recentError;
    const recentFailureRate = recentAttempts > 0
        ? Number(((recentError / recentAttempts) * 100).toFixed(2))
        : 0;

    const lastSubmission = logs.length > 0 ? logs[logs.length - 1] : null;

    return {
        recentLogs,
        recentSuccess,
        recentError,
        recentAttempts,
        recentFailureRate,
        lastSubmission,
        lastSubmissionAgeHours: getHoursSince(lastSubmission?.timestamp)
    };
}

function recordHealthMetrics(params: {
    isRunning: boolean;
    configReady: boolean;
    generationReady: boolean;
    submissionReady: boolean;
    recentFailureRate: number;
    lastSubmissionAgeHours: number | null;
}): void {
    healthMetrics.setGauge(SEO_METRIC_NAMES.ACTIVE_JOBS, params.isRunning ? 1 : 0, { component: 'seo-health' });
    healthMetrics.setGauge(SEO_METRIC_NAMES.ERROR_RATE, params.recentFailureRate, { component: 'seo-health' });
    healthMetrics.setGauge(SEO_HEALTH_METRIC_NAMES.CONFIG_READY, params.configReady ? 1 : 0, { component: 'seo-health' });
    healthMetrics.setGauge(SEO_HEALTH_METRIC_NAMES.GENERATION_READY, params.generationReady ? 1 : 0, { component: 'seo-health' });
    healthMetrics.setGauge(SEO_HEALTH_METRIC_NAMES.SUBMISSION_READY, params.submissionReady ? 1 : 0, { component: 'seo-health' });
    healthMetrics.setGauge(
        SEO_HEALTH_METRIC_NAMES.LAST_SUBMISSION_AGE_HOURS,
        params.lastSubmissionAgeHours ?? UNKNOWN_SUBMISSION_AGE_HOURS,
        { component: 'seo-health' }
    );

    void persistMetricsSnapshot({
        collector: healthMetrics,
        logger: healthLogger,
        metadata: { component: 'seo-health' },
        onlyMetricNames: [
            SEO_METRIC_NAMES.ACTIVE_JOBS,
            SEO_METRIC_NAMES.ERROR_RATE,
            SEO_HEALTH_METRIC_NAMES.CONFIG_READY,
            SEO_HEALTH_METRIC_NAMES.GENERATION_READY,
            SEO_HEALTH_METRIC_NAMES.SUBMISSION_READY,
            SEO_HEALTH_METRIC_NAMES.LAST_SUBMISSION_AGE_HOURS,
        ],
    });
}

function logHealthTransition(status: HealthStatus, reasons: string[], checks: SEOHealthCheck[]): void {
    const fingerprint = JSON.stringify({
        status,
        reasons,
        checks: checks.filter(check => check.status !== HealthStatus.HEALTHY).map(check => ({
            name: check.name,
            status: check.status,
            reason: check.reason
        }))
    });

    if (fingerprint === lastHealthFingerprint) {
        return;
    }

    lastHealthFingerprint = fingerprint;

    const metadata = {
        reasons,
        checks: checks.map(check => ({
            name: check.name,
            status: check.status,
            reason: check.reason
        }))
    };

    if (status === HealthStatus.UNHEALTHY) {
        healthLogger.error('SEO health is unhealthy', undefined, metadata);
        void persistSEOLog({
            logger: healthLogger,
            level: 'error',
            message: 'SEO health is unhealthy',
            operation: 'seo-health:transition',
            metadata,
        });
        return;
    }

    if (status === HealthStatus.DEGRADED) {
        healthLogger.warn('SEO health is degraded', metadata);
        void persistSEOLog({
            logger: healthLogger,
            level: 'warn',
            message: 'SEO health is degraded',
            operation: 'seo-health:transition',
            metadata,
        });
        return;
    }

    healthLogger.info('SEO health is healthy', metadata);
    void persistSEOLog({
        logger: healthLogger,
        level: 'info',
        message: 'SEO health is healthy',
        operation: 'seo-health:transition',
        metadata,
    });
}

// Ensure log directory exists
function ensureLogDirectory(): void {
    if (!fs.existsSync(CONFIG.LOG_DIR)) {
        fs.mkdirSync(CONFIG.LOG_DIR, { recursive: true });
        console.log("📁 Created log directory:", CONFIG.LOG_DIR);
    }
}

// Check if required environment variables are set
function checkEnvironment(emitLogs: boolean = true): boolean {
    const missing = getMissingEnvironmentVariables(CONFIG.REQUIRED_ENV_VARS);

    if (missing.length > 0) {
        if (emitLogs) {
            console.log("⚠️  Missing environment variables:", missing.join(", "));
            console.log("   The SEO engine will start but won't be able to submit to Google.");
            console.log("   Set these in your Render environment variables.");
        }
        return false;
    }

    if (emitLogs) {
        console.log("✅ All required environment variables are set");
    }
    return true;
}

// Check if the SEO engine is already running
function isEngineRunning(emitLogs: boolean = true): boolean {
    try {
        if (fs.existsSync(CONFIG.PID_FILE)) {
            const pid = parseInt(fs.readFileSync(CONFIG.PID_FILE, 'utf8'));

            // Check if process exists (cross-platform)
            try {
                process.kill(pid, 0); // Signal 0 just checks if process exists
                if (emitLogs) {
                    console.log("⚠️  SEO engine is already running (PID:", pid + ")");
                }
                return true;
            } catch {
                // Process doesn't exist, remove stale PID file
                fs.unlinkSync(CONFIG.PID_FILE);
                if (emitLogs) {
                    console.log("🧹 Removed stale PID file");
                }
            }
        }
    } catch (error: any) {
        if (emitLogs) {
            console.log("⚠️  Could not check if engine is running:", error.message);
        }
    }

    return false;
}

// Save process ID for tracking
function savePid(pid: number): void {
    try {
        fs.writeFileSync(CONFIG.PID_FILE, pid.toString());
        console.log("💾 Saved PID:", pid);
    } catch (error) {
        console.log("⚠️  Could not save PID:", error.message);
    }
}

// Start the SEO engine
function startSEngine(): ChildProcess {
    console.log("🎯 Starting SEO Ranking Engine...");

    const enginePath = path.resolve(__dirname, 'automated-ranking-engine.ts');

    // Start the engine process with proper environment
    const engineProcess = spawn('npx', ['tsx', enginePath], {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
        cwd: path.resolve(__dirname, '../..'),
        env: {
            ...process.env,
            NODE_ENV: process.env.NODE_ENV || 'production',
            DATABASE_URL: process.env.DATABASE_URL,
            GOOGLE_SERVICE_ACCOUNT_KEY: process.env.GOOGLE_SERVICE_ACCOUNT_KEY,
            GOOGLE_SEARCH_CONSOLE_SITE: process.env.GOOGLE_SEARCH_CONSOLE_SITE,
            LLM_API_KEY: process.env.LLM_API_KEY,
            LLM_API_BASE: process.env.LLM_API_BASE,
            LLM_MODEL: process.env.LLM_MODEL
        }
    });

    // Log stdout with timestamps
    engineProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        const timestamp = new Date().toISOString();
        console.log("[SEO Engine", timestamp + "]", output.trim());

        // Append to log file with timestamp
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] ${output}`);
        } catch (error) {
            console.log("⚠️  Could not write to log file:", error.message);
        }
    });

    // Log stderr with timestamps
    engineProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        const timestamp = new Date().toISOString();
        console.error("[SEO Engine Error", timestamp + "]", error.trim());

        // Append error to log file with timestamp
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] ERROR: ${error}`);
        } catch (logError) {
            console.log("⚠️  Could not write error to log file:", logError.message);
        }
    });

    // Handle process exit with enhanced logging
    engineProcess.on('exit', (code, signal) => {
        const timestamp = new Date().toISOString();
        console.log("🛑 SEO engine stopped (code:", code, ", signal:", signal, ") at", timestamp);

        // Log to file for debugging
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] ENGINE STOPPED (code: ${code}, signal: ${signal})`);
        } catch (error) {
            console.log("⚠️  Could not log engine stop:", error.message);
        }

        // Clean up PID file
        try {
            if (fs.existsSync(CONFIG.PID_FILE)) {
                fs.unlinkSync(CONFIG.PID_FILE);
                console.log("🧹 Cleaned up PID file");
            }
        } catch (error) {
            console.log("⚠️  Could not clean up PID file:", error.message);
        }

        // Restart engine if it wasn't killed intentionally (with backoff)
        if (signal !== 'SIGTERM' && signal !== 'SIGKILL') {
            const backoffTime = Math.min(30000 * Math.pow(2, Math.floor(Math.random() * 3)), 300000); // 30s-5min with jitter
            console.log("🔄 Restarting SEO engine in", backoffTime / 1000, "s...");
            setTimeout(() => {
                if (!isEngineRunning()) {
                    console.log("🚀 Starting SEO engine restart...");
                    const newProcess = startSEngine();
                    savePid(newProcess.pid!);
                } else {
                    console.log("✅ SEO engine already running, skipping restart");
                }
            }, backoffTime);
        }
    });

    // Handle process errors with enhanced logging
    engineProcess.on('error', (error) => {
        const timestamp = new Date().toISOString();
        console.error("❌ SEO engine error at", timestamp, ":", error.message);

        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] FATAL ERROR: ${error.message}\n`);
        } catch (logError) {
            console.log("⚠️  Could not write fatal error to log file:", logError.message);
        }

        // Attempt restart on fatal errors
        if (!isEngineRunning()) {
            console.log("🔄 Attempting restart due to fatal error...");
            setTimeout(() => {
                const newProcess = startSEngine();
                savePid(newProcess.pid!);
            }, 10000); // 10 second delay for error recovery
        }
    });

    return engineProcess;
}

// Monitor submission progress with enhanced logging
function monitorSubmissions() {
    try {
        if (fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            const logs = JSON.parse(fs.readFileSync(CONFIG.SUBMISSION_LOG, 'utf8'));
            const recentLog = logs[logs.length - 1];

            if (recentLog) {
                const successRate = ((recentLog.successCount / (recentLog.successCount + recentLog.errorCount)) * 100).toFixed(1);
                console.log("\n📊 Recent Submission Status (" + new Date().toISOString() + "):");
                console.log("   📅 Last submission:", recentLog.timestamp);
                console.log("   ✅ Successful:", recentLog.successCount);
                console.log("   ❌ Failed:", recentLog.errorCount);
                console.log("   📈 Success rate:", successRate + "%");

                // Log to engine log for persistence
                try {
                    fs.appendFileSync(CONFIG.ENGINE_LOG, `[${new Date().toISOString()}] SUBMISSION MONITOR: Success rate ${successRate}%\n`);
                } catch (error) {
                    console.log("⚠️  Could not log submission monitor:", error.message);
                }
            }
        }
    } catch (error) {
        console.log("⚠️  Could not read submission log:", error.message);
    }
}

// Health check endpoint for monitoring with enhanced diagnostics
export function getSEOHealth() {
    const isRunning = isEngineRunning(false);
    const timestamp = new Date().toISOString();
    const submissionLogs = readSubmissionLogs();
    const submissionSummary = summarizeSubmissionLogs(submissionLogs);

    const coreMissing = getMissingEnvironmentVariables(['DATABASE_URL']);
    const generationMissing = getMissingEnvironmentVariables(['LLM_API_KEY']);
    const submissionMissing = getMissingEnvironmentVariables(CONFIG.REQUIRED_ENV_VARS);
    const environmentReady = checkEnvironment(false);

    let configValidationError: string | null = null;
    try {
        loadAndValidateConfig();
    } catch (error: any) {
        configValidationError = error.message;
    }

    let lastSubmission = submissionSummary.lastSubmission;
    let submissionStats = { total: 0, success: 0, error: 0 };
    try {
        if (submissionLogs.length > 0) {
            submissionStats.total = submissionLogs.reduce((sum: number, log: SubmissionLogEntry) => sum + (log.successCount || 0) + (log.errorCount || 0), 0);
            submissionStats.success = submissionLogs.reduce((sum: number, log: SubmissionLogEntry) => sum + (log.successCount || 0), 0);
            submissionStats.error = submissionLogs.reduce((sum: number, log: SubmissionLogEntry) => sum + (log.errorCount || 0), 0);
        }
    } catch (error: any) {
        console.log("⚠️  Could not read health data:", error.message);
    }

    const configReady = coreMissing.length === 0;
    const generationReady = generationMissing.length === 0;
    const submissionReady = submissionMissing.length === 0;

    recordHealthMetrics({
        isRunning,
        configReady,
        generationReady,
        submissionReady,
        recentFailureRate: submissionSummary.recentFailureRate,
        lastSubmissionAgeHours: submissionSummary.lastSubmissionAgeHours
    });

    const checks: SEOHealthCheck[] = [
        {
            name: 'engine-process',
            status: isRunning ? HealthStatus.HEALTHY : HealthStatus.UNHEALTHY,
            reason: isRunning
                ? 'SEO engine process is running.'
                : 'SEO engine process is not running; restart the backend integration or engine worker.',
            details: {
                pidFilePresent: fs.existsSync(CONFIG.PID_FILE)
            }
        },
        {
            name: 'configuration-readiness',
            status: configReady
                ? (configValidationError ? HealthStatus.DEGRADED : HealthStatus.HEALTHY)
                : HealthStatus.UNHEALTHY,
            reason: configReady
                ? (configValidationError
                    ? `Core environment is present, but SEO config validation reported: ${configValidationError}`
                    : 'Core SEO runtime configuration is present and validated.')
                : `Core SEO runtime configuration is missing: ${coreMissing.join(', ')}`,
            details: {
                missing: coreMissing,
                configValidationError
            }
        },
        {
            name: 'generation-pipeline-readiness',
            status: generationReady ? HealthStatus.HEALTHY : HealthStatus.DEGRADED,
            reason: generationReady
                ? 'Content generation pipeline is configured.'
                : `Content generation is blocked until these environment variables are set: ${generationMissing.join(', ')}`,
            details: {
                missing: generationMissing,
                llmConfigured: generationReady
            }
        },
        {
            name: 'submission-pipeline-readiness',
            status: submissionReady ? HealthStatus.HEALTHY : HealthStatus.DEGRADED,
            reason: submissionReady
                ? 'Google submission pipeline is configured.'
                : `Google submission is blocked until these environment variables are set: ${submissionMissing.join(', ')}`,
            details: {
                missing: submissionMissing,
                submissionConfigured: submissionReady,
                lastSubmissionAgeHours: submissionSummary.lastSubmissionAgeHours
            }
        },
        {
            name: 'api-availability',
            status: !submissionReady
                ? HealthStatus.DEGRADED
                : submissionSummary.recentAttempts === 0
                    ? HealthStatus.DEGRADED
                    : submissionSummary.recentFailureRate > 50
                        ? HealthStatus.UNHEALTHY
                        : submissionSummary.recentFailureRate > 20
                            ? HealthStatus.DEGRADED
                            : HealthStatus.HEALTHY,
            reason: !submissionReady
                ? 'Google submission API availability cannot be confirmed because submission credentials are missing.'
                : submissionSummary.recentAttempts === 0
                    ? `No submission attempts were recorded in the last ${HEALTH_WINDOW_HOURS} hours, so API availability cannot be confirmed from runtime signals.`
                    : submissionSummary.recentFailureRate > 50
                        ? `Recent Google submission failures are elevated at ${submissionSummary.recentFailureRate}%. Investigate Google credentials, quotas, or network connectivity.`
                        : submissionSummary.recentFailureRate > 20
                            ? `Recent Google submission failures are above the warning threshold at ${submissionSummary.recentFailureRate}%.`
                            : 'Recent submission activity indicates Google submission API availability.',
            details: {
                recentAttempts: submissionSummary.recentAttempts,
                recentFailureRate: submissionSummary.recentFailureRate,
                windowHours: HEALTH_WINDOW_HOURS
            }
        },
        {
            name: 'recent-failure-metrics',
            status: submissionSummary.recentAttempts === 0
                ? HealthStatus.DEGRADED
                : submissionSummary.recentFailureRate >= 50
                    ? HealthStatus.UNHEALTHY
                    : submissionSummary.recentFailureRate >= 20
                        ? HealthStatus.DEGRADED
                        : HealthStatus.HEALTHY,
            reason: submissionSummary.recentAttempts === 0
                ? `No recent submissions were recorded in the last ${HEALTH_WINDOW_HOURS} hours, so failure-rate health has no fresh sample.`
                : submissionSummary.recentFailureRate >= 50
                    ? `Recent failure rate is ${submissionSummary.recentFailureRate}% across ${submissionSummary.recentAttempts} submissions.`
                    : submissionSummary.recentFailureRate >= 20
                        ? `Recent failure rate is elevated at ${submissionSummary.recentFailureRate}% across ${submissionSummary.recentAttempts} submissions.`
                        : `Recent failure rate is ${submissionSummary.recentFailureRate}% across ${submissionSummary.recentAttempts} submissions.`,
            details: {
                recentSuccess: submissionSummary.recentSuccess,
                recentError: submissionSummary.recentError,
                recentAttempts: submissionSummary.recentAttempts,
                recentFailureRate: submissionSummary.recentFailureRate
            }
        }
    ];

    if (submissionReady && submissionSummary.lastSubmissionAgeHours !== null && submissionSummary.lastSubmissionAgeHours > STALE_SUBMISSION_HOURS) {
        checks.push({
            name: 'submission-freshness',
            status: HealthStatus.DEGRADED,
            reason: `The most recent submission log is ${Number(submissionSummary.lastSubmissionAgeHours.toFixed(2))} hours old. Review scheduler activity if regular submissions are expected.`,
            details: {
                lastSubmissionAgeHours: Number(submissionSummary.lastSubmissionAgeHours.toFixed(2)),
                staleAfterHours: STALE_SUBMISSION_HOURS
            }
        });
    }

    const metricHealth = healthMetrics.performHealthCheck();
    const status = getOverallHealthStatus([
        metricHealth.status,
        ...checks.map(check => check.status)
    ]);
    const reasons = checks
        .filter(check => check.status !== HealthStatus.HEALTHY)
        .map(check => `${check.name}: ${check.reason}`);

    logHealthTransition(status, reasons, checks);

    // Check log file sizes for diagnostics
    let engineLogSize = 0;
    let submissionLogSize = 0;
    try {
        if (fs.existsSync(CONFIG.ENGINE_LOG)) {
            const stats = fs.statSync(CONFIG.ENGINE_LOG);
            engineLogSize = stats.size;
        }
        if (fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            const stats = fs.statSync(CONFIG.SUBMISSION_LOG);
            submissionLogSize = stats.size;
        }
    } catch (error) {
        // Ignore log size check errors
    }

    return {
        status,
        timestamp,
        uptime: process.uptime(),
        reasons,
        checks,
        lastSubmission,
        submissionStats,
        environment: {
            ready: environmentReady,
            missingCore: coreMissing,
            missingGeneration: generationMissing,
            missingSubmission: submissionMissing,
            configValidationError
        },
        observability: {
            metricsHealth: metricHealth,
            recentFailureRate: submissionSummary.recentFailureRate,
            recentAttempts: submissionSummary.recentAttempts,
            lastSubmissionAgeHours: submissionSummary.lastSubmissionAgeHours
        },
        logFiles: {
            engine: fs.existsSync(CONFIG.ENGINE_LOG) ? CONFIG.ENGINE_LOG : null,
            submissions: fs.existsSync(CONFIG.SUBMISSION_LOG) ? CONFIG.SUBMISSION_LOG : null,
            engineLogSize,
            submissionLogSize
        },
        diagnostics: {
            pidFile: fs.existsSync(CONFIG.PID_FILE),
            logDir: fs.existsSync(CONFIG.LOG_DIR),
            memoryUsage: process.memoryUsage(),
            nodeVersion: process.version
        }
    };
}

// Express.js health endpoint integration with enhanced error handling
export function setupSEOHealthEndpoint(app: any) {
    app.get('/api/seo-health', (req: any, res: any) => {
        try {
            const health = getSEOHealth();
            const statusCode = health.status === HealthStatus.UNHEALTHY ? 503 : 200;
            res.status(statusCode).json(health);
        } catch (error: any) {
            console.error('SEO health check error:', error);
            res.status(500).json({
                status: HealthStatus.UNHEALTHY,
                timestamp: new Date().toISOString(),
                error: error.message,
                diagnostics: {
                    uptime: process.uptime(),
                    memoryUsage: process.memoryUsage(),
                    nodeVersion: process.version
                }
            });
        }
    });

    // Add detailed diagnostics endpoint
    app.get('/api/seo-diagnostics', (req: any, res: any) => {
        try {
            const health = getSEOHealth();
            res.json({
                ...health,
                detailed: {
                    config: CONFIG,
                    processInfo: {
                        pid: process.pid,
                        platform: process.platform,
                        arch: process.arch,
                        nodeVersion: process.version,
                        uptime: process.uptime()
                    },
                    environment: {
                        nodeEnv: process.env.NODE_ENV,
                        hasDatabaseUrl: !!process.env.DATABASE_URL,
                        hasGoogleKey: !!process.env.GOOGLE_SERVICE_ACCOUNT_KEY,
                        hasLlmKey: !!process.env.LLM_API_KEY,
                        hasGoogleSearchConsoleSite: !!process.env.GOOGLE_SEARCH_CONSOLE_SITE
                    }
                }
            });
        } catch (error: any) {
            res.status(500).json({
                status: HealthStatus.UNHEALTHY,
                timestamp: new Date().toISOString(),
                error: error.message
            });
        }
    });
}

// Main integration function with enhanced startup logging
export function startSEOIntegration() {
    const startupTime = new Date().toISOString();
    console.log("\n🚀 SEO Backend Integration Starting at", startupTime, "...");

    // Setup
    ensureLogDirectory();
    const envReady = checkEnvironment();

    // Log startup to file
    try {
        fs.appendFileSync(CONFIG.ENGINE_LOG, `[${startupTime}] SEO INTEGRATION STARTING\n`);
    } catch (error) {
        console.log("⚠️  Could not log startup:", error.message);
    }

    // Check if already running
    if (isEngineRunning()) {
        console.log("✅ SEO engine is already running");
        monitorSubmissions();
        return null;
    }

    // Start the engine
    console.log("🎯 Starting SEO Ranking Engine...");
    const engineProcess = startSEngine();

    // Save PID for tracking
    if (engineProcess.pid) {
        savePid(engineProcess.pid);
    }

    // Initial monitoring with logging
    setTimeout(() => {
        console.log("🔍 Running initial monitoring check...");
        monitorSubmissions();
    }, 5000);

    // Schedule regular monitoring with enhanced logging
    setInterval(() => {
        const timestamp = new Date().toISOString();
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] SCHEDULED MONITOR CHECK\n`);
        } catch (error) {
            // Ignore logging errors
        }
        monitorSubmissions();
    }, CONFIG.CHECK_INTERVAL * 60 * 1000);

    console.log("\n✅ SEO Backend Integration Complete!");
    console.log("\n📋 Integration Summary:");
    console.log("   🔄 SEO engine:", engineProcess.pid ? "Running (PID: " + engineProcess.pid + ")" : "Failed to start");
    console.log("   📊 Environment:", envReady ? "Ready" : "Missing config");
    console.log("   📝 Logs:", CONFIG.LOG_DIR);
    console.log("   ⏰ Check interval:", CONFIG.CHECK_INTERVAL, "minutes");
    console.log("   🕐 Started at:", startupTime);
    console.log("\n🎯 The SEO engine will now run 24/7 with your backend!");
    console.log("🔗 Health endpoint: /api/seo-health");
    console.log("🔗 Diagnostics endpoint: /api/seo-diagnostics");

    // Handle graceful shutdown with enhanced logging
    process.on('SIGTERM', () => {
        const timestamp = new Date().toISOString();
        console.log("🛑 Received SIGTERM, shutting down SEO engine at", timestamp, "...");
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] SIGTERM RECEIVED - SHUTTING DOWN\n`);
        } catch (error) {
            // Ignore logging errors during shutdown
        }
        if (engineProcess && !engineProcess.killed) {
            engineProcess.kill('SIGTERM');
        }
        process.exit(0);
    });

    process.on('SIGINT', () => {
        const timestamp = new Date().toISOString();
        console.log("🛑 Received SIGINT, shutting down SEO engine at", timestamp, "...");
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${timestamp}] SIGINT RECEIVED - SHUTTING DOWN\n`);
        } catch (error) {
            // Ignore logging errors during shutdown
        }
        if (engineProcess && !engineProcess.killed) {
            engineProcess.kill('SIGTERM');
        }
        process.exit(0);
    });

    // Return the engine process for external management
    return engineProcess;
}

// Auto-start if run directly with error handling
if (import.meta.url === `file://${process.argv[1]}`) {
    try {
        startSEOIntegration();
    } catch (error) {
        console.error('❌ SEO Integration failed to start:', error);
        process.exit(1);
    }
}

export default { startSEOIntegration, getSEOHealth, setupSEOHealthEndpoint };
