/**
 * M1: Session Management UI
 *
 * Allows users to view and revoke active sessions for security.
 * Displays device fingerprint, IP address, user agent, and last activity.
 */

import * as React from "react";
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  Clock,
  Trash2,
  LogOut,
  AlertTriangle,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { pushToast } from "../../lib/toast";
import { apiGet, apiDelete } from "../../lib/api";
import { telemetry } from "../../lib/telemetry";

interface Session {
  session_id: string;
  device_fingerprint: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  is_current: boolean;
}

interface SessionsResponse {
  sessions: Session[];
  total: number;
}

function getDeviceIcon(userAgent: string | null): React.ReactNode {
  if (!userAgent) return <Monitor className="w-5 h-5" />;
  const ua = userAgent.toLowerCase();
  if (
    ua.includes("mobile") ||
    ua.includes("android") ||
    ua.includes("iphone")
  ) {
    return <Smartphone className="w-5 h-5" />;
  }
  if (ua.includes("tablet") || ua.includes("ipad")) {
    return <Tablet className="w-5 h-5" />;
  }
  return <Monitor className="w-5 h-5" />;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60)
    return `${diffMins} minute${diffMins === 1 ? "" : "s"} ago`;
  if (diffHours < 24)
    return `${diffHours} hour${diffHours === 1 ? "" : "s"} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
  return date.toLocaleDateString();
}

export default function Sessions() {
  const [sessions, setSessions] = React.useState<Session[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [revokingSessionId, setRevokingSessionId] = React.useState<
    string | null
  >(null);
  const [showRevokeAllModal, setShowRevokeAllModal] = React.useState(false);
  const [revokingAll, setRevokingAll] = React.useState(false);

  const fetchSessions = React.useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiGet<SessionsResponse>("sessions");
      setSessions(data.sessions);
      telemetry.track("sessions_viewed", { total: data.total });
    } catch (error) {
      pushToast({
        title: "Could not load sessions",
        description: (error as Error).message || "Please try again.",
        tone: "error",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleRevokeSession = async (sessionId: string) => {
    try {
      setRevokingSessionId(sessionId);
      await apiDelete(`sessions/${sessionId}`);

      telemetry.track("session_revoked", { session_id: sessionId });
      pushToast({
        title: "Session revoked",
        description: "This session has been signed out.",
        tone: "success",
      });

      // Refresh sessions list
      await fetchSessions();
    } catch (error) {
      pushToast({
        title: "Could not sign out session",
        description: (error as Error).message || "Please try again.",
        tone: "error",
      });
    } finally {
      setRevokingSessionId(null);
    }
  };

  const handleRevokeAllOtherSessions = async () => {
    try {
      setRevokingAll(true);
      const data = await apiDelete<{ count: number }>("sessions/all");
      telemetry.track("sessions_revoked_all", { count: data.count });
      pushToast({
        title: "All other sessions revoked",
        description: `${data.count} session${data.count === 1 ? "" : "s"} have been signed out.`,
        tone: "success",
      });

      // Refresh sessions list
      await fetchSessions();
      setShowRevokeAllModal(false);
    } catch (error) {
      pushToast({
        title: "Could not sign out other sessions",
        description: (error as Error).message || "Please try again.",
        tone: "error",
      });
    } finally {
      setRevokingAll(false);
    }
  };

  const otherSessions = sessions.filter((s) => !s.is_current);
  const currentSession = sessions.find((s) => s.is_current);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div
      className="max-w-4xl mx-auto p-6 space-y-6"
      role="main"
      aria-label="Active Sessions"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Active Sessions
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Manage your active sessions and sign out from devices you no longer
            use.
          </p>
        </div>
        {otherSessions.length > 0 && (
          <Button
            variant="outline"
            onClick={() => setShowRevokeAllModal(true)}
            className="flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            Sign out all other devices
          </Button>
        )}
      </div>

      {sessions.length === 0 ? (
        <Card className="p-8 text-center">
          <Monitor className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
            No active sessions
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            You don't have any active sessions at the moment.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {/* Current Session */}
          {currentSession && (
            <Card className="p-6 border-2 border-brand-primary/20 bg-brand-primary/5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className="p-2 rounded-lg bg-brand-primary/10 text-brand-primary">
                    {getDeviceIcon(currentSession.user_agent)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                        Current Session
                      </h3>
                      <span className="px-2 py-0.5 text-xs font-medium bg-brand-primary/20 text-brand-primary rounded-full">
                        Active
                      </span>
                    </div>
                    <div className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                      {currentSession.user_agent && (
                        <div className="flex items-center gap-2">
                          <Monitor className="w-4 h-4" />
                          <span className="truncate">
                            {currentSession.user_agent}
                          </span>
                        </div>
                      )}
                      {currentSession.ip_address && (
                        <div className="flex items-center gap-2">
                          <Globe className="w-4 h-4" />
                          <span>{currentSession.ip_address}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>
                          Last active:{" "}
                          {formatDate(currentSession.last_activity_at)}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-500">
                        Session ID: {currentSession.session_id.slice(0, 8)}...
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Other Sessions */}
          {otherSessions.length > 0 && (
            <>
              <div className="flex items-center gap-2 mt-6 mb-4">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Other Active Sessions ({otherSessions.length})
                </h2>
              </div>
              {otherSessions.map((session) => (
                <Card key={session.session_id} className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        {getDeviceIcon(session.user_agent)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="space-y-1 text-sm">
                          {session.user_agent && (
                            <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100">
                              <Monitor className="w-4 h-4" />
                              <span className="truncate font-medium">
                                {session.user_agent}
                              </span>
                            </div>
                          )}
                          {session.ip_address && (
                            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                              <Globe className="w-4 h-4" />
                              <span>{session.ip_address}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                            <Clock className="w-4 h-4" />
                            <span>
                              Last active:{" "}
                              {formatDate(session.last_activity_at)}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-500">
                            Session ID: {session.session_id.slice(0, 8)}...
                          </div>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevokeSession(session.session_id)}
                      disabled={revokingSessionId === session.session_id}
                      className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      {revokingSessionId === session.session_id ? (
                        <>
                          <LoadingSpinner size="sm" />
                          Revoking...
                        </>
                      ) : (
                        <>
                          <Trash2 className="w-4 h-4" />
                          Revoke
                        </>
                      )}
                    </Button>
                  </div>
                </Card>
              ))}
            </>
          )}
        </div>
      )}

      {/* Security Notice */}
      <Card className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-amber-800 dark:text-amber-200">
            <p className="font-medium mb-1">Security Tip</p>
            <p>
              If you see any sessions you don't recognize, revoke them
              immediately and consider changing your password. Each session
              represents a device or browser where you're signed in.
            </p>
          </div>
        </div>
      </Card>

      {/* Revoke All Modal */}
      <ConfirmModal
        isOpen={showRevokeAllModal}
        onClose={() => setShowRevokeAllModal(false)}
        onConfirm={handleRevokeAllOtherSessions}
        title="Sign out all other devices?"
        description={`This will sign you out from ${otherSessions.length} other device${otherSessions.length === 1 ? "" : "s"}. Your current session will remain active.`}
        confirmText={revokingAll ? "Signing out..." : "Sign out all"}
        variant="danger"
        isLoading={revokingAll}
      />
    </div>
  );
}
