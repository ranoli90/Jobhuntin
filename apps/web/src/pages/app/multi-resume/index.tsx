import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { FileText, Upload, TrendingUp, BarChart3, CheckCircle } from 'lucide-react';

const MultiResumePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Multi-Resume Support</h1>
          <p className="text-gray-600">Manage multiple resume versions with analytics and recommendations</p>
        </div>
        <div className="flex space-x-2">
          <Button>
            <Upload className="h-4 w-4 mr-2" />
            Upload Resume
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Create and manage multiple resume versions tailored for different job types and industries with AI-powered recommendations.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Resume Versions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-500" />
                  <div>
                    <div className="font-medium">Software Engineer Resume</div>
                    <div className="text-sm text-gray-500">Primary resume • 85% match rate</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Primary</div>
                  <Badge variant="secondary">Active</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Frontend Developer Resume</div>
                    <div className="text-sm text-gray-500">Specialized • 78% match rate</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Secondary</div>
                  <Badge variant="outline">Active</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resume Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="font-medium">Performance Comparison</div>
                <div className="text-sm text-gray-500 mt-1">
                  Software Engineer resume performs 15% better than Frontend Developer resume for technical roles
                </div>
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">View detailed analytics</span>
                  </div>
                </div>
              </div>
              
              <div className="p-4 border rounded-lg">
                <div className="font-medium">ATS Optimization</div>
                <div className="text-sm text-gray-500 mt-1">
                  Your resumes are optimized for ATS systems with 92% average compliance score
                </div>
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Above average performance</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Resume Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">3</div>
              <p className="text-sm text-gray-500">Resume Versions</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">82%</div>
              <p className="text-sm text-gray-500">Average Match Rate</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">24</div>
              <div className="text-sm text-gray-500">Applications Sent</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">6</div>
              <div className="text-sm text-gray-500">Interviews Scheduled</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MultiResumePage;
