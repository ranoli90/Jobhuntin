import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Progress } from '@/components/ui/Progress';
import { CheckCircle, AlertCircle, Clock, RefreshCw, Trash2 } from 'lucide-react';

interface DLQItem {
  id: string;
  application_id: string;
  failure_reason: string;
  attempt_count: number;
  max_retries: number;
  next_retry_at?: string;
  created_at: string;
  status: 'pending' | 'retrying' | 'completed' | 'failed';
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

interface DLQDashboardProps {
  tenantId: string;
  isAdmin?: boolean;
}

export const DLQDashboard: React.FC<DLQDashboardProps> = ({ tenantId, isAdmin = false }) => {
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

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [tenantId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch DLQ items
      const dlqResponse = await fetch('/api/admin/dlq/items', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!dlqResponse.ok) throw new Error('Failed to fetch DLQ items');
      const dlqData = await dlqResponse.json();
      setDLQItems(dlqData);

      // Fetch concurrent usage
      const concurrentResponse = await fetch('/api/admin/dlq/concurrent-usage', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!concurrentResponse.ok) throw new Error('Failed to fetch concurrent usage');
      const concurrentData = await concurrentResponse.json();

      // Fetch stats
      const statsResponse = await fetch('/api/admin/dlq/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!statsResponse.ok) throw new Error('Failed to fetch stats');
      const statsData = await statsResponse.json();

      setStats({
        totalDLQItems: statsData.total_items || 0,
        pendingItems: statsData.pending_count || 0,
        retryingItems: statsData.retrying_count || 0,
        failedItems: statsData.failed_count || 0,
        activeSessions: concurrentData.total_active || 0,
        maxConcurrent: concurrentData.max_concurrent || 10,
        currentConcurrent: concurrentData.total_active || 0,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryItem = async (itemId: string, force = false) => {
    try {
      const response = await fetch(`/api/admin/dlq/retry/${itemId}${force ? '?force=true' : ''}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to retry item');

      // Refresh data
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry item');
    }
  };

  const handleBulkRetry = async (itemIds: string[], force = false) => {
    try {
      const response = await fetch('/api/admin/dlq/retry', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_ids: itemIds,
          force,
        }),
      });

      if (!response.ok) throw new Error('Failed to bulk retry');

      // Refresh data
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to bulk retry');
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!confirm('Are you sure you want to delete this DLQ item?')) return;

    try {
      const response = await fetch(`/api/admin/dlq/items/${itemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete item');

      // Refresh data
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete item');
    }
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
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="dlq" className="space-y-4">
        <TabsList>
          <TabsTrigger value="dlq">Dead Letter Queue</TabsTrigger>
          <TabsTrigger value="concurrent">Concurrent Usage</TabsTrigger>
        </TabsList>

        <TabsContent value="dlq" className="space-y-4">
          {/* Bulk Actions */}
          <div className="flex justify-between items-center">
            <div className="space-x-2">
              <Button
                onClick={() => handleBulkRetry(dlqItems.filter(item => item.status === 'pending').map(item => item.id))}
                disabled={dlqItems.filter(item => item.status === 'pending').length === 0}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry All Pending
              </Button>
              <Button
                variant="outline"
                onClick={() => handleBulkRetry(dlqItems.filter(item => item.status === 'failed').map(item => item.id), true)}
                disabled={dlqItems.filter(item => item.status === 'failed').length === 0}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Force Retry Failed
              </Button>
            </div>
            <Button onClick={fetchData} variant="outline" size="sm">
              Refresh
            </Button>
          </div>

          {/* DLQ Items List */}
          <div className="space-y-4">
            {dlqItems.map((item) => (
              <Card key={item.id}>
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
        </TabsContent>

        <TabsContent value="concurrent" className="space-y-4">
          {/* Concurrent Usage Overview */}
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

          {/* Active Sessions */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Active Sessions</h3>
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
        </TabsContent>
      </Tabs>
    </div>
  );
};
