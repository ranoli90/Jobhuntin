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

const __dirname = path.dirname(fileURLToPath(import.meta.url));

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

// Ensure log directory exists
function ensureLogDirectory() {
    if (!fs.existsSync(CONFIG.LOG_DIR)) {
        fs.mkdirSync(CONFIG.LOG_DIR, { recursive: true });
        console.log("📁 Created log directory:", CONFIG.LOG_DIR);
    }
}

// Check if required environment variables are set
function checkEnvironment() {
    const missing = CONFIG.REQUIRED_ENV_VARS.filter(env => !process.env[env]);
    
    if (missing.length > 0) {
        console.log("⚠️  Missing environment variables:", missing.join(", "));
        console.log("   The SEO engine will start but won't be able to submit to Google.");
        console.log("   Set these in your Render environment variables.");
        return false;
    }
    
    console.log("✅ All required environment variables are set");
    return true;
}

// Check if the SEO engine is already running
function isEngineRunning(): boolean {
    try {
        if (fs.existsSync(CONFIG.PID_FILE)) {
            const pid = parseInt(fs.readFileSync(CONFIG.PID_FILE, 'utf8'));
            
            // Check if process exists (cross-platform)
            try {
                process.kill(pid, 0); // Signal 0 just checks if process exists
                console.log("⚠️  SEO engine is already running (PID:", pid + ")");
                return true;
            } catch {
                // Process doesn't exist, remove stale PID file
                fs.unlinkSync(CONFIG.PID_FILE);
                console.log("🧹 Removed stale PID file");
            }
        }
    } catch (error) {
        console.log("⚠️  Could not check if engine is running:", error.message);
    }
    
    return false;
}

// Save process ID for tracking
function savePid(pid: number) {
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
    const isRunning = isEngineRunning();
    const timestamp = new Date().toISOString();
    
    let lastSubmission = null;
    let submissionStats = { total: 0, success: 0, error: 0 };
    try {
        if (fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            const logs = JSON.parse(fs.readFileSync(CONFIG.SUBMISSION_LOG, 'utf8'));
            if (logs.length > 0) {
                lastSubmission = logs[logs.length - 1];
                // Calculate overall stats
                submissionStats.total = logs.reduce((sum: number, log: any) => sum + (log.successCount || 0) + (log.errorCount || 0), 0);
                submissionStats.success = logs.reduce((sum: number, log: any) => sum + (log.successCount || 0), 0);
                submissionStats.error = logs.reduce((sum: number, log: any) => sum + (log.errorCount || 0), 0);
            }
        }
    } catch (error) {
        console.log("⚠️  Could not read health data:", error.message);
    }
    
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
        status: isRunning ? 'healthy' : 'stopped',
        timestamp,
        uptime: process.uptime(),
        lastSubmission,
        submissionStats,
        environment: checkEnvironment(),
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
            const statusCode = health.status === 'healthy' ? 200 : 503;
            res.status(statusCode).json(health);
        } catch (error) {
            console.error('SEO health check error:', error);
            res.status(500).json({
                status: 'error',
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
                        hasLlmKey: !!process.env.LLM_API_KEY
                    }
                }
            });
        } catch (error) {
            res.status(500).json({
                status: 'error',
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