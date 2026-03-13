import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle, Clock, Quote, Send, AlertTriangle } from "lucide-react";
import { useState, useEffect } from "react";
import { useApplications } from "../../hooks/useApplications";
import { useHoldNotifications } from "../../hooks/useHoldNotifications";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { LoadingSpinner } from "../../components/ui/LoadingSpinner";
import { sharedLocale, sharedRtl } from "./shared";

/**
 * Deadline countdown component for time-sensitive hold questions
 */
function DeadlineCountdown({ lastActivity }: { lastActivity: string }) {
  const [timeRemaining, setTimeRemaining] = useState<{
    days: number;
    hours: number;
    minutes: number;
    isUrgent: boolean;
    isOverdue: boolean;
  }>({
    days: 0,
    hours: 0,
    minutes: 0,
    isUrgent: false,
    isOverdue: false,
  });

  useEffect(() => {
    // Calculate deadline: 48 hours from last activity
    const deadline = new Date(new Date(lastActivity).getTime() + 48 * 60 * 60 * 1000);
    const now = new Date();
    const total = deadline.getTime() - now.getTime();
    
    if (total <= 0) {
      setTimeRemaining({ days: 0, hours: 0, minutes: 0, isUrgent: true, isOverdue: true });
      return;
    }
    
    const days = Math.floor(total / (1000 * 60 * 60 * 24));
    const hours = Math.floor((total % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((total % (1000 * 60 * 60)) / (1000 * 60));
    const isUrgent = total < 4 * 60 * 60 * 1000;
    
    setTimeRemaining({ days, hours, minutes, isUrgent, isOverdue: false });
  }, [lastActivity]);

  if (timeRemaining.isOverdue) {
    return (
      <Badge variant="error" className="rounded-md font-bold text-[10px] flex items-center gap-1">
        <AlertTriangle className="w-3 h-3" />
        OVERDUE
      </Badge>
    );
  }

  if (timeRemaining.isUrgent) {
    return (
      <Badge variant="warning" className="rounded-md font-bold text-[10px] flex items-center gap-1 bg-red-100 text-red-700 border-red-200">
        <Clock className="w-3 h-3" />
        {timeRemaining.hours}h {timeRemaining.minutes}m
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="rounded-md font-bold text-[10px] text-brand-muted flex items-center gap-1">
      <Clock className="w-3 h-3" />
      {timeRemaining.days > 0 ? `${timeRemaining.days}d` : `${timeRemaining.hours}h`} left
    </Badge>
  );
}

export default function HoldsView() {
  const {
    holdApplications,
    answerHold,
    snoozeApplication,
    isLoading,
    error,
    refetch,
    isSubmitting,
  } = useApplications();
  
  // Enhanced hold notifications hook
  const {
    urgentNotifications,
    unreadCount,
    preferences,
    handleQuickAnswer,
    handleQuickAnswerChange,
    handleSnooze,
    getQuickAnswer,
    calculateTimeRemaining,
  } = useHoldNotifications();
  
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showQuickAnswer, setShowQuickAnswer] = useState<Record<string, boolean>>({});
  const shouldReduceMotion = useReducedMotion();
  const locale = sharedLocale;
  const rtl = sharedRtl;

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-6 text-center">
          <p className="text-brand-muted mb-4">
            Unable to load items needing your input.
          </p>
          <Button onClick={() => refetch()}>Try again</Button>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className="max-w-4xl mx-auto space-y-6 pb-6 px-4 lg:px-0"
        aria-busy="true"
        aria-label="Loading items needing your input"
      >
        <div className="space-y-2">
          <div className="h-8 w-56 bg-brand-border rounded animate-pulse" />
          <div className="h-4 w-72 bg-brand-gray rounded animate-pulse" />
        </div>
        <div className="space-y-6">
          {[1, 2, 3].map((index) => (
            <div
              key={index}
              className="p-0 overflow-hidden border border-brand-border rounded-2xl animate-pulse"
            >
              <div className="bg-brand-gray border-b border-brand-border p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-brand-border" />
                  <div className="space-y-2">
                    <div className="h-4 w-24 bg-brand-border rounded" />
                    <div className="h-3 w-32 bg-brand-gray rounded" />
                  </div>
                </div>
                <div className="h-6 w-24 bg-amber-100 rounded" />
              </div>
              <div className="p-6 space-y-4">
                <div className="h-16 bg-amber-50 rounded-2xl" />
                <div className="h-24 bg-brand-gray rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (holdApplications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 px-6">
        <div className="w-12 h-12 rounded-full border-2 border-brand-border flex items-center justify-center mb-6">
          <CheckCircle className="w-5 h-5 text-brand-muted" />
        </div>
        <h2 className="text-lg font-semibold text-brand-text mb-1">
          Nothing needs your attention
        </h2>
        <p className="text-sm text-brand-muted max-w-xs mx-auto text-center mb-4">
          All your applications are progressing. When the agent needs input from
          you, it will appear here.
        </p>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-gray border border-brand-border">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-brand-muted">Agent active</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
      <div>
        <h2 className="text-2xl font-black text-brand-text tracking-tight">
          Items Needing Your Input
        </h2>
        <p className="text-brand-muted font-medium">
          Your AI agent needs clarification on these {holdApplications.length}{" "}
          threads.
        </p>
      </div>

      <div className="space-y-6">
        {holdApplications.map((app, index) => (
          <motion.div
            key={app.id}
            initial={shouldReduceMotion ? undefined : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={
              shouldReduceMotion
                ? undefined
                : { delay: index * 0.05, duration: 0.25 }
            }
          >
            <Card
              className="p-0 overflow-hidden border-brand-border rounded-xl"
              shadow="lift"
            >
              <div className="bg-brand-gray border-b border-brand-border p-3 sm:p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-brand-primary flex items-center justify-center text-white font-bold text-xs">
                    {(app.company ?? "").charAt(0) || "?"}
                  </div>
                  <div>
                    <h3 className="font-bold text-brand-text text-sm">
                      {app.company ?? "Unknown"}
                    </h3>
                    <p className="text-[10px] text-brand-muted font-medium uppercase tracking-wider">
                      {app.job_title}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {/* Deadline countdown if available */}
                  {app.last_activity && (
                    <DeadlineCountdown lastActivity={app.last_activity} />
                  )}
                  <Badge
                    variant="warning"
                    className="rounded-md font-bold text-[10px]"
                  >
                    RESPONSE REQUIRED
                  </Badge>
              </div>

              <div className="p-4 sm:p-6 space-y-6">
                <div
                  id={`hold-question-${app.id}`}
                  className="bg-amber-50 rounded-2xl p-4 sm:p-6 border border-amber-100 relative"
                >
                  <Quote className="absolute top-4 left-4 w-12 h-12 text-amber-200/50 -z-0" />
                  <p className="text-amber-900 font-medium leading-relaxed relative z-10">
                    "I've encountered a specific question on the portal:{" "}
                    <span className="font-black italic">
                      '{app.hold_question ?? "No question provided"}'
                    </span>
                    . How should I proceed?"
                  </p>
                </div>

                <div className="space-y-4">
                  <label htmlFor={`hold-answer-${app.id}`} className="sr-only">
                    Your response for {app.company ?? "Unknown"} —{" "}
                    {app.job_title}
                  </label>
                  <textarea
                    id={`hold-answer-${app.id}`}
                    className="w-full p-4 rounded-xl border border-brand-border text-sm focus:ring-2 focus:ring-brand-primary/20 focus:border-brand-primary transition-all bg-white dark:bg-slate-900 dark:border-slate-700 dark:text-slate-100 font-medium min-h-[100px]"
                    maxLength={5000}
                    placeholder="Type your response here... (e.g. Yes, I have 5 years experience with Kubernetes)"
                    value={answers[app.id] || ""}
                    onChange={(e) =>
                      setAnswers((previous) => ({
                        ...previous,
                        [app.id]: e.target.value,
                      }))
                    }
                    aria-describedby={`hold-question-${app.id}`}
                  />
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] text-brand-muted">
                      {(answers[app.id] || "").length}/5000 characters
                    </p>
                    {(answers[app.id] || "").length > 4500 && (
                      <p className="text-[10px] text-amber-500 font-medium">
                        {5000 - (answers[app.id] || "").length} characters
                        remaining
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4 sticky bottom-0 bg-white/90 backdrop-blur p-2 rounded-xl border border-brand-border/50">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-brand-muted hover:text-brand-text font-bold text-xs uppercase"
                      disabled={isSubmitting(app.id)}
                      onClick={() => snoozeApplication(app.id)}
                    >
                      {isSubmitting(app.id) ? (
                        <LoadingSpinner className="w-4 h-4 mr-2" />
                      ) : (
                        <Clock className="w-4 h-4 mr-2" />
                      )}{" "}
                      Snooze 24h
                    </Button>
                    <Button
                      disabled={!answers[app.id] || isSubmitting(app.id)}
                      onClick={() => answerHold(app.id, answers[app.id])}
                      className="bg-brand-primary hover:bg-brand-primaryHover text-white font-bold rounded-xl px-6 sm:px-8 shadow-lg shadow-brand-primary/20"
                    >
                      {isSubmitting(app.id) ? (
                        <>
                          <LoadingSpinner className="mr-2 w-4 h-4" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 w-4 h-4" />
                          Send Instructions
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
