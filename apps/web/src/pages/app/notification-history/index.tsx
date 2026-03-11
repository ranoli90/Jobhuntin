import React from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Bell, Clock, CheckCircle, Eye } from "lucide-react";

const NotificationHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Notification History</h1>
          <p className="text-gray-600">
            View your notification history and preferences
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => navigate("/app/communication-preferences")}
            aria-label="View all communication preferences"
          >
            <Eye className="h-4 w-4 mr-2" />
            View All
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          View your complete notification history, including email notifications
          and push notifications sent to your devices.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Recent Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <Bell className="h-5 w-5 text-blue-500" />
                <div>
                  <div className="font-medium">
                    Application Submitted Successfully
                  </div>
                  <div className="text-sm text-gray-500">
                    Your application to Google was submitted successfully
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">2 hours ago</div>
                <Badge variant="secondary">Email</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <Bell className="h-5 w-5 text-green-500" />
                <div>
                  <div className="font-medium">New Job Match</div>
                  <div className="text-sm text-gray-500">
                    We found a new job matching your profile
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">5 hours ago</div>
                <Badge variant="secondary">Push</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center space-x-3">
                <Bell className="h-5 w-5 text-orange-500" />
                <div>
                  <div className="font-medium">Rate Limit Warning</div>
                  <div className="text-sm text-gray-500">
                    You're approaching your monthly limit
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">1 day ago</div>
                <Badge variant="secondary">Email</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notification Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">156</div>
              <p className="text-sm text-gray-500">Total Notifications</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">142</div>
              <p className="text-sm text-gray-500">Delivered</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">89</div>
              <p className="text-sm text-gray-500">Opened</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">14</div>
              <p className="text-sm text-gray-500">Failed</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NotificationHistoryPage;
