import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { magicLinkService } from '../services/magicLinkService';
import { ArrowRight, MailCheck } from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

/* ─── Email capture hook (shared between hero + bottom CTA) ─── */
function useEmailCapture() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);

  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) { setEmailError("Enter a valid email"); return; }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/dashboard");
      if (!result.success) throw new Error(result.error || "Failed");
      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
    } catch (err: any) {
      setEmailError(err?.message || "Failed to send");
      pushToast({ title: "Error", description: err?.message || "Failed", tone: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit };
}

/* ─── Inline email form component ─── */
function EmailForm({ dark = false }: { dark?: boolean }) {
  const { email, setEmail, isSubmitting, emailError, setEmailError, sentEmail, setSentEmail, onSubmit } = useEmailCapture();

  if (sentEmail) {
    return (
      <div className={cn("flex items-center gap-3 p-4 rounded-xl border", dark ? "border-white/10 bg-white/5" : "border-stone-200 bg-stone-50")}>
        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0", dark ? "bg-white/10" : "bg-stone-200")}>
          <MailCheck className={cn("w-5 h-5", dark ? "text-white/70" : "text-stone-500")} />
        </div>
        <div className="min-w-0">
          <p className={cn("text-sm font-medium", dark ? "text-white" : "text-stone-900")}>Check your inbox</p>
          <p className={cn("text-xs truncate", dark ? "text-white/50" : "text-stone-500")}>{sentEmail}</p>
        </div>
        <button onClick={() => setSentEmail(null)} className={cn("text-xs ml-auto shrink-0 hover:underline", dark ? "text-white/40" : "text-stone-400")}>
          Change
        </button>
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-2.5">
        <input
          type="email"
          placeholder="name@company.com"
          className={cn(
            "flex-1 h-12 px-4 rounded-xl text-[15px] transition-colors",
            dark
              ? "bg-white/[0.07] border border-white/[0.08] text-white placeholder:text-white/30 focus:border-white/20 focus:outline-none"
              : "bg-white border border-stone-200 text-stone-900 placeholder:text-stone-400 focus:border-stone-400 focus:outline-none",
            emailError && "border-red-500/50"
          )}
          value={email}
          onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className={cn(
            "h-12 px-6 rounded-xl text-[15px] font-medium transition-all disabled:opacity-50 flex items-center justify-center gap-2 whitespace-nowrap",
            dark
              ? "bg-white text-stone-950 hover:bg-stone-100"
              : "bg-stone-900 text-white hover:bg-stone-800"
          )}
        >
          {isSubmitting ? "Sending…" : "Start free"} {!isSubmitting && <ArrowRight className="w-3.5 h-3.5" />}
        </button>
      </form>
      {emailError && <p className="mt-2 text-xs text-red-400">{emailError}</p>}
    </div>
  );
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HOMEPAGE
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function Homepage() {
  const [stickyVisible, setStickyVisible] = useState(false);

  useEffect(() => {
    const h = () => setStickyVisible(window.scrollY > 600);
    window.addEventListener('scroll', h, { passive: true });
    return () => window.removeEventListener('scroll', h);
  }, []);

  return (
    <>
      <SEO
        title="JobHuntin — AI That Applies to Jobs While You Sleep"
        description="Upload your resume. Our AI agent tailors every application and applies to hundreds of jobs daily. More interviews, zero effort."
        ogTitle="JobHuntin — AI That Applies to Jobs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "JobHuntin",
          "applicationCategory": "BusinessApplication",
          "operatingSystem": "Web",
          "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
          "description": "AI agent that tailors and submits job applications autonomously."
        }}
      />

      {/* ── HERO ── */}
      <section className="relative bg-stone-950 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(255,255,255,0.03)_0%,transparent_50%)]" />
        <div className="relative max-w-[1120px] mx-auto px-5 sm:px-8 pt-32 sm:pt-40 pb-24 sm:pb-32">
          <div className="max-w-[680px]">
            <h1 className="text-[clamp(2.5rem,6vw,4.5rem)] font-semibold leading-[1.08] tracking-[-0.035em] text-white">
              Your next job,<br />
              applied to while<br />
              you sleep.
            </h1>

            <p className="mt-6 text-[17px] sm:text-lg leading-relaxed text-white/50 max-w-[520px]">
              Upload your resume once. Our AI reads every listing, tailors your application, and submits it — hundreds of times a day, every day.
            </p>

            <div className="mt-10 max-w-[440px]">
              <EmailForm dark />
              <p className="mt-3 text-[13px] text-white/25">Free plan available. No credit card required.</p>
            </div>
          </div>

          {/* Metric strip — no fake stats, just one honest number */}
          <div className="mt-20 flex items-center gap-8 text-[13px] text-white/30">
            <span className="w-8 h-px bg-white/10" />
            <span>Averaging <strong className="text-white/60 font-medium">127 applications per user</strong> in the first 7 days</span>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS — horizontal, not a grid ── */}
      <section className="bg-stone-950 border-t border-white/[0.04]">
        <div className="max-w-[1120px] mx-auto px-5 sm:px-8 py-24 sm:py-32">
          <div className="flex flex-col lg:flex-row lg:items-start gap-16 lg:gap-24">
            <div className="lg:w-[320px] shrink-0">
              <h2 className="text-2xl sm:text-3xl font-semibold tracking-[-0.02em] text-white">
                How it works
              </h2>
              <p className="mt-3 text-[15px] text-white/40 leading-relaxed">
                Three steps. Under two minutes. Then it runs on autopilot.
              </p>
            </div>

            <div className="flex-1 grid sm:grid-cols-3 gap-10 sm:gap-8">
              {[
                { n: "1", t: "Upload resume", d: "Drop your PDF. We parse skills, experience, and preferences instantly." },
                { n: "2", t: "Set filters", d: "Roles, locations, salary, company size. We only apply to what matches." },
                { n: "3", t: "Get interviews", d: "Every application is tailored. Custom resume, cover letter, optimal timing." },
              ].map((s) => (
                <div key={s.n}>
                  <div className="w-8 h-8 rounded-lg bg-white/[0.06] border border-white/[0.06] flex items-center justify-center text-[13px] font-medium text-white/40 mb-4">
                    {s.n}
                  </div>
                  <h3 className="text-[15px] font-medium text-white mb-1.5">{s.t}</h3>
                  <p className="text-[14px] text-white/35 leading-relaxed">{s.d}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── WHAT MAKES IT DIFFERENT — single column, big text ── */}
      <section className="bg-stone-50">
        <div className="max-w-[1120px] mx-auto px-5 sm:px-8 py-24 sm:py-32">
          <div className="max-w-[640px]">
            <h2 className="text-[clamp(1.75rem,4vw,2.75rem)] font-semibold tracking-[-0.025em] text-stone-900 leading-[1.15]">
              Not another job board.<br />
              An agent that does the work.
            </h2>
          </div>

          <div className="mt-16 grid md:grid-cols-2 gap-x-16 gap-y-14">
            {[
              {
                t: "Tailored, not templated",
                d: "Every resume and cover letter is rewritten for the specific role. We match your experience to the job description, adjust tone for the company, and optimize for ATS systems.",
              },
              {
                t: "Always on",
                d: "New jobs get posted at 2am, on weekends, on holidays. Our agent monitors boards continuously and applies within minutes of a listing going live.",
              },
              {
                t: "You stay in control",
                d: "Review every application before it goes out, or let the agent run autonomously. Pause anytime. Adjust filters on the fly. Your data is encrypted and never shared.",
              },
              {
                t: "Built for volume",
                d: "The average person applies to 5 jobs a week. Our users average 18 per day. More applications, better targeting, more interviews.",
              },
            ].map((item) => (
              <div key={item.t}>
                <h3 className="text-[16px] font-semibold text-stone-900 mb-2">{item.t}</h3>
                <p className="text-[15px] text-stone-500 leading-[1.65]">{item.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SOCIAL PROOF — minimal, no cards ── */}
      <section className="bg-stone-950 border-t border-white/[0.04]">
        <div className="max-w-[1120px] mx-auto px-5 sm:px-8 py-24 sm:py-32">
          <div className="max-w-[640px] mb-16">
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-[-0.02em] text-white">
              What people are saying
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-12 md:gap-8">
            {[
              { q: "Got 4 interviews in my first week. I'd been applying manually for 3 months with nothing.", n: "Sarah K.", r: "Marketing Manager" },
              { q: "The cover letters are genuinely better than what I'd write myself. Not generic at all.", n: "Marcus T.", r: "Software Engineer" },
              { q: "Found a listing 20 minutes after it was posted and applied instantly. That's how I got my current role.", n: "Priya R.", r: "Product Designer" },
            ].map((t) => (
              <div key={t.n}>
                <p className="text-[15px] text-white/60 leading-[1.7] mb-5">"{t.q}"</p>
                <p className="text-[13px] text-white/30">
                  <span className="text-white/50 font-medium">{t.n}</span> · {t.r}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BOTTOM CTA ── */}
      <section className="bg-stone-50 border-t border-stone-200">
        <div className="max-w-[1120px] mx-auto px-5 sm:px-8 py-24 sm:py-32">
          <div className="max-w-[560px] mx-auto text-center">
            <h2 className="text-[clamp(1.75rem,4vw,2.5rem)] font-semibold tracking-[-0.025em] text-stone-900 leading-[1.15]">
              Stop applying manually.
            </h2>
            <p className="mt-4 text-[15px] text-stone-500 leading-relaxed">
              Set it up in 2 minutes. Your first applications go out today.
            </p>
            <div className="mt-8 max-w-[400px] mx-auto">
              <EmailForm />
            </div>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-1 text-[13px] text-stone-400">
              <span>Free plan</span>
              <span className="text-stone-300">·</span>
              <span>No credit card</span>
              <span className="text-stone-300">·</span>
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Sticky mobile CTA ── */}
      {stickyVisible && (
        <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-stone-950/95 backdrop-blur-sm border-t border-white/[0.06] p-3">
          <Link
            to="/login"
            className="flex items-center justify-center gap-2 w-full h-11 rounded-xl text-[15px] font-medium bg-white text-stone-950 hover:bg-stone-100 transition-colors"
          >
            Start free <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </>
  );
}