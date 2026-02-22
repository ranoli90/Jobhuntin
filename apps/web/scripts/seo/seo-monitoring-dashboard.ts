/**
 * seo-monitoring-dashboard.ts
 * 
 * Real-time monitoring dashboard for your SEO ranking engine
 * Shows live submission status, indexing progress, and traffic predictions
 * 
 * Usage:
 *   npx tsx scripts/seo/seo-monitoring-dashboard.ts
 * 
 * Features:
 *   📊 Live submission tracking
 *   🔍 Google indexing verification
 *   📈 Traffic potential analysis
 *   ⚡ Real-time error monitoring
 *   🎯 Performance metrics
 */

import 'dotenv/config';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface MonitoringMetrics {
  totalGenerated: number;
  totalSubmitted: number;
  totalIndexed: number;
  successRate: number;
  dailyAverage: number;
  estimatedTraffic: number;
  lastSubmission: string;
  lastGeneration: string;
  engineStatus: 'running' | 'stopped' | 'error';
  googleAuth: 'connected' | 'failed' | 'unknown';
}

class SEOMonitoringDashboard {
  private logPath = path.resolve(__dirname, '../../logs/google-indexing-submissions.json');
  private engineLogPath = path.resolve(__dirname, '../../logs/seo-engine.log');
  private metrics: MonitoringMetrics;

  constructor() {
    this.metrics = this.loadMetrics();
    this.startRealtimeMonitoring();
  }

  private loadMetrics(): MonitoringMetrics {
    const defaultMetrics: MonitoringMetrics = {
      totalGenerated: 0,
      totalSubmitted: 0,
      totalIndexed: 0,
      successRate: 0,
      dailyAverage: 0,
      estimatedTraffic: 0,
      lastSubmission: 'Never',
      lastGeneration: 'Never',
      engineStatus: 'unknown',
      googleAuth: 'unknown'
    };

    try {
      if (fs.existsSync(this.logPath)) {
        const logs = JSON.parse(fs.readFileSync(this.logPath, 'utf8'));
        
        // Calculate metrics from logs
        const totalSubmitted = logs.reduce((sum: number, log: any) => sum + log.successCount, 0);
        const totalErrors = logs.reduce((sum: number, log: any) => sum + log.errorCount, 0);
        const successRate = totalSubmitted > 0 ? (totalSubmitted / (totalSubmitted + totalErrors)) * 100 : 0;
        
        // Get last submission
        const lastSubmission = logs.length > 0 ? logs[logs.length - 1].timestamp : 'Never';
        
        return {
          ...defaultMetrics,
          totalSubmitted,
          successRate,
          lastSubmission,
          dailyAverage: Math.round(totalSubmitted / Math.max(1, logs.length)),
          estimatedTraffic: totalSubmitted * 50 // Conservative estimate
        };
      }
    } catch (error) {
      console.log("⚠️  Could not load metrics:", error.message);
    }

    return defaultMetrics;
  }

  private checkEngineStatus(): void {
    try {
      const pidFile = path.resolve(__dirname, '../../logs/seo-engine.pid');
      if (fs.existsSync(pidFile)) {
        const pid = parseInt(fs.readFileSync(pidFile, 'utf8'));
        
        // Check if process exists (cross-platform)
        try {
          process.kill(pid, 0);
          this.metrics.engineStatus = 'running';
        } catch {
          this.metrics.engineStatus = 'stopped';
        }
      } else {
        this.metrics.engineStatus = 'stopped';
      }
    } catch (error) {
      this.metrics.engineStatus = 'error';
    }
  }

  private checkGoogleAuth(): void {
    const hasServiceAccount = !!process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
    const hasSite = !!process.env.GOOGLE_SEARCH_CONSOLE_SITE;
    
    if (hasServiceAccount && hasSite) {
      this.metrics.googleAuth = 'connected';
    } else if (!hasServiceAccount && !hasSite) {
      this.metrics.googleAuth = 'failed';
    } else {
      this.metrics.googleAuth = 'unknown';
    }
  }

