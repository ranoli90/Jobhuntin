import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  Mail, 
  Bell, 
  Shield, 
  Settings, 
  RefreshCw,
  Activity,
  BarChart3,
  Eye,
  Download,
  Filter,
  AlertTriangle,
  Brain,
  Heart,
  Users
} from 'lucide-react';

// Import components
import EmailManager from '@/components/communications/EmailManager';
import NotificationManager from '@/components/communications/NotificationManager';
import AlertProcessor from '@/components/communications/AlertProcessor';
import SemanticMatcher from '@/components/communications/SemanticMatcher';
import UserInterests from '@/components/communications/UserInterests';
import BatchProcessor from '@/components/communications/BatchProcessor';

const CommunicationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Communications Center</h1>
          <p className="text-gray-600">Manage all communication channels and preferences</p>
        </div>
        <div className="flex space-x-2">
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

      <Tabs value={activeTab} className="space-y-4">
        <TabsList className="grid w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="email">Email</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="semantic">Semantic</TabsTrigger>
          <TabsTrigger value="interests">Interests</TabsTrigger>
          <TabsTrigger value="batch">Batch Processing</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Communications Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-8 w-8 text-blue-600" />
                      <div>
                        <h3 className="text-lg font-medium">Email Communications</h3>
                        <p className="text-sm text-gray-500">
                          Send and receive emails with templates
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Bell className="h-8 w-8 text-green-600" />
                      <div>
                        <h3 className="text-lg font-medium">Push Notifications</h3>
                        <p className="text-sm text-gray-500">
                          Real-time notifications with semantic matching
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Shield className="h-8 w-8 text-red-600" />
                      <div>
                        <h3 className="alert-lg font-medium">Alert Processing</h3>
                        <p className="text-sm text-gray-500">
                          Rule-based alert system
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Brain className="h-8 w-8 text-purple-600" />
                      <div>
                        <h3 className="text-lg font-medium">Semantic Matching</h3>
                        <p className="text-sm text-gray-500">
                          AI-powered relevance scoring
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Heart className="h-8 w-8 text-pink-600" />
                      <div>
                        <h3 className="text-lg font-medium">User Interests</h3>
                        <p className="text-sm text-gray-500">
                          Personalized interest profiling
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Users className="h-8 w-8 text-indigo-600" />
                      <div>
                        <h3 className="text-lg font-medium">Batch Processing</h3>
                        <p className="text-sm text-gray-500">
                          Intelligent batch processing
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      <Mail />
                    </div>
                    <div>
                      <div className="text-lg font-medium text-gray-600">Emails Sent Today</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <Mail className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <div className="text-lg font-medium text-green-600">Online</div>
                      <div className="text-sm text-gray-500">Email System</div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <Bell className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <div className="text-lg font-medium text-green-600">Online</div>
                      <div className="text-sm text-gray-500">Notification System</div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="text-center">
                      <Shield className="h-6 w-6 text-red-600" />
                    </div>
                    <div>
                      <div className="text-lg font-medium text-red-600">Online</div>
                      <div className="text-sm text-gray-500">Alert System</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="email" className="space-y-4">
          <EmailManager />
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <NotificationManager />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <AlertProcessor />
        </TabsContent>

        <TabsContent value="semantic" className="space-y-4">
          <SemanticMatcher />
        </TabsContent>

        <TabsContent value="interests" className="space-y-4">
          <UserInterests />
        </TabsContent>

        <TabsContent value="batch" className="space-y-4">
          <BatchProcessor />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CommunicationsPage;
