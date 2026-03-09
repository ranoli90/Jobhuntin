import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

interface Outcome {
  label: string;
  value: string;
}

interface Story {
  name: string;
  role: string;
  company: string;
  initials: string;
  outcome: string;
  before: string;
  after: string;
  quote: string;
  outcomes: Outcome[];
}

const STORIES: Story[] = [
  {
    name: "Sarah Jenkins",
    role: "Marketing Director",
    company: "TechFlow",
    initials: "SJ",
    outcome: "Hired in 14 days",
    before: "3 hrs/day applying",
    after: "5 interviews in week 1",
    quote: "JobHuntin did it while I slept.",
    outcomes: [{ label: "Time to offer", value: "14 days" }, { label: "Interviews", value: "5" }],
  },
  {
    name: "Michael Chen",
    role: "Warehouse Supervisor",
    company: "Costco",
    initials: "MC",
    outcome: "Better role in 2 weeks",
    before: "Long hours, no time to apply",
    after: "Applied while at work",
    quote: "Got a better position without changing my schedule.",
    outcomes: [{ label: "Applications sent", value: "47" }, { label: "Time to offer", value: "2 weeks" }],
  },
  {
    name: "Jessica Alvarez",
    role: "Sales Associate",
    company: "Target",
    initials: "JA",
    outcome: "$5K salary bump",
    before: "2% callback rate",
    after: "15% callback rate",
    quote: "Numbers game — JobHuntin maximized my volume without sacrificing quality.",
    outcomes: [{ label: "Callback rate", value: "15%" }, { label: "Salary change", value: "+$5K" }],
  },
  {
    name: "David Ross",
    role: "Customer Service Lead",
    company: "Amazon",
    initials: "DR",
    outcome: "Remote role landed",
    before: "Inbox empty",
    after: "Inbox full of 'Let's chat'",
    quote: "I didn't believe it at first. Game changer.",
    outcomes: [{ label: "Role type", value: "Remote" }, { label: "First callback", value: "3 days" }],
  },
  {
    name: "Emily Zhang",
    role: "Retail Manager",
    company: "Home Depot",
    initials: "EZ",
    outcome: "Promoted in under 1 month",
    before: "Manual applications",
    after: "Volume through the roof",
    quote: "Got promoted to manager in less than a month.",
    outcomes: [{ label: "Outcome", value: "Promotion" }, { label: "Time", value: "< 1 month" }],
  },
];

function Reveal({ children, className = "", delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [vis, setVis] = useState(false);
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  React.useEffect(() => {
    if (reduced) { setVis(true); return; }
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVis(true); obs.disconnect(); } }, { threshold: 0.1 });
    obs.observe(el); return () => obs.disconnect();
  }, [reduced]);
  return (
    <div ref={ref} className={cn(reduced ? "" : "transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]", vis ? "opacity-100 translate-y-0" : (reduced ? "" : "opacity-0 translate-y-5"), className)} style={{ transitionDelay: reduced ? '0ms' : `${delay}ms` }}>{children}</div>
  );
}

