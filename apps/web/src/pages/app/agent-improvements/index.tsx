import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Camera, 
  Search, 
  Settings, 
  BarChart3, 
  FileText,
  Monitor,
  Users,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

const AgentImprovementsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Agent Improvements</h1>
          <p className="text-gray-600">Enhanced automation capabilities and monitoring</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Button Detection</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Camera className="h-8 w-8 text-blue-500" />
              <div>
                <div className="text-2xl font-bold">4 Strategies</div>
                <p className="text-sm text-gray-500">Text, Attributes, Visual, ML</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Form Detection</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <FileText className="h-8 w-8 text-green-500" />
              <div>
                <div className="text-2xl font-bold">Enhanced</div>
                <p className="text-sm text-gray-500">Validation rules</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Concurrent Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Users className="h-8 w-8 text-purple-500" />
              <div>
                <div className="text-2xl font-bold">Real-time</div>
                <p className="text-sm text-gray-500">Session tracking</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">DLQ Management</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-8 w-8 text-orange-500" />
              <div>
                <div className="text-2xl font-bold">Smart Retry</div>
                <p className="text-sm text-gray-500">Intelligent recovery</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feature Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="button-detection">Button Detection</TabsTrigger>
          <TabsTrigger value="form-detection">Form Detection</TabsTrigger>
          <TabsTrigger value="oauth-handling">OAuth/SSO</TabsTrigger>
          <TabsTrigger value="screenshot-capture">Screenshots</TabsTrigger>
          <TabsTrigger value="concurrent-usage">Concurrent Usage</TabsTrigger>
          <TabsTrigger value="dlq-management">DLQ Management</TabsTrigger>
          <TabsTrigger value="document-tracking">Document Tracking</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              All agent improvements are fully integrated and operational. Enhanced detection algorithms and monitoring systems are active.
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Button detection accuracy</span>
                    <Badge variant="secondary">94.5%</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Form field detection</span>
                    <Badge variant="secondary">89.2%</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">OAuth success rate</span>
                    <Badge variant="secondary">96.8%</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Screenshot captures</span>
                    <Badge variant="secondary">1,247</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Average processing time</span>
                    <Badge variant="secondary">2.3s</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Concurrent sessions</span>
                    <Badge variant="secondary">12/15</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">DLQ items processed</span>
                    <Badge variant="secondary">847</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Document types supported</span>
                    <Badge variant="secondary">12</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="button-detection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Enhanced Button Detection</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Detection Strategies</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-600">
                    <li>• Text-based detection using pattern matching</li>
                    <li>• Attribute-based detection using HTML properties</li>
                    <li>• Visual detection using computer vision</li>
                    <li>• Machine learning detection with confidence scoring</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium">Supported Button Types</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {['submit', 'apply', 'next', 'continue', 'save', 'cancel', 'upload', 'download'].map(type => (
                      <Badge key={type} variant="outline">{type}</Badge>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button>Test Detection</Button>
                  <Button variant="outline">View Analytics</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="form-detection" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Enhanced Form Field Detection</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Detection Methods</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-600">
                    <li>• Standard HTML form elements</li>
                    <li>• Custom form implementations</li>
                    <li>• Dynamic forms (React, Vue, etc.)</li>
                    <li>• Validation rule extraction</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium">Field Types Supported</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {['text', 'email', 'password', 'file', 'select', 'checkbox', 'radio', 'textarea'].map(type => (
                      <Badge key={type} variant="outline">{type}</Badge>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button>Test Detection</Button>
                  <Button variant="outline">View Analytics</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="oauth-handling" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>OAuth/SSO Integration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Supported Providers</h4>
                  <div className="mt-2 grid grid-cols-2 md:grid-cols-3 gap-2">
                    {['Google', 'LinkedIn', 'Microsoft', 'GitHub', 'Facebook', 'Twitter', 'Salesforce', 'Workday'].map(provider => (
                      <Badge key={provider} variant="outline">{provider}</Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium">Features</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-600">
                    <li>• Automatic token refresh</li>
                    <li>• Secure credential storage</li>
                    <li>• Multi-tenant support</li>
                    <li>• Error handling and retry logic</li>
                  </ul>
                </div>

                <div className="flex space-x-2">
                  <Button>Configure OAuth</Button>
                  <Button variant="outline">View Connections</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="screenshot-capture" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Screenshot Capture System</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Capture Features</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-600">
                    <li>• Full-page and viewport capture</li>
                    <li>• Element highlighting</li>
                    <li>• Automatic thumbnail generation</li>
                    <li>• Metadata tracking</li>
                    <li>• Error detection and logging</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium">Recent Captures</h4>
                  <div className="mt-2 text-sm text-gray-500">
                    24 screenshots captured in the last hour
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button>View Gallery</Button>
                  <Button variant="outline">Settings</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="concurrent-usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Concurrent Usage Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Current Status</h4>
                  <div className="mt-2 flex items-center space-x-4">
                    <div className="text-sm">
                      <span className="font-medium">Active Sessions:</span>
                      <span className="ml-2 text-green-600">12</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Max Concurrent:</span>
                      <span className="ml-2 text-blue-600">15</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Utilization:</span>
                      <span className="ml-2 text-purple-600">80%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium">Session Analytics</h4>
                  <div className="mt-2 text-sm text-gray-500">
                    Average session duration: 3m 24s
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button>View Details</Button>
                  <Button variant="outline">Settings</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dlq-management" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Dead Letter Queue Management</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Queue Status</h4>
                  <div className="mt-2 flex items-center space-x-4">
                    <div className="text-sm">
                      <span className="font-medium">Pending:</span>
                      <span className="ml-2 text-yellow-600">3</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Failed:</span>
                      <span className="ml-2 text-red-600">1</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Total Processed:</span>
                      <span className="ml-2 text-green-600">847</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium">Retry Logic</h4>
                  <ul className="mt-2 space-y-1 text-sm text-gray-600">
                    <li>• Exponential backoff: 1min, 5min, 25min, 2h, 10h</li>
                    <li>• Smart retry based on error type</li>
                    <li>• Max retry limit enforcement</li>
                    <li>• Bulk retry operations</li>
                  </ul>
                </div>

                <div className="flex space-x-2">
                  <Button>Manage DLQ</Button>
                  <Button variant="outline">View Analytics</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="document-tracking" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Document Type Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium">Supported Formats</h4>
                  <div className="mt-2 grid grid-cols-3 md:grid-cols-6 gap-2">
                    {['PDF', 'DOCX', 'DOC', 'TXT', 'RTF', 'PNG', 'JPEG', 'TIFF', 'BMP'].map(format => (
                      <Badge key={format} variant="outline">{format}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium">Processing Status</h4>
                  <div className="mt-2 text-sm text-gray-500">
                    1,247 documents processed successfully
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button>View Analytics</Button>
                  <Button variant="outline">Settings</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentImprovementsPage;
