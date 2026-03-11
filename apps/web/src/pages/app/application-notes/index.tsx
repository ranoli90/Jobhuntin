import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import {
  FileText,
  Plus,
  Search,
  Tag,
  Calendar,
  CheckCircle,
} from "lucide-react";

const ApplicationNotesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Application Notes</h1>
          <p className="text-gray-600">
            Rich note-taking system with templates and search capabilities
          </p>
        </div>
        <div className="flex space-x-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Note
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Keep detailed notes for each application with templates, search
          functionality, and reminder integration.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-500" />
                  <div>
                    <div className="font-medium">
                      Interview Preparation Notes
                    </div>
                    <div className="text-sm text-gray-500">
                      Google • Technical interview prep
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">2 hours ago</div>
                  <Badge variant="secondary">Interview</Badge>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Company Research</div>
                    <div className="text-sm text-gray-500">
                      Microsoft • Company culture and values
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">1 day ago</div>
                  <Badge variant="secondary">Research</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Note Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="font-medium">Interview Preparation</div>
                <div className="text-sm text-gray-500 mt-1">
                  Template for preparing for interviews with key questions and
                  talking points
                </div>
                <Badge variant="outline" className="mt-2">
                  Popular
                </Badge>
              </div>

              <div className="p-4 border rounded-lg">
                <div className="font-medium">Contact Information</div>
                <div className="text-sm text-gray-500 mt-1">
                  Template for storing recruiter and hiring manager contact
                  details
                </div>
                <Badge variant="outline" className="mt-2">
                  Essential
                </Badge>
              </div>

              <div className="p-4 border rounded-lg">
                <div className="font-medium">Follow-up Actions</div>
                <div className="text-sm text-gray-500 mt-1">
                  Template for tracking follow-up actions and next steps
                </div>
                <Badge variant="outline" className="mt-2">
                  Professional
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Note Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">47</div>
              <p className="text-sm text-gray-500">Total Notes</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">12</div>
              <p className="text-sm text-gray-500">This Week</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">8</div>
              <p className="text-sm text-gray-500">With Reminders</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">23</div>
              <p className="text-sm text-gray-500">Applications</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationNotesPage;