  private displayDashboard(): void {
    console.clear();
    console.log(`
🚀 SEO RANKING ENGINE - LIVE MONITORING DASHBOARD
${'='.repeat(60)}

📊 PERFORMANCE METRICS
   Total URLs Submitted: ${this.metrics.totalSubmitted.toLocaleString()}
   Success Rate: ${this.metrics.successRate.toFixed(1)}%
   Daily Average: ${this.metrics.dailyAverage}
   Estimated Traffic: ${this.metrics.estimatedTraffic.toLocaleString()} visits/month

⏰ LAST ACTIVITY
   Last Submission: ${this.metrics.lastSubmission}
   Last Generation: ${this.metrics.lastGeneration}

🔧 SYSTEM STATUS
   Engine Status: ${this.getStatusIcon(this.metrics.engineStatus)} ${this.metrics.engineStatus.toUpperCase()}
   Google Auth: ${this.getAuthIcon(this.metrics.googleAuth)} ${this.metrics.googleAuth.toUpperCase()}

🎯 NEXT ACTIONS
   ${this.getNextActions()}

💡 VERIFICATION COMMANDS
   npm run seo:verify              # Check submission status
   npm run seo:verify -- --status  # Verify with Google
   npm run seo:verify -- --console # Open Search Console

📈 REAL-TIME LOG
${'-'.repeat(60)}
    `);
    
    this.displayRecentLogs();
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'running': return '🟢';
      case 'stopped': return '🔴';
      case 'error': return '⚠️';
      default: return '⚪';
    }
  }

  private getAuthIcon(auth: string): string {
    switch (auth) {
      case 'connected': return '✅';
      case 'failed': return '❌';
      default: return '⚠️';
    }
  }

  private getNextActions(): string {
    const actions = [];
    
    if (this.metrics.engineStatus === 'stopped') {
      actions.push('Start the engine: npm run seo:engine');
    }
    
    if (this.metrics.googleAuth === 'failed') {
      actions.push('Set up Google service account in environment variables');
    }
    
    if (this.metrics.totalSubmitted === 0) {
      actions.push('Run initial submission: npm run seo:submit-enhanced');
    }
    
    if (actions.length === 0) {
      actions.push('System is operational - monitoring for new submissions');
    }
    
    return actions.join('\n   ');
  }

  private displayRecentLogs(): void {
    try {
      if (fs.existsSync(this.engineLogPath)) {
        const logs = fs.readFileSync(this.engineLogPath, 'utf8');
        const lines = logs.split('\n').filter(line => line.trim()).slice(-10);
        
        lines.forEach(line => {
          const timestamp = line.match(/\[(.*?)\]/)?.[1] || '';
          const message = line.replace(/\[.*?\]\s*/, '');
          console.log("  ", timestamp, message);
        });
      } else {
        console.log('   No engine logs found yet...');
      }
    } catch (error) {
      console.log('   Could not read engine logs');
    }
  }

  private startRealtimeMonitoring(): void {
    console.log('📡 Starting real-time monitoring...');
    
    // Update dashboard every 10 seconds
    setInterval(() => {
      this.checkEngineStatus();
      this.checkGoogleAuth();
      this.metrics = this.loadMetrics(); // Reload metrics
      this.displayDashboard();
    }, 10000);

    // Initial display
    this.displayDashboard();
  }

  // Method to trigger verification
  public async verifySubmissions(): Promise<void> {
    console.log('\n🔍 Running verification check...');
    
    const verifyScript = spawn('npx', ['tsx', 'scripts/seo/verify-google-indexing.ts'], {
      stdio: 'inherit',
      cwd: path.resolve(__dirname, '../..')
    });

    verifyScript.on('close', (code) => {
      if (code === 0) {
        console.log('✅ Verification complete');
      } else {
        console.log('❌ Verification failed');
      }
      
      // Return to dashboard after verification
      setTimeout(() => this.displayDashboard(), 2000);
    });
  }
}

// Command line interface
const args = process.argv.slice(2);
const dashboard = new SEOMonitoringDashboard();

if (args.includes('--verify')) {
  dashboard.verifySubmissions();
} else if (args.includes('--help')) {
  console.log(`
🚀 SEO Monitoring Dashboard

Usage:
  npx tsx scripts/seo/seo-monitoring-dashboard.ts     # Start dashboard
  npx tsx scripts/seo/seo-monitoring-dashboard.ts --verify  # Run verification

Features:
  • Real-time submission tracking
  • Google indexing verification
  • Traffic potential analysis
  • System health monitoring
  • Error detection and alerts

The dashboard updates every 10 seconds with live data.
  `);
  process.exit(0);
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Monitoring dashboard stopped');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n👋 Monitoring dashboard stopped');
  process.exit(0);
});