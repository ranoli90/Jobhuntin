import React, { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Camera, Download, Eye, EyeOff, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

interface ScreenshotCapture {
  capture_id: string;
  application_id: string;
  step_number: number;
  step_description: string;
  timestamp: string;
  screenshot_path: string;
  thumbnail_path?: string;
  viewport_size: { width: number; height: number };
  full_page: boolean;
  elements_highlighted: string[];
  error_detected: boolean;
  error_message?: string;
}

interface ScreenshotCaptureProps {
  applicationId: string;
  onCapture?: (screenshot: ScreenshotCapture) => void;
}

export const ScreenshotCapture: React.FC<ScreenshotCaptureProps> = ({ 
  applicationId, 
  onCapture 
}) => {
  const [screenshots, setScreenshots] = useState<ScreenshotCapture[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [stepDescription, setStepDescription] = useState('');
  const [fullPage, setFullPage] = useState(false);
  const [highlightElements, setHighlightElements] = useState<string[]>([]);
  const [highlightInput, setHighlightInput] = useState('');
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedScreenshot, setSelectedScreenshot] = useState<ScreenshotCapture | null>(null);
  const [zoom, setZoom] = useState(1);

  const handleCapture = async () => {
    if (!stepDescription.trim()) {
      setError('Please provide a step description');
      return;
    }

    try {
      setIsCapturing(true);
      setError(null);

      const response = await fetch('/api/agent-improvements/capture-screenshot', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          application_id: applicationId,
          step_number: currentStep,
          step_description: stepDescription,
          page_context: {
            viewport: { width: 1920, height: 1080 },
          },
          full_page: fullPage,
          highlight_elements: highlightElements,
        }),
      });

      if (!response.ok) throw new Error('Failed to capture screenshot');

      const screenshot: ScreenshotCapture = await response.json();
      setScreenshots([...screenshots, screenshot]);
      setCurrentStep(currentStep + 1);
      setStepDescription('');
      setHighlightElements([]);
      setHighlightInput('');

      if (onCapture) {
        onCapture(screenshot);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to capture screenshot');
    } finally {
      setIsCapturing(false);
    }
  };

  const handleAddHighlight = () => {
    if (highlightInput.trim() && !highlightElements.includes(highlightInput.trim())) {
      setHighlightElements([...highlightElements, highlightInput.trim()]);
      setHighlightInput('');
    }
  };

  const handleRemoveHighlight = (element: string) => {
    setHighlightElements(highlightElements.filter(el => el !== element));
  };

  const handleDownload = async (screenshot: ScreenshotCapture) => {
    try {
      const response = await fetch(`/api/agent-improvements/screenshots/${screenshot.screenshot_path}`);
      if (!response.ok) throw new Error('Failed to download screenshot');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `screenshot-${screenshot.step_number}-${screenshot.application_id}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download screenshot');
    }
  };

  const handleZoomIn = () => {
    setZoom(Math.min(zoom + 0.25, 3));
  };

  const handleZoomOut = () => {
    setZoom(Math.max(zoom - 0.25, 0.5));
  };

  const handleResetZoom = () => {
    setZoom(1);
  };

  return (
    <div className="space-y-6">
      {/* Capture Form */}
      <Card>
        <CardHeader>
          <CardTitle>Capture Screenshot</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="step-number">Step Number</Label>
              <Input
                id="step-number"
                type="number"
                value={currentStep}
                onChange={(e) => setCurrentStep(parseInt(e.target.value) || 1)}
                min="1"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="step-description">Step Description</Label>
              <Textarea
                id="step-description"
                value={stepDescription}
                onChange={(e) => setStepDescription(e.target.value)}
                placeholder="Describe what this step accomplishes..."
                rows={3}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Highlight Elements</Label>
            <div className="flex space-x-2">
              <Input
                value={highlightInput}
                onChange={(e) => setHighlightInput(e.target.value)}
                placeholder="Enter CSS selector or element ID..."
                onKeyPress={(e) => e.key === 'Enter' && handleAddHighlight()}
              />
              <Button onClick={handleAddHighlight} type="button">
                Add
              </Button>
            </div>
            {highlightElements.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {highlightElements.map((element) => (
                  <Badge
                    key={element}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => handleRemoveHighlight(element)}
                  >
                    {element} ×
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="full-page"
              checked={fullPage}
              onCheckedChange={setFullPage}
            />
            <Label htmlFor="full-page">Capture Full Page</Label>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleCapture}
            disabled={isCapturing || !stepDescription.trim()}
            className="w-full"
          >
            <Camera className="h-4 w-4 mr-2" />
            {isCapturing ? 'Capturing...' : 'Capture Screenshot'}
          </Button>
        </CardContent>
      </Card>

      {/* Screenshots Gallery */}
      {screenshots.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Captured Screenshots ({screenshots.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {screenshots.map((screenshot) => (
                <div
                  key={screenshot.capture_id}
                  className="border rounded-lg overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500"
                  onClick={() => setSelectedScreenshot(screenshot)}
                >
                  <div className="relative">
                    <img
                      src={screenshot.thumbnail_path || screenshot.screenshot_path}
                      alt={screenshot.step_description}
                      className="w-full h-32 object-cover"
                    />
                    {screenshot.error_detected && (
                      <div className="absolute top-2 right-2">
                        <Badge variant="destructive">Error</Badge>
                      </div>
                    )}
                    <div className="absolute bottom-2 left-2">
                      <Badge variant="secondary">
                        Step {screenshot.step_number}
                      </Badge>
                    </div>
                  </div>
                  <div className="p-2">
                    <p className="text-sm font-medium truncate">{screenshot.step_description}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(screenshot.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Screenshot Viewer */}
      {selectedScreenshot && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>
                Step {selectedScreenshot.step_number}: {selectedScreenshot.step_description}
              </CardTitle>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleZoomOut}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetZoom}
                >
                  <RotateCw className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleZoomIn}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDownload(selectedScreenshot)}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedScreenshot(null)}
                >
                  <EyeOff className="h-4 w-4 mr-1" />
                  Close
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between text-sm text-gray-500">
                <span>Viewport: {selectedScreenshot.viewport_size.width}×{selectedScreenshot.viewport_size.height}</span>
                <span>Zoom: {Math.round(zoom * 100)}%</span>
                <span>Full Page: {selectedScreenshot.full_page ? 'Yes' : 'No'}</span>
              </div>
              
              {selectedScreenshot.error_detected && (
                <Alert variant="destructive">
                  <AlertDescription>
                    Error detected: {selectedScreenshot.error_message || 'Unknown error'}
                  </AlertDescription>
                </Alert>
              )}

              <div className="overflow-auto border rounded-lg">
                <img
                  src={selectedScreenshot.screenshot_path}
                  alt={selectedScreenshot.step_description}
                  style={{
                    transform: `scale(${zoom})`,
                    transformOrigin: 'top left',
                    transition: 'transform 0.2s',
                  }}
                  className="max-w-none"
                />
              </div>

              {selectedScreenshot.elements_highlighted.length > 0 && (
                <div className="space-y-2">
                  <Label>Highlighted Elements</Label>
                  <div className="flex flex-wrap gap-2">
                    {selectedScreenshot.elements_highlighted.map((element) => (
                      <Badge key={element} variant="outline">
                        {element}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
