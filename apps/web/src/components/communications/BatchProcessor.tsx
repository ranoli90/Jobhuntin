import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Send, 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  Settings, 
  RefreshCw,
  Search,
  Filter,
  Play,
  Pause,
  RotateCcw,
  Users,
  Mail,
  Activity,
  Zap,
  Download,
  Trash2
} from 'lucide-react';

interface NotificationBatch {
  id: string;
  name: string;
  tenant_id: string;
  user_ids: string[];
  batch_size: number;
  priority: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface BatchProcessingResult {
  batch_id: string;
  total_users: number;
  successful: number;
  failed: number;
  skipped: number;
  processing_time_seconds: number;
  error_details: Array<{
    user_id: string;
    error: string;
  }>;
  created_at: string;
}

interface UserNotificationBatch {
  id: string;
  batch_id: string;
  user_id: string;
  tenant_id: string;
  notification_data: Record<string, any>;
  status: string;
  error_message: string | null;
  processing_attempts: number;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
}

interface BatchProcessingStats {
  total_processed: number;
  successful: number;
  failed: number;
  skipped: number;
  average_processing_time: number;
  total_batches: number;
  completed_batches: number;
  total_notifications: number;
  average_processing_time: number;
}

const BatchProcessor: React.FC = () => {
  const [batches, setBatches] = useState<NotificationBatch[]>([]);
  const [batchResults, setBatchResults] = useState<BatchProcessingResult[]>([]);
  const [stats, setStats] = useState<BatchProcessingStats | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showCreateBatch, setShowCreateBatch] = useState(false);
  const [showBatchDetails, setShowBatchDetails] = useState(false);
  const [showRetryFailed, setShowRetryFailed] = useState(false);

  // Create batch form state
  const [batchForm, setBatchForm] = useState({
    name: '',
    tenant_id: '',
    user_ids: [],
    notification_template: {
      title: '',
      message: '',
      category: 'general',
      priority: 'medium',
      channels: ['in_app'],
      data: {},
    },
    batch_size: 100,
    priority: 'medium',
  });

