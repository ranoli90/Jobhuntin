import * as React from "react";
import { Sparkles, Users, Zap } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { cn } from "../../lib/utils";

interface UpgradeCardProps {
  currentPlan: "FREE" | "PRO" | "TEAM";
  onUpgrade: () => void;
  onAddSeats?: () => void;
  className?: string;
}

const PLANS = {
  FREE: { name: "Free", price: "$0", features: ["10 swipes/day", "Basic filters", "Email support"] },
  PRO: { name: "Pro", price: "$19/mo", features: ["Unlimited swipes", "Priority matching", "HOLD inbox", "Export CSV"] },
  TEAM: { name: "Team", price: "$49/seat", features: ["Everything in Pro", "Team dashboard", "Shared pipeline", "SSO ready"] },
};

export function UpgradeCard({ currentPlan, onUpgrade, onAddSeats, className }: UpgradeCardProps) {
  const isPro = currentPlan === "PRO";
  const isTeam = currentPlan === "TEAM";

  return (
    <Card tone="sunrise" shadow="lift" className={cn("p-6", className)}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-brand-ink" />
            <h3 className="font-display text-2xl">{isTeam ? "Team plan active" : isPro ? "Pro plan active" : "Unlock unlimited"}</h3>
          </div>
          <p className="mt-1 text-sm text-brand-ink/70">
            {isTeam ? "Manage your team and scale hiring together." : isPro ? "You're flying at full speed." : "Upgrade to apply without limits."}
          </p>
        </div>
        <Badge variant="outline" className="bg-white/50">
          {PLANS[currentPlan].price}
        </Badge>
      </div>

      <div className="mt-4 space-y-2">
        {PLANS[currentPlan].features.map((feature) => (
          <div key={feature} className="flex items-center gap-2 text-sm text-brand-ink">
            <Zap className="h-4 w-4 text-brand-lagoon" />
            {feature}
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        {!isPro && !isTeam && (
          <Button variant="primary" onClick={onUpgrade}>
            Upgrade to Pro
          </Button>
        )}
        {isPro && onAddSeats && (
          <Button variant="lagoon" onClick={onAddSeats}>
            <Users className="mr-2 h-4 w-4" />
            Add team seats
          </Button>
        )}
        {isTeam && (
          <Button variant="ghost" onClick={onAddSeats}>
            Manage seats
          </Button>
        )}
      </div>
    </Card>
  );
}
