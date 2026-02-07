import { useState, useMemo, useEffect } from "react";
import { Inbox, MessageCircle, Clock, ArrowRight, HelpCircle, Send, Calendar, DollarSign, X, Filter } from "lucide-react";
import { useApplications, type ApplicationRecord } from "../hooks/useApplications";
import { useAnswerMemory } from "../hooks/useAnswerMemory";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { EmptyState } from "../components/ui/EmptyState";
import { useNavigate } from "react-router-dom";

export default function HoldInbox() {
  const navigate = useNavigate();
  const { holdApplications, isLoading, answerHold, snoozeApplication } = useApplications();
  const { getSuggestion, saveAnswer: saveToMemory } = useAnswerMemory();
  const [activeHoldId, setActiveHoldId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeHold = useMemo(() => 
    holdApplications.find((app) => app.id === activeHoldId),
    [holdApplications, activeHoldId]
  );

  const suggestion = activeHold ? getSuggestion(activeHold.hold_question || "") : null;

  const sortedHolds = useMemo(() => {
    return [...holdApplications].sort((a, b) => {
      const aDate = a.last_activity ? new Date(a.last_activity).getTime() : 0;
      const bDate = b.last_activity ? new Date(b.last_activity).getTime() : 0;
      return aDate - bDate;
    });
  }, [holdApplications]);

  const ANSWER_TEMPLATES = [
    { icon: Calendar, label: "Availability", text: "I'm available for an interview this week, preferably Tuesday or Thursday afternoon." },
    { icon: DollarSign, label: "Salary expectations", text: "My salary expectation is in the range mentioned in the job posting. I'm open to discussion based on the full package." },
    { icon: HelpCircle, label: "Need clarification", text: "Could you please clarify what specific information you need? I'm happy to provide more details." },
  ];

  const handleAnswer = async () => {
    if (!activeHoldId || !answerText.trim()) return;
    
    setIsSubmitting(true);
    try {
      // Save to memory first (fire and forget or await, depending on preference)
      if (activeHold?.hold_question) {
        // We make a best guess at the field type, or default to "text"
        saveToMemory({
          field_label: activeHold.hold_question,
          field_type: "text",
          answer_value: answerText,
        }).catch(console.error);
      }

      await answerHold(activeHoldId, answerText);
      closeModal();
    } catch (err) {
      console.error("Failed to answer hold:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSnooze = async (holdId: string) => {
    try {
      await snoozeApplication(holdId, 24);
      if (activeHoldId === holdId) {
        closeModal();
      }
    } catch (err) {
      console.error("Failed to snooze hold:", err);
    }
  };

  const closeModal = () => {
    setActiveHoldId(null);
    setAnswerText("");
  };

  const getUrgencyBadge = (lastActivity?: string) => {
    if (!lastActivity) return { variant: "outline", label: "New" } as const;
    const days = Math.floor((Date.now() - new Date(lastActivity).getTime()) / (1000 * 60 * 60 * 24));
    if (days >= 3) return { variant: "ink", label: `${days}d ago` } as const;
    if (days >= 1) return { variant: "mango", label: `${days}d ago` } as const;
    return { variant: "lagoon", label: "Today" } as const;
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">HOLD Inbox</p>
          <h1 className="font-display text-4xl">Answer to unblock</h1>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="mango" className="text-sm">
            <Inbox className="mr-2 h-4 w-4" />
            {holdApplications.length} pending
          </Badge>
          <Button variant="ghost" size="sm" onClick={() => navigate("/app/applications")}>
            View all applications
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner label="Loading holds..." />
      ) : sortedHolds.length === 0 ? (
        <EmptyState
          title="No pending questions"
          description="You're all caught up! We'll notify you when an employer has a question."
          actionLabel="Browse jobs"
          icon={<Inbox className="h-12 w-12 text-brand-ink/30" />}
          onAction={() => navigate("/app/jobs")}
        />
      ) : (
        <div className="space-y-4">
          {sortedHolds.map((hold) => {
            const urgency = getUrgencyBadge(hold.last_activity);
            return (
              <Card key={hold.id} tone="sunrise" className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-sunrise/20">
                      <MessageCircle className="h-6 w-6 text-brand-sunrise" />
                    </div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="font-display text-xl">{hold.job_title}</h3>
                        <Badge variant={urgency.variant}>{urgency.label}</Badge>
                      </div>
                      <p className="text-brand-ink/70">{hold.company}</p>
                      <div className="mt-3 rounded-2xl border border-dashed border-brand-sunrise/30 bg-brand-sunrise/10 p-3">
                        <p className="text-sm text-brand-ink">
                          <span className="font-medium">Question:</span> {hold.hold_question || "No question provided"}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => setActiveHoldId(hold.id)}
                    >
                      Answer now
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleSnooze(hold.id)}
                    >
                      Snooze 24h
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {activeHoldId && activeHold && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-6">
          <Card tone="sunrise" className="w-full max-w-lg p-6 shadow-2xl">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-sunrise/20">
                  <MessageCircle className="h-6 w-6 text-brand-sunrise" />
                </div>
                <div>
                  <h3 className="font-display text-xl">Answer required</h3>
                  <p className="text-sm text-brand-ink/60">{activeHold.company} — {activeHold.job_title}</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={closeModal}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="mt-6 rounded-2xl border border-dashed border-brand-sunrise/30 bg-brand-sunrise/10 p-4">
              <div className="flex items-center gap-2 text-sm text-brand-sunrise mb-2">
                <HelpCircle className="h-4 w-4" />
                <span className="font-medium">Employer asks:</span>
              </div>
              <p className="text-brand-ink">{activeHold.hold_question || "No question provided"}</p>
            </div>

            <div className="mt-4">
              <label className="text-sm font-medium text-brand-ink">Your response</label>
              <textarea 
                className="mt-2 w-full rounded-2xl border border-brand-ink/10 bg-white p-4 text-brand-ink" 
                rows={4}
                value={answerText}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAnswerText(e.target.value)}
                placeholder="Type your answer here..."
              />
            </div>

            <div className="mt-4">
              <p className="text-xs uppercase tracking-[0.3em] text-brand-ink/50 mb-3">Quick templates</p>
              <div className="flex flex-wrap gap-2">
                {ANSWER_TEMPLATES.map((template) => (
                  <Button
                    key={template.label}
                    variant="outline"
                    size="sm"
                    onClick={() => setAnswerText(template.text)}
                  >
                    <template.icon className="mr-2 h-3 w-3" />
                    {template.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-brand-ink/50">
                <Clock className="h-3 w-3" />
                <span>Respond within 24h for best results</span>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={closeModal}>
                  Cancel
                </Button>
                <Button 
                  variant="sunrise" 
                  onClick={handleAnswer}
                  disabled={!answerText.trim() || isSubmitting}
                  className="gap-2"
                >
                  <Send className="h-4 w-4" />
                  {isSubmitting ? "Sending..." : "Send answer"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