  useEffect(() => {
    fetchBatches();
    fetchBatchResults();
    fetchStats();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchBatches();
        fetchBatchResults();
        fetchStats();
      }, 20000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchBatches = async () => {
    try {
      const response = await fetch('/api/communications/batch/history?limit=50', {
        headers: {
          'content-type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch batches');
      const data = await response.json();
      setBatches(data.batches || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batches');
    } finally {
      setLoading(false);
    }
  };

  const fetchBatchResults = async () => {
    try {
      // This would normally fetch from the API
      // For now, we'll simulate some batch results
      const mockResults: BatchProcessingResult[] = [
        {
          batch_id: '1',
          total_users: 100,
          successful: 95,
          failed: 3,
          skipped: 2,
          processing_time_seconds: 45.2,
          error_details: [],
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          batch_id: '2',
          total_users: 50,
          successful: 48,
          failed: 2,
          skipped: 0,
          processing_time_seconds: 23.7,
          error_details: [],
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ];
      
      setBatchResults(mockResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batch results');
    }
  };

  const fetchStats = async () => {
    try {
      // This would normally fetch from the API
      // For now, we'll simulate some stats
      const mockStats: BatchProcessingStats = {
        total_processed: 150,
        successful: 143,
        failed: 5,
        skipped: 2,
        average_processing_time: 34.5,
        total_batches: 2,
        completed_batches: 2,
        total_notifications: 150,
        average_processing_time: 34.5,
      };
      
      setStats(mockStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    }
  };

  const handleCreateBatch = async () => {
    try {
      // In a real implementation, this would get user IDs from the API
      // For now, we'll use mock user IDs
      const mockUserIds = Array.from({ length: batchForm.batch_size }, (_, i) => `user_${i + 1}`);

      const response = await fetch('/api/communications/batch/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: batchForm.name,
          tenant_id: batchForm.tenant_id || 'default',
          user_ids: mockUserIds,
          notification_template: batchForm.notification_template,
          batch_size: batchForm.batch_size,
          priority: batchForm.priority,
        }),
      });

      if (!response.ok) throw new Error('Failed to create batch');
      
      await fetchBatches();
      setShowCreateBatch(false);
      setBatchForm({
        name: '',
        tenant_id: '',
        user_ids: [],
        notification_template: {
          title: '',
          message: '',
          category: 'general',
          priority: 'medium',
          channels: ['in_app'],
          data: {},
        },
        batch_size: 100,
        priority: 'medium',
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create batch');
    }
  };

  const handleProcessBatch = async (batchId: string) => {
    try {
      const response = await fetch(`/api/communications/batch/process/${batchId}`, {
        method: 'POST',
        headers: {
          'Authorization': `batch_id=${batchId}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to process batch');
      
      await fetchBatches();
      await fetchBatchResults();
      await fetchStats();
      
      // Show success message
      alert(`Batch ${batchId} processed successfully`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process batch');
    }
  };

  const handleRetryFailed = async (batchId: string) => {
    try {
      const response = await fetch(`/api/communications/batch/retry/${batchId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to retry failed notifications');
      
      await fetchBatches();
      await fetchBatchResults();
      
      const data = await response.json();
      
      alert(`Retried ${data.successful} failed notifications`);
      setShowRetryFailed(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retry failed notifications');
    }
  };

  const handleCancelBatch = async (batchId: string) => {
    try {
      if (!confirm('Are you sure you want to cancel this batch?')) return;

      const response = await fetch(`/api/communications/batch/cancel/${batchId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to cancel batch');
      
      await fetchBatches();
      alert(`Batch ${batchId} cancelled`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel batch');
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      pending: <Clock className="h-4 w-4" />,
      processing: <RefreshCw className="h-4 w-4" />,
      completed: <CheckCircle className="h-4 w-4" />,
      cancelled: <Trash2 className="h-4 w-4" />,
    };
    return icons[status] || <Clock className="h-4 w-4" />;
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800',
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
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

  const getBatchStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getBatchStatusIcon = (status: string) => {
    const icons = {
      pending: <Clock className="h-4 w-4" />,
      processing: <RefreshCw className="h-4 w-4" />,
      completed: <CheckCircle className="h-4 w-4" />,
      cancelled: <Trash2 className="h-4 w-4" />,
    };
    return icons[status] || <Clock className="h-4 w-4" />;
  };

  const filteredBatches = selectedBatch 
    ? batches.filter(batch => batch.id === selectedBatch)
    : batches;

  const selectedBatchData = selectedBatch ? batches.find(batch => batch.id === selectedBatch) : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Batch Processor</h1>
          <p className="text-6">Process notifications in batches with intelligent throttling and error handling</p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowCreateBatch(true)}>
            <Send className="h-4 w-4 mr-2" />
            Create Batch
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh' : 'Manual refresh'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Batch Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Processed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_processed}</div>
              <div className="text-sm text-gray-500">
                All notifications
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.total_processed > 0 
                  ? ((stats.successful / stats.total_processed) * 100).toFixed(1)
                  : '0.0'
                }%
              </div>
              <div className="text-sm text-gray-500">
                {stats.successful}/{stats.total_processed}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Failed Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.total_processed > 0 
                  ? ((stats.failed / stats.total_processed) * 100).toFixed(1)
                  : '0.0'
                }%
              </div>
              <div className="text-sm text-gray-500">
                {stats.failed}/{stats.total_processed}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {stats.average_processing_time}s
              </div>
              <div className="text-sm text-gray-500">
                Per batch
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Batch Modal */}
      {showCreateBatch && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Create Notification Batch</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="batch-name">Batch Name</Label>
                <Input
                  id="batch-name"
                  placeholder="Enter batch name"
                  value={batchForm.name}
                  onChange={(e) => setBatchForm({ ...batchForm, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch-size">Batch Size</Label>
                <Select value={batchForm.batch_size.toString()} onValueChange={(value) => setBatchForm({ ...batchForm, batch_size: parseInt(value) })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50 notifications</SelectItem>
                    <SelectItem value="100">100 notifications</SelectItem>
                    <SelectItem value="200">200 notifications</SelectItem>
                    <SelectItem value="500">500 notifications</SelectItem>
                    <SelectItem value="1000">1000 notifications</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="batch-priority">Priority</Label>
                  <Select value={batchForm.priority} onValueChange={(value) => setBatchForm({ ...batchForm, priority: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="batch-category">Category</Label>
                  <Select value={batchForm.notification_template.category} onValueChange={(value) => setBatchForm({
                    ...batchForm,
                    notification_template: {
                      ...batchForm.notification_template,
                      category: value,
                    },
                  })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="application_status">Application Status</SelectItem>
                      <SelectItem value="job_matches">Job Matches</SelectItem>
                      <SelectItem value="security">Security</SelectItem>
                      <SelectItem value="marketing">Marketing</SelectItem>
                      <SelectItem value="usage_limits">Usage Limits</SelectItem>
                      <SelectItem value="reminders">Reminders</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch-template">Notification Template</Label>
                <Textarea
                  id="batch-template"
                  placeholder="Notification title"
                  rows={3}
                  value={batchForm.notification_template.title}
                  onChange={(e) => setBatchForm({
                    ...batchForm,
                    notification_template: {
                      ...batchForm.notification_template,
                      title: e.target.value,
                    },
                  })}
                />
              </div>

              <div className="flex space-x-2">
                <Button onClick={handleCreateBatch} disabled={!batchForm.name || !batchForm.notification_template.title}>
                  <Send className="h-4 w-4 mr-2" />
                  Create Batch
                </Button>
                <Button variant="outline" onClick={() => setShowCreateBatch(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Batch List */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Batches</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {batches.map((batch) => (
              <Card key={batch.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-1">
                      <h4 className="font-medium">{batch.name}</h4>
                      <p className="text-sm text-gray-500">
                        {batch.user_ids.length} users
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge className={getBatchStatusColor(batch.status)}>
                          {batch.status}
                        </Badge>
                        <Badge className={getPriorityColor(batch.priority)}>
                          {batch.priority}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="text-sm text-gray-500">
                      {formatTimeAgo(batch.created_at)}
                    </div>
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedBatch(batch.id)}
                      >
                        <Eye className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleProcessBatch(batch.id)}
                        disabled={batch.status !== 'pending'}
                      >
                        {batch.status === 'pending' ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
                      </Button>
                      {batch.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCancelBatch(batch.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
              
              {batches.length === 0 && (
                <div className="text-center py-8">
                  <Send className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No notification batches created yet</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Click "Create Batch" to start processing notifications in batches
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Batch Details Modal */}
      {showBatchDetails && selectedBatchData && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Batch Details</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="results">Results</TabsTrigger>
                <TabsTrigger value="users">Users</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Batch ID</Label>
                      <Input value={selectedBatchData.id} readOnly />
                    </div>
                    <div className="space-y-2">
                      <Label>Name</Label>
                      <Input value={selectedBatchData.name} readOnly />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Users Count</Label>
                      <Input value={selectedBatchData.user_ids.length} readOnly />
                    </div>
                    <div className="space-y-2">
                      <Label>Batch Size</Label>
                      <Input value={selectedBatchData.batch_size} readOnly />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <Select value={selectedBatchData.priority} disabled>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="critical">Critical</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="low">Low</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={selectedBatchData.status} disabled>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="processing">Processing</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Created At</Label>
                    <Input value={formatTimeAgo(selectedBatchData.created_at)} readOnly />
                  </div>

                  <div className="space-y-2">
                    <Label>Updated At</Label>
                    <Input value={formatTimeAgo(selectedBatchData.updated_at)} readOnly />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="results">
                <div className="space-y-4">
                  {batchResults
                    .filter(result => result.batch_id === selectedBatchData.id)
                    .map((result) => (
                      <Card key={result.batch_id} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="flex-1">
                              <h4 className="font-medium">Processing Result</h4>
                              <p className="text-sm text-gray-500">
                                {result.processing_time_seconds.toFixed(2)}s
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <div className="text-sm text-gray-500">
                              {result.total_users} users
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="text-green-600">
                                {result.successful}
                              </span>
                              <span className="text-red-600">
                                {result.failed}
                              </span>
                              <span className="text-gray-600">
                                {result.skipped}
                              </span>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                    
                    {batchResults.length === 0 && (
                      <div className="text-center py-4">
                        <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-500">No processing results yet</p>
                      </div>
                    )}
                  </div>
                </TabsContent>

              <TabsContent value="users">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>User Count</Label>
                    <Input value={selectedBatchData.user_ids.length} readOnly />
                  </div>
                  <div className="space-y-2">
                    <Label>Users List</Label>
                    <div className="bg-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto">
                      {selectedBatchData.user_ids.map((userId, index) => (
                        <div key={userId} className="text-sm p-2 border rounded">
                          {userId}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
            
            <div className="flex space-x-2 mt-6">
              <Button onClick={() => setShowBatchDetails(false)}>
                Close
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-20"
              onClick={() => setShowCreateBatch(true)}
            >
              <Send className="h-6 w-6 mx-auto mb-2" />
              Create Batch
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={handleRetryFailed}
              disabled={!batchResults.some(r => r.failed > 0)}
            >
              <RotateCw className="h-6 w-6 mx-auto mb-2" />
              Retry Failed
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={() => {
                // Export batch data
                const dataStr = JSON.stringify(batches, null, 2);
                const blob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'notification-batches.json';
                a.click();
              }}
            >
              <Download Data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BatchProcessor;
