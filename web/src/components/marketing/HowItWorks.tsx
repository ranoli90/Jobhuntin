import * as React from "react";
import { Search, FileText, Send, PartyPopper } from "lucide-react";

const STEPS = [
  {
    icon: Search,
    title: "We find matches",
    description: "Our AI scans thousands of listings to find jobs that actually fit your skills and goals.",
    color: "bg-brand-lagoon/20 text-brand-lagoon",
  },
  {
    icon: FileText,
    title: "We customize apps",
    description: "No generic resumes. We tailor every application to highlight why you're perfect for that role.",
    color: "bg-brand-sunrise/20 text-brand-sunrise",
  },
  {
    icon: Send,
    title: "We apply for you",
    description: "Click once, we handle the forms, cover letters, and submissions. You just show up for interviews.",
    color: "bg-brand-plum/20 text-brand-plum",
  },
  {
    icon: PartyPopper,
    title: "You land offers",
    description: "Track everything in one place. When offers roll in, you pick the best one. We'll celebrate with you.",
    color: "bg-brand-mango/20 text-brand-mango",
  },
];

export function HowItWorks() {
  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-16 text-center">
          <p className="mb-2 text-sm uppercase tracking-[0.3em] text-brand-ink/50">How it works</p>
          <h2 className="font-display text-4xl text-brand-ink">Your job search, on autopilot</h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="group relative rounded-3xl border border-white/70 bg-white p-8 transition-all hover:-translate-y-2 hover:shadow-xl"
              >
                {/* Step number */}
                <div className="absolute -top-4 -right-4 flex h-10 w-10 items-center justify-center rounded-full bg-brand-shell font-display text-lg text-brand-ink">
                  {index + 1}
                </div>

                {/* Icon */}
                <div className={`mb-6 inline-flex rounded-2xl p-4 ${step.color}`}>
                  <Icon className="h-6 w-6" />
                </div>

                <h3 className="mb-3 font-display text-xl text-brand-ink">{step.title}</h3>
                <p className="text-sm leading-relaxed text-brand-ink/70">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
