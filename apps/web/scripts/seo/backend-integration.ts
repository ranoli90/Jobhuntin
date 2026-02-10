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

console.log(`🚀 Starting SEO Backend Integration...`);

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
        console.log(`📁 Created log directory: ${CONFIG.LOG_DIR}`);
    }
}

// Check if required environment variables are set
function checkEnvironment() {
    const missing = CONFIG.REQUIRED_ENV_VARS.filter(env => !process.env[env]);
    
    if (missing.length > 0) {
        console.log(`⚠️  Missing environment variables: ${missing.join(', ')}`);
        console.log(`   The SEO engine will start but won't be able to submit to Google.`);
        console.log(`   Set these in your Render environment variables.`);
        return false;
    }
    
    console.log(`✅ All required environment variables are set`);
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
                console.log(`⚠️  SEO engine is already running (PID: ${pid})`);
                return true;
            } catch {
                // Process doesn't exist, remove stale PID file
                fs.unlinkSync(CONFIG.PID_FILE);
                console.log(`🧹 Removed stale PID file`);
            }
        }
    } catch (error) {
        console.log(`⚠️  Could not check if engine is running: ${error.message}`);
    }
    
    return false;
}

// Save process ID for tracking
function savePid(pid: number) {
    try {
        fs.writeFileSync(CONFIG.PID_FILE, pid.toString());
        console.log(`💾 Saved PID: ${pid}`);
    } catch (error) {
        console.log(`⚠️  Could not save PID: ${error.message}`);
    }
}

// Start the SEO engine
function startSEngine(): ChildProcess {
    console.log(`🎯 Starting SEO Ranking Engine...`);
    
    const enginePath = path.resolve(__dirname, 'automated-ranking-engine.ts');
    
    // Start the engine process
    const engineProcess = spawn('npx', ['tsx', enginePath], {
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
        cwd: path.resolve(__dirname, '../..')
    });
    
    // Log stdout
    engineProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log(`[SEO Engine] ${output.trim()}`);
        
        // Append to log file
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${new Date().toISOString()}] ${output}`);
        } catch (error) {
            console.log(`⚠️  Could not write to log file: ${error.message}`);
        }
    });
    
    // Log stderr
    engineProcess.stderr?.on('data', (data) => {
        const error = data.toString();
        console.error(`[SEO Engine Error] ${error.trim()}`);
        
        // Append error to log file
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${new Date().toISOString()}] ERROR: ${error}`);
        } catch (logError) {
            console.log(`⚠️  Could not write error to log file: ${logError.message}`);
        }
    });
    
    // Handle process exit
    engineProcess.on('exit', (code, signal) => {
        console.log(`🛑 SEO engine stopped (code: ${code}, signal: ${signal})`);
        
        // Clean up PID file
        try {
            if (fs.existsSync(CONFIG.PID_FILE)) {
                fs.unlinkSync(CONFIG.PID_FILE);
            }
        } catch (error) {
            console.log(`⚠️  Could not clean up PID file: ${error.message}`);
        }
        
        // Restart engine if it wasn't killed intentionally
        if (signal !== 'SIGTERM' && signal !== 'SIGKILL') {
            console.log(`🔄 Restarting SEO engine in 30 seconds...`);
            setTimeout(() => {
                if (!isEngineRunning()) {
                    const newProcess = startSEngine();
                    savePid(newProcess.pid!);
                }
            }, 30000);
        }
    });
    
    // Handle process errors
    engineProcess.on('error', (error) => {
        console.error(`❌ SEO engine error: ${error.message}`);
        
        try {
            fs.appendFileSync(CONFIG.ENGINE_LOG, `[${new Date().toISOString()}] FATAL ERROR: ${error.message}\n`);
        } catch (logError) {
            console.log(`⚠️  Could not write fatal error to log file: ${logError.message}`);
        }
    });
    
    return engineProcess;
}

