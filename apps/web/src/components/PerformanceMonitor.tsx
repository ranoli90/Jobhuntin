/**
 * Performance Monitoring Component
 * 
 * Monitors and reports on frontend performance metrics including:
 * - Core Web Vitals (LCP, FID, CLS)
 * - Component render performance
 * - Memory usage
 * - Network performance
 * - Error rates
 */

import * as React from "react";
import { BarChart3, Activity, AlertCircle, TrendingUp } from "lucide-react";

// Performance Observer entry type definitions
interface LayoutShiftEntry extends PerformanceEntry {
  value: number;
  hadRecentInput: boolean;
}

interface FirstInputEntry extends PerformanceEntry {
  processingStart: number;
}

interface PerformanceMemory {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

declare global {
  interface Performance {
    memory?: PerformanceMemory;
  }
}

interface PerformanceMetrics {
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  fcp: number; // First Contentful Paint
  ttfb: number; // Time to First Byte
  memoryUsage: number;
  renderTime: number;
  errorCount: number;
  networkRequests: number;
}

interface PerformanceMonitorProps {
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void;
  reportToService?: boolean;
  enableReporting?: boolean;
}

export class PerformanceMonitor extends React.Component<PerformanceMonitorProps> {
  private observer: PerformanceObserver | null = null;
  private metrics: PerformanceMetrics = {
    lcp: 0,
    fid: 0,
    cls: 0,
    fcp: 0,
    ttfb: 0,
    memoryUsage: 0,
    renderTime: 0,
    errorCount: 0,
    networkRequests: 0,
  };
  private renderStartTime: number = 0;
  private errorCount: number = 0;

  componentDidMount() {
    this.renderStartTime = performance.now();
    this.initializePerformanceMonitoring();
    this.setupErrorTracking();
    this.setupNetworkTracking();
    this.startMetricsCollection();
  }

  componentWillUnmount() {
    this.cleanup();
  }

  private initializePerformanceMonitoring = () => {
    if ('PerformanceObserver' in window) {
      // Monitor Core Web Vitals
      this.observer = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        
        entries.forEach((entry) => {
          switch (entry.entryType) {
            case 'largest-contentful-paint':
              this.metrics.lcp = entry.startTime;
              break;
            case 'first-input':
              this.metrics.fid = (entry as FirstInputEntry).processingStart - entry.startTime;
              break;
            case 'layout-shift':
              if (!(entry as LayoutShiftEntry).hadRecentInput) {
                this.metrics.cls += (entry as LayoutShiftEntry).value;
              }
              break;
            case 'first-contentful-paint':
              this.metrics.fcp = entry.startTime;
              break;
            case 'navigation':
              const navEntry = entry as PerformanceNavigationTiming;
              this.metrics.ttfb = navEntry.responseStart - navEntry.requestStart;
              break;
          }
        });

        this.updateMetrics();
      });

