import React, { useState, useEffect, useRef } from 'react';
import { apiGet, apiPost, apiDelete } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Progress } from '@/components/ui/Progress';
import { 
  RefreshCw, 
  Trash2, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  Download,
  Eye,
  Search,
  Filter
} from 'lucide-react';

interface DLQItem {
  id: string;
  application_id: string;
  failure_reason: string;
  attempt_count: number;
  max_retries: number;
  next_retry_at?: string;
  created_at: string;
  status: 'pending' | 'retrying' | 'completed' | 'failed';
  error_details: any;
}

interface ConcurrentUsageSession {
  session_id: string;
  user_id: string;
  application_id?: string;
  start_time: string;
  end_time?: string;
  status: 'active' | 'completed' | 'failed' | 'cancelled';
  steps_completed: number;
  total_steps: number;
  error_count: number;
  screenshots_captured: number;
  duration_seconds?: number;
}

const DLQDashboardPage: React.FC = () => {
  const [dlqItems, setDLQItems] = useState<DLQItem[]>([]);
  const [concurrentSessions, setConcurrentSessions] = useState<ConcurrentUsageSession[]>([]);
  const [stats, setStats] = useState({
    totalDLQItems: 0,
    pendingItems: 0,
    retryingItems: 0,
    failedItems: 0,
    activeSessions: 0,
    maxConcurrent: 10,
    currentConcurrent: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const consecutiveErrorsRef = useRef(0);
  const BASE_POLL_MS = 30000;
  const MAX_POLL_MS = 300000;

  const fetchData = async (): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      const [dlqData, concurrentData, statsData] = await Promise.all([
        apiGet<DLQItem[] | DLQItem>('admin/dlq/items').then((d) =>
          Array.isArray(d) ? (d as DLQItem[]) : ([d] as DLQItem[])
        ),
        apiGet<{ active_tasks?: ConcurrentUsageSession[]; total_active?: number; max_concurrent?: number }>(
          'admin/dlq/concurrent-usage'
        ),
        apiGet<{ total_items?: number; pending_count?: number; retrying_count?: number; failed_count?: number }>(
          'admin/dlq/stats'
        ),
      ]);

      setDLQItems(dlqData as DLQItem[]);
      setConcurrentSessions(concurrentData.active_tasks || []);

      setStats({
        totalDLQItems: statsData.total_items || 0,
        pendingItems: statsData.pending_count || 0,
        retryingItems: statsData.retrying_count || 0,
        failedItems: statsData.failed_count || 0,
        activeSessions: concurrentData.total_active || 0,
        maxConcurrent: concurrentData.max_concurrent || 10,
        currentConcurrent: concurrentData.total_active || 0,
      });
      consecutiveErrorsRef.current = 0;
      return true;
    } catch (err) {
      consecutiveErrorsRef.current += 1;
      setError(err instanceof Error ? err.message : 'An error occurred');
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;
    const scheduleNext = () => {
      if (cancelled) return;
      const delay = Math.min(
        BASE_POLL_MS * Math.pow(2, consecutiveErrorsRef.current),
        MAX_POLL_MS
      );
      timeoutId = setTimeout(() => {
        if (cancelled) return;
        fetchData().then(() => scheduleNext());
      }, delay);
    };
    fetchData().then(() => scheduleNext());
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, []);

  const handleRetryItem = async (itemId: string, force = false) => {
    try {
      await apiPost(
        `admin/dlq/retry/${itemId}${force ? '?force=true' : ''}`,
        undefined
      );
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry item');
    }
  };

  const handleBulkRetry = async (force = false) => {
    try {
      await apiPost('admin/dlq/retry', { item_ids: selectedItems, force });
      await fetchData();
      setSelectedItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk retry');
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!confirm('Are you sure you want to delete this DLQ item?')) return;

    try {
      await apiDelete(`admin/dlq/items/${itemId}`);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete item');
    }
  };

  const handleSelectItem = (itemId: string) => {
    setSelectedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'secondary',
      retrying: 'default',
      completed: 'success',
      failed: 'destructive',
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  const getRetryProgress = (item: DLQItem) => {
    return (item.attempt_count / item.max_retries) * 100;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dead Letter Queue</h1>
        <div className="flex space-x-2">
          <Button
            onClick={() => handleBulkRetry(false)}
            disabled={selectedItems.length === 0}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Selected ({selectedItems.length})
          </Button>
          <Button
            onClick={() => handleBulkRetry(true)}
            disabled={selectedItems.length === 0}
            variant="outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Force Retry Selected
          </Button>
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total DLQ Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDLQItems}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.pendingItems}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.failedItems}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.activeSessions}</div>
            <div className="text-sm text-gray-500">
              {stats.currentConcurrent}/{stats.maxConcurrent}
            </div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* DLQ Items */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">DLQ Items</h2>
          <div className="text-sm text-gray-500">
            {dlqItems.length} items
          </div>
        </div>

        {dlqItems.map((item) => (
          <Card key={item.id} className={selectedItems.includes(item.id) ? 'ring-2 ring-blue-500' : ''}>
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(item.status)}
                    <span className="text-sm text-gray-500">
                      Application ID: {item.application_id}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium">{item.failure_reason}</p>
                    <p className="text-sm text-gray-500">
                      Created: {new Date(item.created_at).toLocaleString()}
                    </p>
                    {item.next_retry_at && (
                      <p className="text-sm text-gray-500">
                        Next retry: {new Date(item.next_retry_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(item.id)}
                    onChange={() => handleSelectItem(item.id)}
                    className="rounded"
                  />
                  {item.status === 'pending' && (
                    <Button
                      size="sm"
                      onClick={() => handleRetryItem(item.id)}
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Retry
                    </Button>
                  )}
                  {item.status === 'failed' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRetryItem(item.id, true)}
                    >
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Force Retry
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeleteItem(item.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Retry Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Retry Progress</span>
                  <span>{item.attempt_count}/{item.max_retries}</span>
                </div>
                <Progress value={getRetryProgress(item)} className="h-2" />
              </div>
            </CardContent>
          </Card>
        ))}
        
        {dlqItems.length === 0 && (
          <Card>
            <CardContent className="p-6 text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-gray-500">No items in the Dead Letter Queue</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Concurrent Usage */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Concurrent Usage</h2>
          <div className="text-sm text-gray-500">
            {concurrentSessions.length} active sessions
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Concurrent Usage Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Current Usage</span>
                  <span>{stats.currentConcurrent}/{stats.maxConcurrent}</span>
                </div>
                <Progress value={(stats.currentConcurrent / stats.maxConcurrent) * 100} className="h-2" />
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Active Sessions:</span>
                  <span className="ml-2 font-medium">{stats.activeSessions}</span>
                </div>
                <div>
                  <span className="text-gray-500">Max Concurrent:</span>
                  <span className="ml-2 font-medium">{stats.maxConcurrent}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {concurrentSessions.map((session) => (
          <Card key={session.session_id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(session.status)}
                    <span className="text-sm font-medium">
                      Session: {session.session_id.slice(0, 8)}...
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    <p>Started: {new Date(session.start_time).toLocaleString()}</p>
                    {session.duration_seconds && (
                      <p>Duration: {Math.floor(session.duration_seconds / 60)}m {session.duration_seconds % 60}s</p>
                    )}
                    <p>Progress: {session.steps_completed}/{session.total_steps} steps</p>
                    {session.error_count > 0 && (
                      <p className="text-red-500">Errors: {session.error_count}</p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {concurrentSessions.length === 0 && (
          <Card>
            <CardContent className="p-6 text-center">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No active sessions</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default DLQDashboardPage;