// Monitor submission progress
function monitorSubmissions() {
    try {
        if (fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            const logs = JSON.parse(fs.readFileSync(CONFIG.SUBMISSION_LOG, 'utf8'));
            const recentLog = logs[logs.length - 1];
            
            if (recentLog) {
                console.log(`\n📊 Recent Submission Status:`);
                console.log(`   📅 Last submission: ${recentLog.timestamp}`);
                console.log(`   ✅ Successful: ${recentLog.successCount}`);
                console.log(`   ❌ Failed: ${recentLog.errorCount}`);
                console.log(`   📈 Success rate: ${((recentLog.successCount / (recentLog.successCount + recentLog.errorCount)) * 100).toFixed(1)}%`);
            }
        }
    } catch (error) {
        console.log(`⚠️  Could not read submission log: ${error.message}`);
    }
}

// Health check endpoint for monitoring
export function getSEOHealth() {
    const isRunning = isEngineRunning();
    
    let lastSubmission = null;
    try {
        if (fs.existsSync(CONFIG.SUBMISSION_LOG)) {
            const logs = JSON.parse(fs.readFileSync(CONFIG.SUBMISSION_LOG, 'utf8'));
            if (logs.length > 0) {
                lastSubmission = logs[logs.length - 1];
            }
        }
    } catch (error) {
        console.log(`⚠️  Could not read health data: ${error.message}`);
    }
    
    return {
        status: isRunning ? 'healthy' : 'stopped',
        timestamp: new Date().toISOString(),
        lastSubmission,
        environment: checkEnvironment(),
        logFiles: {
            engine: fs.existsSync(CONFIG.ENGINE_LOG) ? CONFIG.ENGINE_LOG : null,
            submissions: fs.existsSync(CONFIG.SUBMISSION_LOG) ? CONFIG.SUBMISSION_LOG : null
        }
    };
}

// Main integration function
export function startSEOIntegration() {
    console.log(`\n🚀 SEO Backend Integration Starting...`);
    
    // Setup
    ensureLogDirectory();
    const envReady = checkEnvironment();
    
    // Check if already running
    if (isEngineRunning()) {
        console.log(`✅ SEO engine is already running`);
        monitorSubmissions();
        return;
    }
    
    // Start the engine
    console.log(`🎯 Starting SEO Ranking Engine...`);
    const engineProcess = startSEngine();
    
    // Save PID for tracking
    if (engineProcess.pid) {
        savePid(engineProcess.pid);
    }
    
    // Initial monitoring
    setTimeout(() => {
        monitorSubmissions();
    }, 5000);
    
    // Schedule regular monitoring
    setInterval(() => {
        monitorSubmissions();
    }, CONFIG.CHECK_INTERVAL * 60 * 1000);
    
    console.log(`\n✅ SEO Backend Integration Complete!`);
    console.log(`\n📋 Integration Summary:`);
    console.log(`   🔄 SEO engine: ${engineProcess.pid ? 'Running' : 'Failed to start'}`);
    console.log(`   📊 Environment: ${envReady ? 'Ready' : 'Missing config'}`);
    console.log(`   📝 Logs: ${CONFIG.LOG_DIR}`);
    console.log(`   ⏰ Check interval: ${CONFIG.CHECK_INTERVAL} minutes`);
    console.log(`\n🎯 The SEO engine will now run 24/7 with your backend!`);
    
    // Handle graceful shutdown
    process.on('SIGTERM', () => {
        console.log(`🛑 Received SIGTERM, shutting down SEO engine...`);
        if (engineProcess && !engineProcess.killed) {
            engineProcess.kill('SIGTERM');
        }
        process.exit(0);
    });
    
    process.on('SIGINT', () => {
        console.log(`🛑 Received SIGINT, shutting down SEO engine...`);
        if (engineProcess && !engineProcess.killed) {
            engineProcess.kill('SIGTERM');
        }
        process.exit(0);
    });
}

// Auto-start if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
    startSEOIntegration();
}

export default { startSEOIntegration, getSEOHealth };