export default function SuccessStories() {
  return (
    <div className="min-h-screen bg-white text-[#2D2A26]">
      <SEO
        title="Success Stories | Real Outcomes from JobHuntin Users"
        description="JobHuntin users share their outcomes: hired in 14 days, salary bumps, remote roles, and promotions. Real results, not reviews."
        ogTitle="Success Stories | JobHuntin"
        ogImage="https://jobhuntin.com/og/success-stories.png"
        canonicalUrl="https://jobhuntin.com/success-stories"
        includeDate={true}
        schema={STORIES.map(story => ({
          "@context": "https://schema.org",
          "@type": "Review",
          "author": { "@type": "Person", "name": story.name },
          "reviewBody": story.quote,
          "reviewRating": { "@type": "Rating", "ratingValue": "5", "bestRating": "5" },
          "itemReviewed": { "@type": "SoftwareApplication", "name": "JobHuntin", "applicationCategory": "CareerAutomation" },
        }))}
      />

      {/* Hero — matches Pricing/Homepage */}
      <section className="relative overflow-hidden" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.15) 0%, transparent 60%)' }} />
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-60" preserveAspectRatio="none" viewBox="0 0 1440 400" aria-hidden="true">
          <path d="M-100 200 C200 120, 500 280, 800 200 S1200 100, 1540 180" stroke="#455DD3" strokeOpacity="0.15" strokeWidth="2" fill="none" />
          <path d="M-100 250 C300 170, 600 330, 900 250 S1300 150, 1540 230" stroke="#7B93DB" strokeOpacity="0.1" strokeWidth="1.5" fill="none" />
        </svg>
        <div className="relative max-w-[1080px] mx-auto px-6 py-20 sm:py-28">
          <Reveal>
            <p className="text-[12px] font-medium text-[#7DD3CF] uppercase tracking-wider mb-[12px]">Real outcomes</p>
            <h1 className="text-[clamp(2.25rem,5vw,3.5rem)] font-bold text-white leading-tight mb-[16px]" style={{ letterSpacing: '-1.5px' }}>
              They got hired. <span className="text-[#7DD3CF]">You're next.</span>
            </h1>
            <p className="text-[16px] text-white/75 max-w-[480px] font-medium">
              Outcomes from real users — hired in 14 days, salary bumps, remote roles. Not reviews. Results.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Aggregate stats — scannable, meaningful */}
      <section className="bg-[#F7F6F3] py-12 border-b border-[#E9E9E7]">
        <div className="max-w-[1080px] mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
            {[
              { value: "500K+", label: "Applications sent" },
              { value: "14 days", label: "Avg. to first interview" },
              { value: "10K+", label: "Users hired" },
              { value: "18%", label: "Avg. callback rate" },
            ].map((s, i) => (
              <Reveal key={s.label} delay={i * 60}>
                <div className="text-center md:text-left">
                  <div className="text-2xl sm:text-3xl font-bold text-[#2D2A26]">{s.value}</div>
                  <div className="text-[13px] text-[#787774] font-medium mt-1">{s.label}</div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Case studies — outcome-first, matches homepage card style */}
      <section className="py-[64px] sm:py-[80px] bg-white">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-[8px]">Success stories</p>
            <h2 className="text-[clamp(2rem,4vw,40px)] font-bold text-[#2D2A26] mb-12" style={{ letterSpacing: '-1px' }}>
              Real outcomes from real users
            </h2>
          </Reveal>

          <div className="space-y-8 sm:space-y-12">
            {STORIES.map((story, i) => (
              <Reveal key={story.name} delay={i * 80}>
                <article className="rounded-[12px] overflow-hidden bg-[#F7F6F3] border border-[#E9E9E7] hover:border-[#E3E2E0] hover:-translate-y-[2px] transition-all duration-300">
                  <div className="p-6 sm:p-8 md:p-10">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                      {/* Left: person + outcome */}
                      <div className="flex gap-4 md:gap-6">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-[#2D2A26] flex items-center justify-center text-white text-sm font-bold shrink-0">
                          {story.initials}
                        </div>
                        <div>
                          <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-1">{story.role} · {story.company}</p>
                          <h3 className="text-lg sm:text-xl font-bold text-[#2D2A26] mb-2">{story.name}</h3>
                          <div className="inline-block px-3 py-1 rounded-lg bg-[#0D9488]/15 text-[#0D9488] text-[13px] font-semibold">
                            {story.outcome}
                          </div>
                        </div>
                      </div>

                      {/* Right: before → after + quote */}
                      <div className="md:max-w-[420px] md:ml-auto md:text-right">
                        <div className="flex flex-wrap items-center gap-2 mb-3 text-[13px] md:justify-end">
                          <span className="text-[#9B9A97]">{story.before}</span>
                          <span className="text-[#9B9A97]">→</span>
                          <span className="font-semibold text-[#2D2A26]">{story.after}</span>
                        </div>
                        <blockquote className="text-[15px] sm:text-[16px] text-[#2D2A26] font-medium leading-relaxed">
                          "{story.quote}"
                        </blockquote>
                        <div className="flex flex-wrap gap-4 mt-4 md:justify-end">
                          {story.outcomes.map((o) => (
                            <div key={o.label} className="text-[12px]">
                              <span className="text-[#9B9A97]">{o.label}: </span>
                              <span className="font-semibold text-[#2D2A26]">{o.value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA — homepage style */}
      <section className="bg-[#2D2A26] py-16 sm:py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 60% 40% at 50% 100%, rgba(23,190,187,0.1) 0%, transparent 70%)' }} />
        <div className="relative max-w-[1080px] mx-auto px-6 text-center">
          <Reveal>
            <h2 className="text-[clamp(1.75rem,4vw,36px)] font-bold text-white mb-4" style={{ letterSpacing: '-1px' }}>
              Your turn.
            </h2>
            <p className="text-[16px] text-[#9B9A97] max-w-[400px] mx-auto mb-8">
              20 free applications per week. No credit card. Start in two minutes.
            </p>
            <Link
              to="/login"
              className={cn(
                "inline-flex items-center gap-2 h-[44px] px-[24px] rounded-[10px] text-[16px] font-semibold",
                "bg-[#455DD3] text-white hover:bg-[#3A4FB8] transition-all duration-300",
                "shadow-lg shadow-[#455DD3]/30 hover:shadow-[#455DD3]/50 hover:scale-[1.02] active:scale-[0.98]",
                "focus-visible:ring-2 focus-visible:ring-[#455DD3] focus-visible:ring-offset-2 focus-visible:ring-offset-[#2D2A26] focus-visible:outline-none"
              )}
            >
              Get started free <ArrowRight className="w-4 h-4" />
            </Link>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
