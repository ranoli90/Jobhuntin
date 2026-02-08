import * as React from "react";
import { Search, FileText, Send, PartyPopper } from "lucide-react";

const STEPS = [
  {
    icon: Search,
    title: "We find matches",
    description: "Our AI scans thousands of listings to find jobs that actually fit your skills and goals.",
    color: "bg-blue-50 text-blue-600 border-blue-200",
  },
  {
    icon: FileText,
    title: "We customize apps",
    description: "No generic resumes. We tailor every application to highlight why you're perfect for that role.",
    color: "bg-primary-50 text-primary-600 border-primary-200",
  },
  {
    icon: Send,
    title: "We apply for you",
    description: "Click once, we handle the forms, cover letters, and submissions. You just show up for interviews.",
    color: "bg-violet-50 text-violet-600 border-violet-200",
  },
  {
    icon: PartyPopper,
    title: "You land offers",
    description: "Track everything in one place. When offers roll in, you pick the best one. We'll celebrate with you.",
    color: "bg-emerald-50 text-emerald-600 border-emerald-200",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="relative py-24 lg:py-32 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-16 lg:mb-20 text-center">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wider text-primary-600">How it works</p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900">
            Your job search, on autopilot
          </h2>
          <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
            Four simple steps to transform your job hunt from tedious to effortless
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="relative group"
              >
                <div className="h-full rounded-xl bg-white border border-slate-200 p-6 transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
                  {/* Step number */}
                  <div className="absolute -top-3 -right-3 flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white text-sm font-bold shadow-md">
                    {index + 1}
                  </div>

                  {/* Icon */}
                  <div className={`mb-4 inline-flex rounded-xl border p-3 ${step.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>

                  <h3 className="mb-2 text-lg font-semibold text-slate-900">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-600">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