      // Observe all performance entry types
      this.observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift', 'first-contentful-paint', 'navigation'] });
    }
  };

  private setupErrorTracking = () => {
    // Track JavaScript errors
    window.addEventListener('error', (event) => {
      this.errorCount++;
      this.metrics.errorCount = this.errorCount;
      this.updateMetrics();
      this.reportError('javascript', event.error);
    });

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.errorCount++;
      this.metrics.errorCount = this.errorCount;
      this.updateMetrics();
      this.reportError('promise', event.reason);
    });
  };

  private setupNetworkTracking = () => {
    // Track network requests
    if ('PerformanceObserver' in window) {
      const networkObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        this.metrics.networkRequests += entries.length;
        this.updateMetrics();
      });

      networkObserver.observe({ entryTypes: ['resource'] });
    }
  };

  private startMetricsCollection = () => {
    // Collect metrics every 5 seconds
    const interval = setInterval(() => {
      this.collectMemoryMetrics();
      this.updateMetrics();
    }, 5000);

    // Cleanup on unmount
    return () => clearInterval(interval);
  };

  private collectMemoryMetrics = () => {
    if (performance.memory) {
      this.metrics.memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
    }
  };

  private updateMetrics = () => {
    const renderTime = performance.now() - this.renderStartTime;
    this.metrics.renderTime = renderTime;

    if (this.props.onMetricsUpdate) {
      this.props.onMetricsUpdate(this.metrics);
    }

    if (this.props.reportToService && this.props.enableReporting) {
      this.reportMetrics();
    }
  };

  private reportMetrics = async () => {
    try {
      await fetch('/api/performance-metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...this.metrics,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      });
    } catch (error) {
      console.warn('Failed to report performance metrics:', error);
    }
  };

  private reportError = (type: string, error: Error | unknown) => {
    if (!this.props.reportToService || !this.props.enableReporting) return;

    try {
      fetch('/api/performance-errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          error: error?.message || error,
          stack: error?.stack,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
        }),
      });
    } catch (reportingError) {
      console.warn('Failed to report performance error:', reportingError);
    }
  };

  private cleanup = () => {
    if (this.observer) {
      this.observer.disconnect();
    }
  };

  render() {
    return null; // This component doesn't render anything
  }
}

/**
 * Performance Dashboard Component
 * Displays real-time performance metrics
 */
