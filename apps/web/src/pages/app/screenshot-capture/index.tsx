import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import {
  Camera,
  Download,
  Eye,
  EyeOff,
  ZoomIn,
  ZoomOut,
  RotateCw,
} from "lucide-react";

const ScreenshotCapturePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Screenshot Capture</h1>
          <p className="text-gray-600">
            Professional screenshot capture tool for debugging and analysis
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline">
            <Camera className="h-4 w-4 mr-2" />
            Capture Screenshot
          </Button>
        </div>
      </div>

      <Alert>
        <AlertDescription>
          Screenshot capture tool allows you to capture screenshots during the
          application process for debugging and analysis purposes.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Screenshot Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium">Capture Options</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Full-page and viewport capture</li>
                  <li>• Element highlighting</li>
                  <li>• Automatic thumbnail generation</li>
                  <li>• Metadata tracking</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium">Recent Captures</h4>
                <div className="text-sm text-gray-500">
                  24 screenshots captured in the last hour
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ScreenshotCapturePage;
