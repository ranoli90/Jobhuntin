import React, { useState, useEffect } from 'react';
import { magicLinkService } from '../services/magicLinkService';
import { ArrowRight, MailCheck, Check } from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

const STATS = [
  { value: "3.4×", label: "More interviews" },
  { value: "12min", label: "Avg. time to first apply" },
  { value: "89%", label: "Response rate increase" },
];

const LOGOS = [
  "Deloitte", "Stripe", "Salesforce", "HubSpot", "Shopify", "Notion",
];

const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);

  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) {
      setEmailError("Enter a valid email");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);

    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/dashboard");
      if (!result.success) throw new Error(result.error || "Failed");
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setEmailError(err?.message || "Failed to send");
      pushToast({ title: "Error", description: err?.message || "Failed", tone: "error" });
    }
  };

  return (
    <section className="relative min-h-[90vh] flex items-center bg-stone-950">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(120,113,108,0.15)_0%,_transparent_60%)]" />

      <div className="relative z-10 w-full max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 py-24 sm:py-32">
        <div className="max-w-3xl">
          <p className="text-sm font-medium tracking-widest uppercase text-stone-500 mb-6">
            Autonomous job search
          </p>

          <h1 className="font-display text-5xl sm:text-6xl md:text-7xl lg:text-[5.5rem] leading-[1.05] tracking-tight text-stone-100 mb-8">
            Stop applying.<br />
            <span className="text-stone-400 italic">Start interviewing.</span>
          </h1>

          <p className="text-lg sm:text-xl text-stone-400 max-w-xl mb-12 leading-relaxed">
            Upload your resume. Our agent tailors every application, writes every cover letter, and applies to hundreds of jobs daily — while you sleep.
          </p>

          {!sentEmail ? (
            <div className="max-w-md">
              <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3">
                <input
                  type="email"
                  placeholder="you@email.com"
                  className={cn(
                    "flex-1 px-5 py-4 rounded-lg bg-stone-900 border border-stone-800 text-stone-100 placeholder:text-stone-600",
                    "focus:outline-none focus:border-stone-600 transition-colors",
                    emailError && "border-red-800 text-red-400"
                  )}
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError("");
                  }}
                />
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-4 rounded-lg font-medium text-stone-950 bg-stone-100 hover:bg-white transition-colors disabled:opacity-50 flex items-center gap-2 whitespace-nowrap"
                >
                  {isSubmitting ? "Sending..." : "Get started"}
                  {!isSubmitting && <ArrowRight className="w-4 h-4" />}
                </button>
              </form>

              {emailError && (
                <p className="mt-3 text-sm text-red-400">{emailError}</p>
              )}

              <p className="mt-4 text-xs text-stone-600">
                Free to start · No credit card · 2-minute setup
              </p>
            </div>
          ) : (
            <div className="max-w-md p-6 rounded-lg border border-stone-800 bg-stone-900/50">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-stone-800 flex items-center justify-center">
                  <MailCheck className="w-5 h-5 text-stone-300" />
                </div>
                <div>
                  <p className="font-medium text-stone-200">Check your inbox</p>
                  <p className="text-sm text-stone-500">{sentEmail}</p>
                </div>
              </div>
              <button
                onClick={() => setSentEmail(null)}
                className="text-sm text-stone-500 hover:text-stone-300 transition-colors"
              >
                Use a different email →
              </button>
            </div>
          )}
        </div>

        {/* Stats row */}
        <div className="mt-20 pt-12 border-t border-stone-800/60">
          <div className="grid grid-cols-3 gap-4 sm:gap-8 max-w-lg">
            {STATS.map((stat) => (
              <div key={stat.label}>
                <p className="font-display text-3xl sm:text-4xl text-stone-100 italic">{stat.value}</p>
                <p className="text-sm text-stone-500 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

const LogoBar = () => (
  <section className="py-16 bg-stone-950 border-t border-stone-900">
    <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12">
      <p className="text-xs font-medium tracking-widest uppercase text-stone-600 mb-8">
        Our users land roles at
      </p>
      <div className="flex flex-wrap gap-x-12 gap-y-4">
        {LOGOS.map((name) => (
          <span key={name} className="text-lg font-medium text-stone-700">{name}</span>
        ))}
      </div>
    </div>
  </section>
);

const HowItWorks = () => {
  const steps = [
    {
      num: "01",
      title: "Upload your resume",
      desc: "Drop your PDF. Our system extracts your skills, experience, and career goals in seconds.",
    },
    {
      num: "02",
      title: "Set your preferences",
      desc: "Tell us what you want — roles, locations, salary range, company size. We filter thousands of listings.",
    },
    {
      num: "03",
      title: "We apply for you",
      desc: "Every application is tailored. Custom resumes, personalized cover letters, strategic timing.",
    },
    {
      num: "04",
      title: "You interview",
      desc: "Wake up to interview requests. We handle the grind so you can focus on the conversations that matter.",
    },
  ];

  return (
    <section className="py-24 sm:py-32 bg-stone-50">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="max-w-2xl mb-16">
          <p className="text-sm font-medium tracking-widest uppercase text-stone-400 mb-4">How it works</p>
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight text-stone-900 leading-[1.1]">
            Four steps to<br /><span className="italic text-stone-500">effortless</span> job search
          </h2>
        </div>

        <div className="grid sm:grid-cols-2 gap-x-16 gap-y-12">
          {steps.map((step) => (
            <div key={step.num} className="group">
              <span className="text-sm font-mono text-stone-300 block mb-3">{step.num}</span>
              <h3 className="text-xl font-semibold text-stone-900 mb-2">{step.title}</h3>
              <p className="text-stone-500 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const ValueProps = () => {
  const props = [
    {
      title: "Every application, tailored",
      desc: "No spray-and-pray. Each resume and cover letter is customized to the specific role, company, and job description.",
    },
    {
      title: "Runs 24/7",
      desc: "New listings appear at all hours. Our agent monitors job boards around the clock and applies the moment a match appears.",
    },
    {
      title: "Your data stays yours",
      desc: "Encrypted at rest, never sold to third parties. Delete everything with one click. We're GDPR and SOC 2 compliant.",
    },
  ];

  return (
    <section className="py-24 sm:py-32 bg-stone-950">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="max-w-2xl mb-16">
          <p className="text-sm font-medium tracking-widest uppercase text-stone-500 mb-4">Why JobHuntin</p>
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight text-stone-100 leading-[1.1]">
            Built for people who<br /><span className="italic text-stone-500">value their time</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {props.map((prop) => (
            <div key={prop.title} className="p-8 rounded-xl border border-stone-800 bg-stone-900/30">
              <h3 className="text-lg font-semibold text-stone-200 mb-3">{prop.title}</h3>
              <p className="text-stone-500 leading-relaxed">{prop.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const SocialProof = () => {
  const testimonials = [
    {
      quote: "I got 4 interviews in my first week. I'd been applying manually for 3 months with zero callbacks.",
      name: "Sarah K.",
      role: "Marketing Manager",
    },
    {
      quote: "The cover letters it writes are better than anything I could do myself. Genuinely impressed.",
      name: "Marcus T.",
      role: "Software Engineer",
    },
    {
      quote: "Landed my dream role at a Series B startup. JobHuntin found the listing 20 minutes after it was posted.",
      name: "Priya R.",
      role: "Product Designer",
    },
  ];

  return (
    <section className="py-24 sm:py-32 bg-stone-50">
      <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="max-w-2xl mb-16">
          <p className="text-sm font-medium tracking-widest uppercase text-stone-400 mb-4">Testimonials</p>
          <h2 className="font-display text-4xl sm:text-5xl tracking-tight text-stone-900 leading-[1.1]">
            Real results from<br /><span className="italic text-stone-500">real people</span>
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((t) => (
            <div key={t.name} className="p-8 rounded-xl bg-white border border-stone-200">
              <p className="text-stone-700 leading-relaxed mb-6">"{t.quote}"</p>
              <div>
                <p className="font-medium text-stone-900">{t.name}</p>
                <p className="text-sm text-stone-400">{t.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const FinalCTA = () => (
  <section className="py-24 sm:py-32 bg-stone-950">
    <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
      <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl tracking-tight text-stone-100 leading-[1.1] mb-6">
        Ready to stop<br /><span className="italic text-stone-400">grinding?</span>
      </h2>
      <p className="text-lg text-stone-500 max-w-xl mx-auto mb-10">
        Join thousands of professionals who let JobHuntin handle the applications while they focus on what matters.
      </p>
      <a
        href="#"
        onClick={(e: React.MouseEvent) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
        className="inline-flex items-center gap-2 px-8 py-4 rounded-lg font-medium text-stone-950 bg-stone-100 hover:bg-white transition-colors"
      >
        Get started free <ArrowRight className="w-4 h-4" />
      </a>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-stone-600">
        <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5" /> Free tier available</span>
        <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5" /> No credit card</span>
        <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5" /> Cancel anytime</span>
      </div>
    </div>
  </section>
);

const StickyMobileCTA = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsVisible(window.scrollY > 500);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-stone-950 border-t border-stone-800 p-4">
      <button
        className="w-full rounded-lg py-3.5 font-medium text-stone-950 bg-stone-100 hover:bg-white transition-colors flex items-center justify-center gap-2"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      >
        Get started free <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};

export default function Homepage() {
  return (
    <>
      <SEO
        title="JobHuntin — Autonomous Job Applications While You Sleep"
        description="Upload your resume once. Our AI agent tailors and applies to hundreds of jobs daily. Land 3.4× more interviews with zero effort."
        ogTitle="JobHuntin — Autonomous Job Applications While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            { "@type": "Question", "name": "Is this legit? Will I get banned from job sites?", "acceptedAnswer": { "@type": "Answer", "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications." } },
            { "@type": "Question", "name": "How is this different from just applying myself?", "acceptedAnswer": { "@type": "Answer", "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter." } },
            { "@type": "Question", "name": "What happens to my resume and data?", "acceptedAnswer": { "@type": "Answer", "text": "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime." } }
          ]
        }}
      />
      <Hero />
      <LogoBar />
      <HowItWorks />
      <ValueProps />
      <SocialProof />
      <FinalCTA />
      <StickyMobileCTA />
    </>
  );
}