export function PerformanceDashboard() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    // Only show in development
    if (import.meta.env.DEV) {
      setIsVisible(true);
    }
  }, []);

  if (!isVisible || !metrics) return null;

  const getScoreColor = (score: number, thresholds: { good: number; needsImprovement: number }) => {
    if (score <= thresholds.good) return 'text-green-600';
    if (score <= thresholds.needsImprovement) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMetricStatus = (value: number, thresholds: { good: number; needsImprovement: number }) => {
    if (value <= thresholds.good) return 'Good';
    if (value <= thresholds.needsImprovement) return 'Needs Improvement';
    return 'Poor';
  };

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-80 z-50">
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-blue-600" />
        <h3 className="font-semibold text-gray-900">Performance Metrics</h3>
      </div>

      <div className="space-y-2 text-sm">
        {/* Core Web Vitals */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600">LCP:</span>
          <span className={getScoreColor(metrics.lcp, { good: 2500, needsImprovement: 4000 })}>
            {metrics.lcp.toFixed(0)}ms ({getMetricStatus(metrics.lcp, { good: 2500, needsImprovement: 4000 })})
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">FID:</span>
          <span className={getScoreColor(metrics.fid, { good: 100, needsImprovement: 300 })}>
            {metrics.fid.toFixed(0)}ms ({getMetricStatus(metrics.fid, { good: 100, needsImprovement: 300 })})
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">CLS:</span>
          <span className={getScoreColor(metrics.cls, { good: 0.1, needsImprovement: 0.25 })}>
            {metrics.cls.toFixed(3)} ({getMetricStatus(metrics.cls, { good: 0.1, needsImprovement: 0.25 })})
          </span>
        </div>

        {/* Additional Metrics */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600">FCP:</span>
          <span className={getScoreColor(metrics.fcp, { good: 1800, needsImprovement: 3000 })}>
            {metrics.fcp.toFixed(0)}ms
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">TTFB:</span>
          <span className={getScoreColor(metrics.ttfb, { good: 800, needsImprovement: 1800 })}>
            {metrics.ttfb.toFixed(0)}ms
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">Memory:</span>
          <span className={metrics.memoryUsage > 50 ? 'text-red-600' : 'text-green-600'}>
            {metrics.memoryUsage.toFixed(1)}MB
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">Render Time:</span>
          <span className={metrics.renderTime > 100 ? 'text-red-600' : 'text-green-600'}>
            {metrics.renderTime.toFixed(0)}ms
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">Errors:</span>
          <span className={metrics.errorCount > 0 ? 'text-red-600' : 'text-green-600'}>
            {metrics.errorCount}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">Network Requests:</span>
          <span className="text-blue-600">
            {metrics.networkRequests}
          </span>
        </div>
      </div>

      {/* Performance Score */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-gray-600">Overall Score:</span>
          <div className="flex items-center gap-1">
            <Activity className="w-4 h-4 text-blue-600" />
            <span className="font-semibold text-blue-600">
              {calculatePerformanceScore(metrics).toFixed(0)}/100
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Calculate overall performance score
 */
function calculatePerformanceScore(metrics: PerformanceMetrics): number {
  let score = 100;

  // LCP scoring (0-2500ms = 100, 2500-4000ms = 50-100, >4000ms = 0-50)
  if (metrics.lcp <= 2500) {
    score -= 0;
  } else if (metrics.lcp <= 4000) {
    score -= ((metrics.lcp - 2500) / 1500) * 25;
  } else {
    score -= 25;
  }

  // FID scoring (0-100ms = 100, 100-300ms = 50-100, >300ms = 0-50)
  if (metrics.fid <= 100) {
    score -= 0;
  } else if (metrics.fid <= 300) {
    score -= ((metrics.fid - 100) / 200) * 25;
  } else {
    score -= 25;
  }

  // CLS scoring (0-0.1 = 100, 0.1-0.25 = 50-100, >0.25 = 0-50)
  if (metrics.cls <= 0.1) {
    score -= 0;
  } else if (metrics.cls <= 0.25) {
    score -= ((metrics.cls - 0.1) / 0.15) * 25;
  } else {
    score -= 25;
  }

  // Memory usage scoring (0-50MB = 100, 50-100MB = 50-100, >100MB = 0-50)
  if (metrics.memoryUsage <= 50) {
    score -= 0;
  } else if (metrics.memoryUsage <= 100) {
    score -= ((metrics.memoryUsage - 50) / 50) * 15;
  } else {
    score -= 15;
  }

  // Error penalty
  score -= metrics.errorCount * 5;

  // Network request penalty (too many requests)
  if (metrics.networkRequests > 100) {
    score -= 10;
  }

  return Math.max(0, Math.min(100, score));
}

/**
 * Hook for performance monitoring
 */
export function usePerformanceMonitoring() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = React.useState(false);

  const startMonitoring = React.useCallback(() => {
    setIsMonitoring(true);
  }, []);

  const stopMonitoring = React.useCallback(() => {
    setIsMonitoring(false);
  }, []);

  const handleMetricsUpdate = React.useCallback((newMetrics: PerformanceMetrics) => {
    setMetrics(newMetrics);
  }, []);

  return {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    handleMetricsUpdate,
  };
}

/**
 * Performance optimization utilities
 */
export const performanceUtils = {
  /**
   * Debounce function for performance optimization
   */
  debounce: <Args extends unknown[], Return>(
    func: (...args: Args) => Return,
    wait: number
  ): ((...args: Args) => void) => {
    let timeout: ReturnType<typeof setTimeout>;
    return (...args: Args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  },

  /**
   * Throttle function for performance optimization
   */
  throttle: <Args extends unknown[], Return>(
    func: (...args: Args) => Return,
    limit: number
  ): ((...args: Args) => void) => {
    let inThrottle: boolean;
    return (...args: Args) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },

  /**
   * Lazy load component
   */
  lazyLoad: <T extends React.ComponentType<unknown>>(
    importFunc: () => Promise<{ default: T }>
  ) => {
    return React.lazy(importFunc);
  },

  /**
   * Memoize expensive calculations
   */
  memoize: <Args extends unknown[], Return>(func: (...args: Args) => Return): (...args: Args) => Return => {
    const cache = new Map<string, Return>();
    return (...args: Args) => {
      const key = JSON.stringify(args);
      if (cache.has(key)) {
        return cache.get(key)!;
      }
      const result = func(...args);
      cache.set(key, result);
      return result;
    };
  },
};
