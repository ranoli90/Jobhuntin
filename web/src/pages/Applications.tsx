import { useState, useMemo } from "react";
import { Download, Inbox, MessageCircle, Briefcase, HelpCircle, Clock, Calendar, DollarSign, X, Send } from "lucide-react";
import { AppCard } from "../components/Applications/AppCard";
import { useApplications, type ApplicationRecord } from "../hooks/useApplications";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { DataTable } from "../components/ui/DataTable";
import { Badge } from "../components/ui/Badge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { EmptyState } from "../components/ui/EmptyState";
import { COPY } from "../copy";
import { useNavigate } from "react-router-dom";
import { pushToast } from "../lib/toast";
import { downloadFile } from "../lib/api";

export default function ApplicationsPage() {
  const navigate = useNavigate();
  const { applications, holdApplications, stats, byStatus, isLoading, answerHold } = useApplications();
  const [activeHoldId, setActiveHoldId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeHold = useMemo(() => 
    holdApplications.find((app) => app.id === activeHoldId),
    [holdApplications, activeHoldId]
  );

  const ANSWER_TEMPLATES = [
    { icon: Calendar, label: "Availability", text: "I'm available for an interview this week, preferably Tuesday or Thursday afternoon." },
    { icon: DollarSign, label: "Salary expectations", text: "My salary expectation is in the range mentioned in the job posting. I'm open to discussion based on the full package." },
    { icon: HelpCircle, label: "Need clarification", text: "Could you please clarify what specific information you need? I'm happy to provide more details." },
  ];

  const handleAnswer = async () => {
    if (!activeHoldId || !answerText.trim()) return;
    setIsSubmitting(true);
    try {
      await answerHold(activeHoldId, answerText);
      setActiveHoldId(null);
      setAnswerText("");
    } catch (err) {
      pushToast({ title: "Could not send answer", description: (err as Error).message, tone: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const closeModal = () => {
    setActiveHoldId(null);
    setAnswerText("");
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Applications</p>
          <h1 className="font-display text-4xl">Your momentum board</h1>
        </div>
        <Button
          variant="ghost"
          className="gap-2"
          onClick={async () => {
            try {
              await downloadFile("applications/export", "applications.csv");
              pushToast({ title: "Export complete", tone: "success" });
            } catch (err) {
              pushToast({ title: "Export failed", description: (err as Error).message, tone: "error" });
            }
          }}
        >
          <Download className="h-4 w-4" /> Export CSV
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {Object.entries(byStatus).map(([status, count]) => (
          <Card key={status} tone="shell" shadow="lift">
            <p className="text-xs uppercase tracking-[0.3em] text-brand-ink/60">{status}</p>
            <p className="text-3xl font-semibold text-brand-ink">{count}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">Latest applications</h2>
            <Badge variant="lagoon">{stats.successRate}% success</Badge>
          </div>
          {isLoading ? (
            <LoadingSpinner />
          ) : applications.length ? (
            <div className="space-y-4">
              {applications.slice(0, 5).map((app) => (
                <AppCard key={app.id} application={app} onAnswerHold={setActiveHoldId} />
              ))}
            </div>
          ) : (
            <EmptyState 
              title={COPY.empty.applications.title} 
              description={COPY.empty.applications.description}
              actionLabel={COPY.empty.applications.action}
              icon={<Briefcase className="h-8 w-8 text-brand-ink/40" />}
              onAction={() => navigate("/app/jobs")}
            />
          )}
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 text-brand-ink">
            <Inbox className="h-5 w-5" />
            <h2 className="font-display text-xl">HOLD inbox</h2>
          </div>
          {holdApplications.length ? (
            <div className="space-y-4">
              {holdApplications.map((app) => (
                <AppCard key={`${app.id}-hold`} application={app} onAnswerHold={setActiveHoldId} />
              ))}
            </div>
          ) : (
            <EmptyState 
              title={COPY.empty.holds.title}
              description={COPY.empty.holds.description}
              actionLabel={COPY.empty.holds.action}
              icon={<MessageCircle className="h-8 w-8 text-brand-ink/40" />}
              onAction={() => navigate("/app/applications")}
            />
          )}
        </section>
      </div>

      <Card tone="shell" shadow="lift">
        <h2 className="font-display text-2xl mb-4">Full log</h2>
        <DataTable
          data={applications}
          columns={[
            { header: "Job", key: "job_title" },
            { header: "Company", key: "company" },
            { header: "Status", key: "status", render: (value) => <Badge variant="outline">{value}</Badge> },
            {
              header: "Updated",
              key: "last_activity",
              render: (value) => (value ? new Date(String(value)).toLocaleDateString() : "today"),
            },
          ]}
          emptyLabel="No applications logged"
        />
      </Card>

      {activeHoldId && activeHold ? (
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
                onChange={(e) => setAnswerText(e.target.value)}
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
      ) : null}
    </div>
  );
}
