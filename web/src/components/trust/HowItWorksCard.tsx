import * as React from "react";
import { Sparkles, FileText, Send, MessageCircle } from "lucide-react";
import { Card } from "../ui/Card";

const STEPS = [
  {
    icon: Sparkles,
    title: "We scan job boards",
    description: "Our AI finds matches based on your skills, experience, and preferences—24/7.",
  },
  {
    icon: FileText,
    title: "We craft tailored apps",
    description: "Every resume and cover letter is customized for that specific role. No templates.",
  },
  {
    icon: Send,
    title: "We submit for you",
    description: "We fill out forms, upload documents, and hit submit—correctly, every time.",
  },
  {
    icon: MessageCircle,
    title: "We handle HOLDs",
    description: "When employers ask questions, we draft responses for you to approve and send.",
  },
];

export function HowItWorksCard() {
  return (
    <Card tone="shell" shadow="lift" className="p-6">
      <h3 className="mb-6 font-display text-xl text-brand-ink">
        How JobHuntin applies on your behalf
      </h3>
      <div className="space-y-4">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.title} className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-sunrise/20">
                <Icon className="h-5 w-5 text-brand-sunrise" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-brand-sunrise">{index + 1}</span>
                  <h4 className="font-semibold text-brand-ink">{step.title}</h4>
                </div>
                <p className="mt-1 text-sm text-brand-ink/70">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
