import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Progress } from '@/components/ui/Progress';
import { 
  FileText, 
  Upload, 
  CheckCircle, 
  AlertTriangle,
  FileImage,
  FileSpreadsheet,
  File,
  BarChart3,
  TrendingUp,
  RefreshCw,
  Download,
  Eye,
  EyeOff
} from 'lucide-react';

interface DocumentType {
  tracking_id: string;
  file_name: string;
  content_type: string;
  file_size: number;
  document_type: string;
  confidence_score: number;
  content_preview?: string;
  metadata: Record<string, any>;
  created_at: string;
}

interface DocumentStats {
  total_documents: number;
  by_type: Record<string, number>;
  average_confidence: number;
  total_size: number;
  by_category: Record<string, number>;
}

const DocumentProcessor: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [stats, setStats] = useState<DocumentStats>({
    total_documents: 0,
    by_type: {},
    average_confidence: 0,
    total_size: 0,
    by_category: {},
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchDocuments();
    fetchStats();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchDocuments();
        fetchStats();
      }, 10000);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedType]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/document-tracking/list', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/document-tracking/stats', {
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

  const getDocumentIcon = (documentType: string) => {
    const icons = {
      pdf: '📄',
      docx: '📝',
      doc: '📄',
      txt: '📄',
      rtf: '📄',
      jpeg: '🖼️',
      png: '🖼️',
      tiff: '🖼️',
      bmp: '🖼️',
    };
    return icons[documentType as keyof typeof icons] || '📄';
  };

  const getDocumentColor = (documentType: string) => {
    const colors = {
      pdf: 'bg-red-100 text-red-800',
      docx: 'bg-blue-100 text-blue-800',
      doc: 'bg-blue-100 text-blue-800',
      txt: 'bg-gray-100 text-gray-800',
      rtf: 'bg-gray-100 text-gray-800',
      jpeg: 'bg-green-100 text-green-800',
      png: 'bg-green-100 text-green-800',
      tiff: 'bg-green-100 text-green-800',
      bmp: 'bg-green-100 text-green-800',
    };
    return colors[documentType as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const handleTrackDocument = async (file: File) => {
    try {
      setLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/document-tracking/track', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to track document');
      
      await fetchDocuments();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to track document');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (trackingId: string) => {
    if (!confirm('Are you sure you want to delete this document tracking record?')) return;

    try {
      const response = await fetch(`/api/document-tracking/${trackingId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete document');
      
      await fetchDocuments();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const filteredDocuments = selectedType === 'all' 
    ? documents 
    : documents.filter(doc => doc.document_type === selectedType);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Document Processor</h1>
          <p className="text-gray-600">Track and analyze document types with AI-powered classification</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Upload className="h-4 w-4 mr-2" />
            Upload Document
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh' : 'Manual refresh'}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchStats}>
            <BarChart3 className="h-4 w-4 mr-2" />
            Refresh Stats
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">
              Drag and drop a document here, or click to browse
            </p>
            <Button
              onClick={() => document.getElementById('file-upload')?.click()}
              disabled={loading}
            >
              <Upload className="h-4 w-4 mr-2" />
              Choose File
            </Button>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".pdf,.docx,.doc,.txt,.rtf,.jpeg,.png,.tiff,.bmp"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleTrackDocument(file);
                }
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_documents}</div>
            <div className="text-sm text-gray-500">
              {formatFileSize(stats.total_size)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Average Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <span className={getConfidenceColor(stats.average_confidence)}>
                {Math.round(stats.average_confidence * 100)}%
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Classification accuracy
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">PDF Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.by_type.pdf || 0}
            </div>
            <div className="text-sm text-gray-500">
              Most common type
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Image Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(stats.by_type.jpeg || 0) + (stats.by_type.png || 0) + (stats.by_type.tiff || 0) + (stats.by_type.bmp || 0)}
            </div>
            <div className="text-sm text-gray-500">
              Total images
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Document Type Filter */}
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
                <span className="mr-1">{getDocumentIcon(type)}</span>
                {type.toUpperCase()}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Document List */}
      <Card>
        <CardHeader>
          <CardTitle>
            Tracked Documents 
            {selectedType !== 'all' && `(${selectedType.toUpperCase()})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredDocuments.map((doc) => (
              <Card key={doc.tracking_id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{getDocumentIcon(doc.document_type)}</div>
                    <div className="flex-1">
                      <h4 className="font-medium">{doc.file_name}</h4>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(doc.file_size)} • {doc.content_type}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge className={getDocumentColor(doc.document_type)}>
                          {doc.document_type.toUpperCase()}
                        </Badge>
                        <Badge 
                          variant="outline" 
                          className={getConfidenceColor(doc.confidence_score)}
                        >
                          {Math.round(doc.confidence_score * 100)}% confidence
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // In a real implementation, this would download the original file
                        console.log('Download document:', doc.tracking_id);
                      }}
                    >
                      <Download className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteDocument(doc.tracking_id)}
                    >
                      <FileText className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {/* Content Preview */}
                {doc.content_preview && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">
                      <strong>Content Preview:</strong>
                    </p>
                    <p className="text-sm text-gray-700 mt-1 line-clamp-2">
                      {doc.content_preview}
                    </p>
                  </div>
                )}

                {/* Metadata */}
                {showDetails && Object.keys(doc.metadata).length > 0 && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Metadata:</strong>
                    </p>
                    <div className="space-y-1">
                      {Object.entries(doc.metadata).map(([key, value]) => (
                        <div key={key} className="text-sm">
                          <span className="font-medium">{key}:</span>
                          <span className="text-gray-700 ml-2">{JSON.stringify(value, null, 2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
          
          {filteredDocuments.length === 0 && (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {selectedType === 'all' 
                  ? 'No documents tracked yet' 
                  : `No ${selectedType} documents tracked yet`
                }
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Upload a document to start tracking
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentProcessor;
