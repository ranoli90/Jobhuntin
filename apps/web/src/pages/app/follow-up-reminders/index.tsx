import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, Calendar, Bell, CheckCircle } from 'lucide-react';

const FollowUpRemindersPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Follow-up Reminders</h1>
          <p className="text-gray-600">Automated follow-up reminders for job applications</p>
        </div>
        <div className="flex space-x-2">
          <Button>
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Reminder
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Set up automated follow-up reminders to stay on top of your job applications and never miss an important deadline.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Reminders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Clock className="h-5 w-5 text-blue-500" />
                  <div>
                    <div className="font-medium">Follow-up with Google</div>
                    <div className="text-sm text-gray-500">Application submitted 3 days ago</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Tomorrow</div>
                  <Badge variant="secondary">Active</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Clock className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Interview Preparation</div>
                    <div className="text-sm text-gray-500">Interview scheduled for next week</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">In 3 days</div>
                  <Badge variant="secondary">Active</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reminder Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="font-medium">Application Follow-up</div>
                <div className="text-sm text-gray-500 mt-1">
                  "I wanted to follow up on my application for the [Position] role. I'm very interested in this opportunity..."
                </div>
                <Badge variant="outline" className="mt-2">Professional</Badge>
              </div>
              
              <div className="p-4 border rounded-lg">
                <div className="font-medium">Interview Thank You</div>
                <div className="text-sm text-gray-500 mt-1">
                  "Thank you for taking the time to interview with me for the [Position] position. I enjoyed learning more about..."
                </div>
                <Badge variant="outline" className="mt-2">Gratitude</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reminder Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">8</div>
              <p className="text-sm text-gray-500">Active Reminders</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">24</div>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">3</div>
              <p className="text-sm text-gray-500">Scheduled</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">2</div>
              <p className="text-sm text-gray-500">Overdue</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FollowUpRemindersPage;
