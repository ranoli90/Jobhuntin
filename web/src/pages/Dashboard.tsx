import { ArrowUpRight, BarChart3, Briefcase, DollarSign, Inbox, Rocket, MessageCircle } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBilling } from "../hooks/useBilling";
import { useApplications } from "../hooks/useApplications";
import { HowItWorksCard } from "../components/trust/HowItWorksCard";
import { SafetyPillars } from "../components/trust/SafetyPillars";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const { applications, holdApplications, byStatus, stats, isLoading } = useApplications();

  const metrics = [
    { label: "Apps running", value: String(byStatus.APPLYING + byStatus.APPLIED), icon: Briefcase },
    { label: "Success %", value: `${stats.successRate}%`, icon: BarChart3 },
    { label: "HOLDs pending", value: String(byStatus.HOLD), icon: Inbox },
    { label: "This month", value: String(stats.monthlyApps), icon: DollarSign },
  ];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.4em] text-brand-ink/60">Dashboard</p>
          <h1 className="font-display text-4xl">Your command center</h1>
        </div>
        <Button className="gap-2" variant="lagoon" wobble onClick={() => navigate("/app/jobs")}>
          <Rocket className="h-4 w-4" />
          Let's skedaddle!
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label} tone="shell" shadow="lift" className="space-y-3">
            <div className="flex items-center gap-2 text-brand-ink/70">
              <metric.icon className="h-5 w-5 text-brand-sunrise" />
              <span className="text-xs uppercase tracking-[0.3em]">{metric.label}</span>
            </div>
            <p className="text-3xl font-semibold">
              {isLoading ? "—" : metric.value}
            </p>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card tone="sunrise" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Inbox className="h-5 w-5 text-brand-sunrise" />
                <div>
                  <p className="text-sm text-brand-ink/70">HOLD queue</p>
                  <p className="text-2xl font-semibold">
                    {isLoading ? "—" : `${holdApplications.length} pending`}
                  </p>
                </div>
              </div>
              <Badge variant="mango">Needs attention</Badge>
            </div>
            <div className="space-y-3 text-sm">
              {isLoading ? (
                <div className="rounded-2xl bg-white/70 px-4 py-3 text-brand-ink/50">Loading holds...</div>
              ) : holdApplications.length === 0 ? (
                <div className="rounded-2xl bg-white/70 px-4 py-3 text-brand-ink/70">
                  No pending questions. You're all caught up!
                </div>
              ) : (
                holdApplications.slice(0, 3).map((app) => (
                  <div key={app.id} className="flex items-center justify-between rounded-2xl bg-white/70 px-4 py-3">
                    <div className="flex items-center gap-3">
                      <MessageCircle className="h-4 w-4 text-brand-sunrise" />
                      <div>
                        <p className="font-medium">{app.company}</p>
                        <p className="text-xs text-brand-ink/60">{app.hold_question?.slice(0, 50)}...</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => navigate("/app/applications")}>
                      Answer
                    </Button>
                  </div>
                ))
              )}
            </div>
            {holdApplications.length > 3 && (
              <Button variant="outline" size="sm" className="w-full" onClick={() => navigate("/app/applications")}>
                View all {holdApplications.length} holds
              </Button>
            )}
          </Card>
          
          <HowItWorksCard />
        </div>
        
        <div className="space-y-6">
          <Card tone="lagoon" className="space-y-3">
            <p className="text-sm text-brand-ink/70">Plan snapshot</p>
            <p className="text-3xl font-semibold">{status?.plan ?? "FREE"}</p>
            <p className="text-sm text-brand-ink/70">
              Seats: {status?.seats ?? 1} · Success rate: {status?.success_rate ?? 72}%
            </p>
            <Button variant="outline" onClick={() => navigate("/app/billing")}>Upgrade</Button>
          </Card>
          
          <SafetyPillars />
        </div>
      </div>
    </div>
  );
}

export function JobsView() {
  return (
    <Card tone="shell">
      <h2 className="text-2xl font-semibold">Jobs</h2>
      <p className="mt-2 text-brand-ink/70">Coming soon: filterable job radar synced from the Playwright agent.</p>
    </Card>
  );
}

export function ApplicationsView() {
  return (
    <Card tone="shell">
      <h2 className="text-2xl font-semibold">Applications</h2>
      <p className="mt-2 text-brand-ink/70">Track every application, hold state, and nudges in one board.</p>
    </Card>
  );
}

export function HoldsView() {
  return (
    <Card tone="shell">
      <h2 className="text-2xl font-semibold">HOLD Inbox</h2>
      <p className="mt-2 text-brand-ink/70">Inbox timeline showcasing who needs love next.</p>
    </Card>
  );
}

export function TeamView() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const isSolo = !status?.seats || status.seats <= 1;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm uppercase tracking-[0.35em] text-brand-ink/60">Team</p>
        <h1 className="font-display text-4xl">Your workspace</h1>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card tone="shell" shadow="lift" className="p-6">
          <h2 className="font-display text-xl text-brand-ink">Current plan</h2>
          <p className="mt-2 text-brand-ink/70">
            {isSolo
              ? "You're on the Solo plan. All applications and HOLDs are yours. Upgrade to add teammates and share pipelines."
              : `You have ${status?.seats ?? 1} seat(s). Invite teammates from Billing.`}
          </p>
          <Button
            variant={isSolo ? "primary" : "outline"}
            className="mt-4"
            onClick={() => navigate("/app/billing")}
          >
            {isSolo ? "Upgrade for team features" : "Manage billing"}
          </Button>
        </Card>
        <Card tone="shell" className="p-6">
          <h2 className="font-display text-xl text-brand-ink">Team features</h2>
          <ul className="mt-3 space-y-2 text-sm text-brand-ink/70">
            <li>• Shared job pipeline and applications</li>
            <li>• Invite members with roles (Admin, Member)</li>
            <li>• Central billing and usage</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

export function BillingView() {
  return (
    <Card tone="shell">
      <h2 className="text-2xl font-semibold">Billing</h2>
      <p className="mt-2 text-brand-ink/70">Stripe-powered checkout and seat management coming shortly.</p>
    </Card>
  );
}
