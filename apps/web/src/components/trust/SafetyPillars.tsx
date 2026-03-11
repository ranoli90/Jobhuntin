import * as React from "react";
import { Shield, Lock, EyeOff, Mail, Ban } from "lucide-react";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

const PILLARS = [
  {
    icon: Shield,
    title: "We never spam employers",
    description:
      "Every application is thoughtful and tailored. We don't blast generic resumes.",
  },
  {
    icon: Lock,
    title: "Your data stays yours",
    description:
      "Encrypted storage, no selling to third parties, delete anytime with one click.",
  },
  {
    icon: EyeOff,
    title: "We never modify without approval",
    description:
      "Every resume tweak and cover letter is shown to you first. You always approve.",
  },
  {
    icon: Mail,
    title: "Your email, your identity",
    description:
      "All applications come from your email address. Employers never know we helped.",
  },
  {
    icon: Ban,
    title: "No Terms of Service violations",
    description:
      "We respect job site rules. We don't scrape illegally or use fake accounts.",
  },
];

export function SafetyPillars() {
  return (
    <Card tone="lagoon" shadow="lift" className="p-6">
      <div className="mb-6 flex items-center gap-3">
        <Badge variant="lagoon" className="text-lg">
          🛡️
        </Badge>
        <h3 className="font-display text-xl text-brand-ink">
          What we never do
        </h3>
      </div>
      <div className="space-y-4">
        {PILLARS.map((pillar) => {
          const Icon = pillar.icon;
          return (
            <div key={pillar.title} className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/50">
                <Icon className="h-5 w-5 text-brand-ink" />
              </div>
              <div>
                <h4 className="font-semibold text-brand-ink">{pillar.title}</h4>
                <p className="mt-1 text-sm text-brand-ink/70">
                  {pillar.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
