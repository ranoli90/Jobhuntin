import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Clock,
  Activity,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Download,
  Settings,
  Eye,
  EyeOff,
  Calendar
} from 'lucide-react';

interface PerformanceMetric {
  metric_id: string;
  application_id?: string;
  metric_type: string;
  metric_value: number;
  metric_unit: string;
  metadata: Record<string, any>;
  created_at: string;
}

interface PerformanceStats {
  total_metrics: number;
  by_type: Record<string, number>;
  average_values: Record<string, number>;
  trends: Record<string, 'up' | 'down' | 'stable'>;
}

const PerformanceMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [stats, setStats] = useState<PerformanceStats>({
    total_metrics: 0,
    by_type: {},
    average_values: {},
    trends: {},
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchMetrics();
    fetchStats();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchMetrics();
        fetchStats();
      }, 15000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedType, dateRange]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/performance-metrics/list', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch metrics');
      const data = await response.json();
      setMetrics(data.metrics || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/performance-metrics/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data.stats || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    }
  };

  const handleRecordMetric = async (metricType: string, value: number, unit: string) => {
    try {
      const response = await fetch('/api/performance-metrics/record', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          metric_type: metricType,
          metric_value: value,
          metric_unit: unit,
        }),
      });

      if (!response.ok) throw new Error('Failed to record metric');
      
      await fetchMetrics();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record metric');
    }
  };

  const getMetricIcon = (metricType: string) => {
    const icons = {
      button_detection_accuracy: '🎯',
      form_field_detection_accuracy: '📝',
      screenshot_capture_time: '📸',
      processing_time: '⚡',
      success_rate: '✅',
      error_rate: '❌',
      concurrent_sessions: '👥',
      memory_usage: '💾',
      cpu_usage: '🔥',
    };
    return icons[metricType] || '📊';
  };

  const getMetricColor = (metricType: string) => {
    const colors = {
      button_detection_accuracy: 'text-green-600',
      form_field_detection_accuracy: 'text-green-600',
      screenshot_capture_time: 'text-blue-600',
      processing_time: 'text-purple-600',
      success_rate: 'text-green-600',
      error_rate: 'text-red-600',
      concurrent_sessions: 'text-blue-600',
      memory_usage: 'text-orange-600',
      cpu_usage: 'text-red-600',
    };
    return colors[metricType] || 'text-gray-600';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    const icons = {
      up: <TrendingUp className="h-4 w-4 text-green-600" />,
      down: <TrendingDown className="h-4 w-4 text-red-600" />,
      stable: <Activity className="h-4 w-4 text-gray-600" />,
    };
    return icons[trend] || <Activity className="h-4 w-4 text-gray-600" />;
  };

  const formatValue = (value: number, unit: string) => {
    if (unit === 'percentage') return `${value}%`;
    if (unit === 'milliseconds') return `${value}ms`;
    if (unit === 'seconds') return `${value}s`;
    if (unit === 'count') return value.toString();
    if (unit === 'megabytes') return `${value}MB`;
    return `${value} ${unit}`;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    
    if (diffSeconds < 60) return 'Just now';
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`;
    if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
    return `${Math.floor(diffSeconds / 86400)} days ago`;
  };

  const getTrendColor = (trend: 'up' | 'down' | 'stable') => {
    const colors = {
      up: 'text-green-600',
      down: 'text-red-600',
      stable: 'text-gray-600',
    };
    return colors[trend] || 'text-gray-600';
  };

  const filteredMetrics = selectedType === 'all' 
    ? metrics 
    : metrics.filter(metric => metric.metric_type === selectedType);

  const recentMetrics = filteredMetrics.slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Performance Metrics</h1>
          <p className="text-gray-600">Monitor agent performance and system metrics</p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={() => handleRecordMetric('processing_time', 0, 'seconds')}
            size="sm"
          >
            <Activity className="h-4 w-4 mr-2" />
            Record Metric
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh' : 'Manual refresh'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStats}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Refresh Stats
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {showDetails ? 'Hide Details' : 'Show Details'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_metrics}</div>
            <div className="text-sm text-gray-500">
              All recorded metrics
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text font-medium">Average Processing Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {formatValue(stats.average_values.processing_time || 0, 'seconds')}
            </div>
            <div className="text-sm text-gray-500">
              Per application
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatValue(stats.average_values.success_rate || 0, 'percentage')}
            </div>
            <div className="text-sm text-gray-500">
              Overall success rate
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text font-medium">Error Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatValue(stats.average_values.error_rate || 0, 'percentage')}
            </div>
            <div className="text-sm text-gray-500">
              Overall error rate
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metric Type Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Filter by Type</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedType === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('all')}
            >
              All Types
            </Button>
            {Object.keys(stats.by_type).map((type) => (
              <Button
                key={type}
                variant={selectedType === type ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedType(type)}
              >
                <span className="mr-1">{getMetricIcon(type)}</span>
                {type.replace(/_/g, ' ').toUpperCase()}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentMetrics.map((metric) => (
              <Card key={metric.metric_id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getMetricIcon(metric.metric_type)}</div>
                    <div className="flex-1">
                      <h4 className="font-medium">{metric.metric_type.replace(/_/g, ' ').toUpperCase()}</h4>
                      <p className="text-sm text-gray-500">
                        {formatTimeAgo(metric.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getMetricColor(metric.metric_type)}>
                      {formatValue(metric.metric_value, metric.metric_unit)}
                    </Badge>
                    <div className="text-sm text-gray-500">
                      {metric.application_id ? `App: ${metric.application_id.slice(0, 8)}...` : 'System'}
                    </div>
                  </div>
                </div>

                {/* Details */}
                {showDetails && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>Details:</strong>
                  </p>
                  <div className="space-y-1">
                    <div className="text-sm">
                      <span className="font-medium">Metric ID:</span>
                      <span className="text-gray-700 ml-2">{metric.metric_id}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Application ID:</span>
                      <span className="text-gray-700 ml-2">{metric.application_id || 'N/A'}</span>
                    </div>
                    {Object.entries(metric.metadata).length > 0 && (
                      <div className="text-sm">
                        <span className="font-medium">Metadata:</span>
                        <div className="text-gray-700 ml-2">
                          <pre className="text-xs bg-gray-100 p-2 rounded">
                            {JSON.stringify(metric.metadata, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                )}
              </Card>
            ))}
          </div>
          
          {recentMetrics.length === 0 && (
            <div className="text-center py-8">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No metrics recorded yet</p>
              <p className="text-sm text-gray-400 mt-2">
                Record metrics to start monitoring performance
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Trends */}
      {showDetails && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.trends).map(([type, trend]) => (
                <div key={type} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getMetricIcon(type)}</div>
                    <div>
                      <h4 className="font-medium">{type.replace(/_/g, ' ').toUpperCase()}</h4>
                      <p className="text-sm text-gray-500">
                        {stats.average_values[type] ? formatValue(stats.average_values[type], getUnitByType(type)) : 'N/A'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getTrendIcon(trend)}
                    <span className={`text-sm ${getTrendColor(trend)}`}>
                      {trend === 'up' ? 'Improving' : trend === 'down' ? 'Declining' : 'Stable'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

function getUnitByType(metricType: string): string {
  const units = {
    button_detection_accuracy: 'percentage',
    form_field_detection_accuracy: 'percentage',
    screenshot_capture_time: 'milliseconds',
    processing_time: 'seconds',
    success_rate: 'percentage',
    error_rate: 'percentage',
    concurrent_sessions: 'count',
    memory_usage: 'megabytes',
    cpu_usage: 'percentage',
  };
  return units[metricType] || 'count';
}

export default PerformanceMetrics;
