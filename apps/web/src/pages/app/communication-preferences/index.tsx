import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiPut } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Switch } from "@/components/ui/Switch";
import { Mail, Bell, Settings } from "lucide-react";
import { pushToast } from "@/lib/toast";

interface EmailPreferences {
  status_changes: boolean;
  security: boolean;
  usage_alerts: boolean;
  marketing: boolean;
  weekly_digest: boolean;
}

interface NotificationPreferences {
  dnd_active: boolean;
  dnd_start_time: string | null;
  dnd_end_time: string | null;
  timezone: string;
  notification_sound: boolean;
  notification_vibration: boolean;
  notification_badge: boolean;
  email_preferences: EmailPreferences;
}

const CommunicationPreferencesPage: React.FC = () => {
  const navigate = useNavigate();
  const [emailPrefs, setEmailPrefs] = useState<EmailPreferences | null>(null);
  const [notifPrefs, setNotifPrefs] =
    useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [emailRes, notifRes] = await Promise.all([
        apiGet<EmailPreferences>("communications/preferences/email"),
        apiGet<NotificationPreferences>(
          "communications/preferences/notifications",
        ),
      ]);
      setEmailPrefs(emailRes);
      setNotifPrefs(notifRes);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load communication preferences",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEmailToggle = async (
    key: keyof EmailPreferences,
    value: boolean,
  ) => {
    if (!emailPrefs) return;
    setUpdating(`email-${key}`);
    try {
      const next = { ...emailPrefs, [key]: value };
      await apiPut("communications/preferences/email", next);
      setEmailPrefs(next);
      pushToast({ title: "Email preferences updated", tone: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof Error ? err.message : "Failed to update",
        tone: "error",
      });
    } finally {
      setUpdating(null);
    }
  };

  const handleNotificationToggle = async (
    key: keyof NotificationPreferences,
    value: boolean,
  ) => {
    if (!notifPrefs) return;
    setUpdating(`notif-${key}`);
    try {
      const next = { ...notifPrefs, [key]: value };
      await apiPut("communications/preferences/notifications", next);
      setNotifPrefs(next);
      pushToast({ title: "Notification preferences updated", tone: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof Error ? err.message : "Failed to update",
        tone: "error",
      });
    } finally {
      setUpdating(null);
    }
  };

  const handleNestedEmailToggle = async (
    key: keyof EmailPreferences,
    value: boolean,
  ) => {
    if (!notifPrefs) return;
    setUpdating(`notif-email-${key}`);
    try {
      const next = {
        ...notifPrefs,
        email_preferences: { ...notifPrefs.email_preferences, [key]: value },
      };
      await apiPut("communications/preferences/notifications", next);
      setNotifPrefs(next);
      pushToast({ title: "Preferences updated", tone: "success" });
    } catch (err) {
      pushToast({
        title: err instanceof Error ? err.message : "Failed to update",
        tone: "error",
      });
    } finally {
      setUpdating(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Communication Preferences</h1>
            <p className="text-gray-600">
              Manage your email and notification preferences
            </p>
          </div>
        </div>
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Communication Preferences</h1>
          <p className="text-gray-600">
            Manage your email and notification preferences
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={() => navigate("/app/settings")}
            aria-label="Go to Settings"
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Alert>
        <AlertDescription>
          Configure how you receive communications from JobHuntin, including
          email notifications and push notifications.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Mail className="h-5 w-5" />
              Email Preferences
            </CardTitle>
          </CardHeader>
          <CardContent>
            {emailPrefs ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Application Status Updates</span>
                  <Switch
                    checked={emailPrefs.status_changes}
                    onCheckedChange={(v) =>
                      handleEmailToggle("status_changes", v)
                    }
                    disabled={updating === "email-status_changes"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Magic Link Notifications</span>
                  <Switch
                    checked={emailPrefs.security}
                    onCheckedChange={(v) =>
                      handleEmailToggle("security", v)
                    }
                    disabled={updating === "email-security"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Rate Limit Warnings</span>
                  <Switch
                    checked={emailPrefs.usage_alerts}
                    onCheckedChange={(v) =>
                      handleEmailToggle("usage_alerts", v)
                    }
                    disabled={updating === "email-usage_alerts"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Weekly Summary</span>
                  <Switch
                    checked={emailPrefs.weekly_digest}
                    onCheckedChange={(v) =>
                      handleEmailToggle("weekly_digest", v)
                    }
                    disabled={updating === "email-weekly_digest"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Marketing</span>
                  <Switch
                    checked={emailPrefs.marketing}
                    onCheckedChange={(v) =>
                      handleEmailToggle("marketing", v)
                    }
                    disabled={updating === "email-marketing"}
                  />
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Could not load email preferences.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bell className="h-5 w-5" />
              Notification Preferences
            </CardTitle>
          </CardHeader>
          <CardContent>
            {notifPrefs ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Push Notifications</span>
                  <Switch
                    checked={notifPrefs.notification_sound}
                    onCheckedChange={(v) =>
                      handleNotificationToggle("notification_sound", v)
                    }
                    disabled={updating === "notif-notification_sound"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Notification Badge</span>
                  <Switch
                    checked={notifPrefs.notification_badge}
                    onCheckedChange={(v) =>
                      handleNotificationToggle("notification_badge", v)
                    }
                    disabled={updating === "notif-notification_badge"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Vibration</span>
                  <Switch
                    checked={notifPrefs.notification_vibration}
                    onCheckedChange={(v) =>
                      handleNotificationToggle("notification_vibration", v)
                    }
                    disabled={updating === "notif-notification_vibration"}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <span>Do Not Disturb</span>
                  <Switch
                    checked={notifPrefs.dnd_active}
                    onCheckedChange={(v) =>
                      handleNotificationToggle("dnd_active", v)
                    }
                    disabled={updating === "notif-dnd_active"}
                  />
                </div>
                <div className="border-t pt-4 mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Email in notifications
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Application Updates</span>
                      <Switch
                        checked={
                          notifPrefs.email_preferences.status_changes
                        }
                        onCheckedChange={(v) =>
                          handleNestedEmailToggle("status_changes", v)
                        }
                        disabled={
                          updating === "notif-email-status_changes"
                        }
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Weekly Digest</span>
                      <Switch
                        checked={
                          notifPrefs.email_preferences.weekly_digest
                        }
                        onCheckedChange={(v) =>
                          handleNestedEmailToggle("weekly_digest", v)
                        }
                        disabled={
                          updating === "notif-email-weekly_digest"
                        }
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Could not load notification preferences.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CommunicationPreferencesPage;
