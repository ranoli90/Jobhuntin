import { ArrowUpRight, BarChart3, Briefcase, DollarSign, Inbox, Rocket, MessageCircle, TrendingUp, CheckCircle, Clock, Zap } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useBilling } from "../hooks/useBilling";
import { useApplications } from "../hooks/useApplications";
import { HowItWorksCard } from "../components/trust/HowItWorksCard";
import { SafetyPillars } from "../components/trust/SafetyPillars";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const AnimatedNumber = ({ value, duration = 1.5 }: { value: number | string; duration?: number }) => {
  const [displayValue, setDisplayValue] = useState(0);
  
  useEffect(() => {
    const numValue = Number(value);
    if (isNaN(numValue)) return;
    
    let start = 0;
    const end = numValue;
    const increment = end / (duration * 60); // 60fps
    
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(start));
      }
    }, 1000/60);
    
    return () => clearInterval(timer);
  }, [value, duration]);
  
  return <span>{typeof value === 'string' ? value : displayValue}</span>;
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { status } = useBilling();
  const { applications, holdApplications, byStatus, stats, isLoading } = useApplications();
  const [isHovered, setIsHovered] = useState(false);

  const metrics = [
    { 
      label: "Active Applications", 
      value: byStatus.APPLYING + byStatus.APPLIED, 
      icon: Briefcase,
      trend: 12.5,
      delta: 'up',
      color: 'from-blue-500/20 to-blue-600/10',
      iconColor: 'text-blue-400'
    },
    { 
      label: "Success Rate", 
      value: `${stats.successRate}%`, 
      icon: BarChart3,
      trend: 3.2,
      delta: 'up',
      color: 'from-emerald-500/20 to-emerald-600/10',
      iconColor: 'text-emerald-400'
    },
    { 
      label: "Pending HOLDs", 
      value: byStatus.HOLD, 
      icon: Inbox,
      trend: 2,
      delta: 'down',
      color: 'from-amber-500/20 to-amber-600/10',
      iconColor: 'text-amber-400'
    },
    { 
      label: "Monthly Volume", 
      value: stats.monthlyApps, 
      icon: Zap,
      trend: 28,
      delta: 'up',
      color: 'from-purple-500/20 to-purple-600/10',
      iconColor: 'text-purple-400'
    },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <p className="text-sm font-medium uppercase tracking-[0.4em] text-brand-ink/60">Dashboard</p>
          <h1 className="font-display text-4xl font-bold bg-gradient-to-r from-brand-ink to-brand-ink/80 bg-clip-text text-transparent">
            Your Command Center
          </h1>
        </motion.div>
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Button 
            className="group relative overflow-hidden gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white shadow-lg hover:shadow-cyan-500/20 transition-all duration-300"
            onClick={() => navigate("/app/jobs")}
          >
            <span className="relative z-10 flex items-center gap-2">
              <Rocket className="h-5 w-5 transition-transform group-hover:rotate-12" />
              <span className="font-medium">Find Jobs</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
          </Button>
        </motion.div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
            className="h-full"
          >
            <Card 
              className="h-full backdrop-blur-sm bg-white/5 hover:bg-white/10 transition-all duration-300 border border-white/10 hover:border-white/20 group"
              shadow="lift"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-brand-ink/70">
                    <metric.icon className={`h-4 w-4 ${metric.iconColor}`} />
                    <span>{metric.label}</span>
                  </div>
                  <p className="text-2xl font-bold text-white">
                    {isLoading ? (
                      <span className="inline-block h-8 w-16 bg-white/10 rounded animate-pulse"></span>
                    ) : typeof metric.value === 'string' ? (
                      metric.value
                    ) : (
                      <AnimatedNumber value={metric.value} />
                    )}
                  </p>
                </div>
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  metric.delta === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {metric.delta === 'up' ? (
                    <TrendingUp className="h-3 w-3 mr-1" />
                  ) : (
                    <ArrowUpRight className="h-3 w-3 mr-1 transform rotate-180" />
                  )}
                  {metric.trend}%
                </div>
              </div>
              <div className="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div 
                  className={`h-full rounded-full bg-gradient-to-r ${metric.color}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, 30 + index * 10)}%` }}
                  transition={{ delay: 0.3 + index * 0.1, duration: 0.8, type: 'spring' }}
                />
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="relative overflow-hidden bg-gradient-to-br from-amber-500/5 to-amber-600/10 border border-amber-500/20 backdrop-blur-sm">
              {/* Animated background elements */}
              <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-amber-500/10 blur-3xl"></div>
                <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-amber-400/10 blur-3xl"></div>
              </div>
              
              <div className="relative z-10 space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10">
                      <Inbox className="h-5 w-5 text-amber-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-amber-100/80">HOLD QUEUE</p>
                      <p className="text-2xl font-bold text-white">
                        {isLoading ? (
                          <span className="inline-block h-7 w-24 bg-white/10 rounded animate-pulse"></span>
                        ) : (
                          `${holdApplications.length} Pending`
                        )}
                      </p>
                    </div>
                  </div>
                  <Badge className="bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20 transition-colors">
                    Needs attention
                  </Badge>
                </div>
                <div className="space-y-3">
                  {isLoading ? (
                    <div className="rounded-xl bg-white/5 p-4">
                      <div className="h-4 w-3/4 rounded bg-white/10 animate-pulse"></div>
                      <div className="mt-2 h-3 w-1/2 rounded bg-white/5 animate-pulse"></div>
                    </div>
                  ) : holdApplications.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-amber-500/30 bg-amber-500/5 p-6 text-center">
                      <CheckCircle className="mx-auto h-8 w-8 text-amber-400/70 mb-2" />
                      <p className="text-amber-100/80">No pending questions</p>
                      <p className="text-sm text-amber-100/50">You're all caught up!</p>
                    </div>
                  ) : (
                    <motion.div 
                      className="space-y-3"
                      initial="hidden"
                      animate="visible"
                      variants={{
                        hidden: { opacity: 0 },
                        visible: {
                          opacity: 1,
                          transition: {
                            staggerChildren: 0.1
                          }
                        }
                      }}
                    >
                      {holdApplications.slice(0, 3).map((app, idx) => (
                        <motion.div 
                          key={app.id} 
                          className="group flex items-center justify-between rounded-xl bg-white/5 p-4 backdrop-blur-sm transition-all hover:bg-white/10 hover:shadow-lg hover:shadow-amber-500/5 border border-white/5 hover:border-amber-500/20"
                          variants={{
                            hidden: { opacity: 0, y: 10 },
                            visible: { 
                              opacity: 1, 
                              y: 0,
                              transition: { type: 'spring', stiffness: 300, damping: 20 }
                            }
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400">
                              <MessageCircle className="h-3.5 w-3.5" />
                            </div>
                            <div className="min-w-0">
                              <p className="truncate font-medium text-white">{app.company}</p>
                              <p className="text-xs text-amber-100/60 truncate">
                                {app.hold_question?.slice(0, 50)}{app.hold_question && app.hold_question.length > 50 ? '...' : ''}
                              </p>
                            </div>
                          </div>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-xs font-medium bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 hover:text-white transition-colors"
                            onClick={() => navigate("/app/applications")}
                          >
                            Review
                          </Button>
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </div>
                {holdApplications.length > 3 && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="w-full mt-3 bg-white/5 border-white/10 text-amber-100 hover:bg-amber-500/10 hover:border-amber-500/30 hover:text-amber-50 transition-colors"
                    onClick={() => navigate("/app/applications")}
                  >
                    View all {holdApplications.length} holds
                  </Button>
                )}
              </div>
            </Card>
          </motion.div>
          
          <HowItWorksCard />
        </div>
        
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="relative overflow-hidden bg-gradient-to-br from-brand-lagoon/5 to-brand-lagoon/10 border border-brand-lagoon/20 backdrop-blur-sm">
              {/* Animated background elements */}
              <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-brand-lagoon/10 blur-3xl"></div>
                <div className="absolute -left-10 -bottom-10 h-40 w-40 rounded-full bg-brand-lagoon/5 blur-3xl"></div>
              </div>
              
              <div className="relative z-10 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-brand-lagoon-300/80">CURRENT PLAN</p>
                    <p className="text-2xl font-bold text-white">{status?.plan ?? "FREE"}</p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-lagoon/10 text-brand-lagoon-300">
                    <Zap className="h-5 w-5" />
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Team Seats</span>
                    <span className="font-medium">{status?.seats ?? 1} Active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Success Rate</span>
                    <span className="font-medium text-emerald-400">{status?.success_rate ?? 72}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Next Billing</span>
                    <div className="flex items-center">
                      <Clock className="h-3.5 w-3.5 mr-1 text-brand-lagoon-300/70" />
                      <span>Mar 1, 2025</span>
                    </div>
                  </div>
                </div>
                
                <Button 
                  className="w-full mt-2 bg-brand-lagoon/90 hover:bg-brand-lagoon text-white hover:shadow-lg hover:shadow-brand-lagoon/20 transition-all"
                  onClick={() => navigate("/app/billing")}
                >
                  Upgrade Plan
                </Button>
              </div>
            </Card>
          </motion.div>
          
          <SafetyPillars />
        </div>
      </div>
    </motion.div>
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
