import React, { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Quote } from 'lucide-react';
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
  accent: string; // color block for card
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
    accent: "#FFB8A0",
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
    accent: "#C2DCC8",
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
    accent: "#D3E5EF",
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
    accent: "#FADEC9",
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
    accent: "#E8D5F2",
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

      {/* Hero — matches homepage, playful */}
      <section className="relative overflow-hidden" style={{ background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)' }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(69,93,211,0.15) 0%, transparent 60%)' }} />
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-60" preserveAspectRatio="none" viewBox="0 0 1440 400" aria-hidden="true">
          <path d="M-100 200 C200 120, 500 280, 800 200 S1200 100, 1540 180" stroke="#455DD3" strokeOpacity="0.15" strokeWidth="2" fill="none" />
          <path d="M-100 250 C300 170, 600 330, 900 250 S1300 150, 1540 230" stroke="#7B93DB" strokeOpacity="0.1" strokeWidth="1.5" fill="none" />
        </svg>
        <div className="absolute top-[15%] right-[10%] w-4 h-4 rounded-full bg-[#7DD3CF]/30 animate-pulse" style={{ animationDuration: '2.5s' }} />
        <div className="absolute bottom-[25%] left-[8%] w-3 h-3 rounded-full bg-[#455DD3]/40 animate-pulse" style={{ animationDuration: '3s', animationDelay: '0.5s' }} />
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

      {/* Case studies — bento-style, fun color blocks, playful layout */}
      <section className="py-[64px] sm:py-[80px] bg-[#F7F6F3]">
        <div className="max-w-[1080px] mx-auto px-6">
          <Reveal>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-[#455DD3]" />
              <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider">Success stories</p>
            </div>
            <h2 className="text-[clamp(2rem,4vw,40px)] font-bold text-[#2D2A26] mb-12" style={{ letterSpacing: '-1px' }}>
              Real outcomes from real users
            </h2>
          </Reveal>

          <div className="space-y-6 sm:space-y-8">
            {STORIES.map((story, i) => (
              <Reveal key={story.name} delay={i * 80}>
                <article className="rounded-2xl overflow-hidden bg-white border border-[#E9E9E7] shadow-sm hover:border-[#E3E2E0] hover:shadow-lg transition-all duration-300">
                  <div className="flex flex-col md:flex-row">
                    {/* Left: color block + person + outcome */}
                    <div className="md:w-[42%] p-6 sm:p-8 md:p-8 flex flex-col gap-4" style={{ background: `${story.accent}40` }}>
                      <div className="flex items-start gap-4">
                        <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center text-white text-lg font-bold shrink-0 shadow-lg" style={{ background: `linear-gradient(135deg, ${story.accent}, ${story.accent}cc)` }}>
                          {story.initials}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-[12px] font-medium text-[#9B9A97] uppercase tracking-wider mb-0.5">{story.role} · {story.company}</p>
                          <h3 className="text-xl sm:text-2xl font-bold text-[#2D2A26] mb-2">{story.name}</h3>
                          <span className="inline-block px-4 py-1.5 rounded-xl text-[14px] font-bold text-white shadow-sm" style={{ background: story.accent }}>
                            {story.outcome}
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-x-6 gap-y-1">
                        {story.outcomes.map((o) => (
                          <div key={o.label} className="text-[13px]">
                            <span className="text-[#9B9A97]">{o.label}: </span>
                            <span className="font-bold text-[#2D2A26]">{o.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Right: before → after + quote */}
                    <div className="md:w-[58%] p-6 sm:p-8 md:p-8 flex flex-col justify-center border-t md:border-t-0 md:border-l border-[#E9E9E7]">
                      <div className="flex flex-wrap items-center gap-2 mb-4 text-[14px]">
                        <span className="text-[#9B9A97] line-through">{story.before}</span>
                        <span className="text-[#455DD3] font-bold">→</span>
                        <span className="font-bold text-[#2D2A26]">{story.after}</span>
                      </div>
                      <div className="relative">
                        <Quote className="absolute -top-1 -left-1 w-7 h-7 text-[#E9E9E7]" aria-hidden />
                        <blockquote className="text-[16px] sm:text-[18px] text-[#2D2A26] font-medium leading-relaxed pl-6">
                          &ldquo;{story.quote}&rdquo;
                        </blockquote>
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
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40" preserveAspectRatio="none" viewBox="0 0 1440 400" aria-hidden="true">
          <path d="M-80 350 C300 250, 600 450, 900 300 S1200 180, 1520 280" stroke="#7DD3CF" strokeOpacity="0.08" strokeWidth="1.5" fill="none" />
        </svg>
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
                "inline-flex items-center gap-2 h-[48px] px-[28px] rounded-xl text-[16px] font-semibold",
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
