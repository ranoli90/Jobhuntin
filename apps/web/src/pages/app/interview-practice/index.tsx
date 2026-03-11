import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Brain, Target, TrendingUp, CheckCircle, Clock } from "lucide-react";

const InterviewPracticePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Interview Practice</h1>
          <p className="text-gray-600">
            AI-powered interview preparation with mastery tracking
          </p>
        </div>
        <div className="flex space-x-2">
          <Button>
            <Brain className="h-4 w-4 mr-2" />
            Start Practice
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Practice interview questions with AI-powered feedback and track your
          improvement over time.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Question Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 border rounded-lg">
                <div className="font-medium">Behavioral Questions</div>
                <div className="text-sm text-gray-500 mt-1">
                  15 questions • 85% mastery
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: "85%" }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="p-4 border rounded-lg">
                <div className="font-medium">Technical Questions</div>
                <div className="text-sm text-gray-500 mt-1">
                  23 questions • 72% mastery
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: "72%" }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Practice Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Target className="h-5 w-5 text-blue-500" />
                  <div>
                    <div className="font-medium">React Hooks Interview</div>
                    <div className="text-sm text-gray-500">
                      Technical question • Score: 8/10
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">2 hours ago</div>
                  <Badge variant="secondary">Good</Badge>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Brain className="h-5 w-5 text-green-500" />
                  <div>
                    <div className="font-medium">Tell me about yourself</div>
                    <div className="text-sm text-gray-500">
                      Behavioral question • Score: 9/10
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">1 day ago</div>
                  <Badge variant="secondary">Excellent</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Practice Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">38</div>
              <p className="text-sm text-gray-500">Questions Practiced</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">79%</div>
              <p className="text-sm text-gray-500">Average Score</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">12</div>
              <p className="text-sm text-gray-500">Mastered Questions</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">85%</div>
              <p className="text-sm text-gray-500">Improvement Rate</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default InterviewPracticePage;
