import * as React from "react";
import { Star, Quote } from "lucide-react";

const TESTIMONIALS = [
  {
    quote: "I applied to 47 jobs in one afternoon. Got 6 interviews that week. Skedaddle is like having a personal recruiter who never sleeps.",
    author: "Sarah Chen",
    role: "Product Designer",
    company: "Previously at Airbnb",
    result: "Landed at Stripe in 3 weeks",
  },
  {
    quote: "I was skeptical about AI job applications, but the quality blew me away. Every cover letter felt genuinely personal—not template garbage.",
    author: "Marcus Johnson",
    role: "Software Engineer",
    company: "Previously at Meta",
    result: "3 offers, 15% salary bump",
  },
  {
    quote: "As a career switcher, I didn't know how to position myself. Skedaddle figured out my transferable skills and found roles I'd never have found.",
    author: "Priya Patel",
    role: "Former Teacher → UX Researcher",
    company: "Now at Spotify",
    result: "Career change in 2 months",
  },
];

export function Testimonials() {
  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-16 text-center">
          <p className="mb-2 text-sm uppercase tracking-[0.3em] text-brand-ink/50">Success stories</p>
          <h2 className="font-display text-4xl text-brand-ink">Real people, real results</h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <div
              key={i}
              className="relative rounded-3xl border border-white/70 bg-white p-8 transition-all hover:-translate-y-1 hover:shadow-lg"
            >
              <Quote className="absolute right-6 top-6 h-8 w-8 text-brand-shell" />

              {/* Stars */}
              <div className="mb-4 flex gap-1">
                {[...Array(5)].map((_, j) => (
                  <Star key={j} className="h-4 w-4 fill-brand-sunrise text-brand-sunrise" />
                ))}
              </div>

              <p className="mb-6 text-lg leading-relaxed text-brand-ink/80">
                "{t.quote}"
              </p>

              <div className="border-t border-brand-shell pt-4">
                <p className="font-semibold text-brand-ink">{t.author}</p>
                <p className="text-sm text-brand-ink/60">{t.role}</p>
                <p className="text-xs uppercase tracking-[0.2em] text-brand-lagoon mt-2">
                  {t.result}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Stats bar */}
        <div className="mt-16 rounded-3xl bg-brand-ink px-8 py-10 text-white">
          <div className="grid gap-8 text-center md:grid-cols-3">
            <div>
              <p className="font-display text-4xl text-brand-sunrise">12,000+</p>
              <p className="mt-1 text-sm text-white/70">Applications sent this month</p>
            </div>
            <div>
              <p className="font-display text-4xl text-brand-lagoon">73%</p>
              <p className="mt-1 text-sm text-white/70">Average interview rate</p>
            </div>
            <div>
              <p className="font-display text-4xl text-brand-mango">2.3 weeks</p>
              <p className="mt-1 text-sm text-white/70">Average time to first offer</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
