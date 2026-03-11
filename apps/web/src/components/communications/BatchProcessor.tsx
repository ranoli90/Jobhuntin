import React, { useState } from "react";
import { apiPost } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import {
  Send,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Download,
  Loader2,
} from "lucide-react";

/** API response from POST /communications/notifications/batch */
interface BatchSendResponse {
  batch_id: string;
  total: number;
  successful: number;
  failed: number;
  results: Array<
    | { success: true; notification_id: string }
    | { success: false; error: string }
  >;
  message: string;
}

/**
 * User IDs: No API exists for listing tenant members or team users.
 * Backend note: POST /communications/notifications/batch currently sends all
 * notifications to the current user. To support targeting multiple users, the
 * backend would need to accept user_id per notification in the request.
 */
const BATCH_ENDPOINT = "communications/notifications/batch";

const BatchProcessor: React.FC = () => {
  const [batchForm, setBatchForm] = useState({
    title: "",
    message: "",
    category: "general",
    priority: "medium",
    channels: ["in_app"] as string[],
    batch_size: 10,
  });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<BatchSendResponse | null>(null);
  const [showSendForm, setShowSendForm] = useState(true);

  const handleSendBatch = async () => {
    setError(null);
    setSending(true);
    try {
      const template = {
        title: batchForm.title,
        message: batchForm.message || batchForm.title,
        category: batchForm.category,
        priority: batchForm.priority,
        channels: batchForm.channels,
        data: {},
      };
      const notifications = Array.from({ length: batchForm.batch_size }, () => ({
        ...template,
      }));

      const data = await apiPost<BatchSendResponse>(BATCH_ENDPOINT, {
        notifications,
      });

      setLastResult(data);
      setShowSendForm(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to send batch notifications",
      );
    } finally {
      setSending(false);
    }
  };

  const handleReset = () => {
    setLastResult(null);
    setError(null);
    setShowSendForm(true);
    setBatchForm({
      title: "",
      message: "",
      category: "general",
      priority: "medium",
      channels: ["in_app"],
      batch_size: 10,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Batch Processor</h1>
          <p className="text-muted-foreground">
            Send notifications in batches via{" "}
            <code className="text-sm">POST /communications/notifications/batch</code>
          </p>
        </div>
        {lastResult && (
          <Button variant="outline" onClick={handleReset}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Send Another
          </Button>
        )}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Stats from last batch */}
      {lastResult && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{lastResult.total}</div>
              <div className="text-sm text-muted-foreground">Notifications</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Successful</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {lastResult.successful}
              </div>
              <div className="text-sm text-muted-foreground">
                {lastResult.total > 0
                  ? ((lastResult.successful / lastResult.total) * 100).toFixed(1)
                  : "0"}
                % success rate
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {lastResult.failed}
              </div>
              <div className="text-sm text-muted-foreground">Errors</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Batch ID</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm font-mono truncate" title={lastResult.batch_id}>
                {lastResult.batch_id}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Send batch form */}
      {showSendForm && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Send Batch Notifications</CardTitle>
            <p className="text-sm text-muted-foreground">
              Sends notifications to the current user. Backend does not yet
              support targeting multiple users per batch.
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="batch-title">Title</Label>
                <Input
                  id="batch-title"
                  placeholder="Notification title"
                  value={batchForm.title}
                  onChange={(e) =>
                    setBatchForm({ ...batchForm, title: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="batch-message">Message</Label>
                <Textarea
                  id="batch-message"
                  placeholder="Notification message (optional)"
                  rows={2}
                  value={batchForm.message}
                  onChange={(e) =>
                    setBatchForm({ ...batchForm, message: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="batch-size">Batch Size</Label>
                <Select
                  value={batchForm.batch_size.toString()}
                  onValueChange={(value) =>
                    setBatchForm({
                      ...batchForm,
                      batch_size: Number.parseInt(value, 10),
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5 notifications</SelectItem>
                    <SelectItem value="10">10 notifications</SelectItem>
                    <SelectItem value="50">50 notifications</SelectItem>
                    <SelectItem value="100">100 notifications</SelectItem>
                    <SelectItem value="200">200 notifications</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="batch-priority">Priority</Label>
                  <Select
                    value={batchForm.priority}
                    onValueChange={(value) =>
                      setBatchForm({ ...batchForm, priority: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="batch-category">Category</Label>
                  <Select
                    value={batchForm.category}
                    onValueChange={(value) =>
                      setBatchForm({ ...batchForm, category: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="application_status">
                        Application Status
                      </SelectItem>
                      <SelectItem value="job_matches">Job Matches</SelectItem>
                      <SelectItem value="security">Security</SelectItem>
                      <SelectItem value="marketing">Marketing</SelectItem>
                      <SelectItem value="usage_limits">Usage Limits</SelectItem>
                      <SelectItem value="reminders">Reminders</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleSendBatch}
                  disabled={!batchForm.title || sending}
                >
                  {sending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4 mr-2" />
                  )}
                  {sending ? "Sending…" : "Send Batch"}
                </Button>
                <Button variant="outline" onClick={handleReset}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last batch results detail */}
      {lastResult && lastResult.results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Last Batch Results</CardTitle>
            <p className="text-sm text-muted-foreground">
              {lastResult.message}
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {lastResult.results.slice(0, 20).map((r, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {r.success ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
                      <span className="font-mono text-muted-foreground">
                        {r.notification_id}
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-4 w-4 text-red-600 shrink-0" />
                      <span className="text-red-600">{r.error}</span>
                    </>
                  )}
                </div>
              ))}
              {lastResult.results.length > 20 && (
                <p className="text-sm text-muted-foreground pt-2">
                  … and {lastResult.results.length - 20} more
                </p>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => {
                const blob = new Blob(
                  [JSON.stringify(lastResult, null, 2)],
                  { type: "application/json" },
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `batch-${lastResult.batch_id}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Results
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BatchProcessor;
