import React, { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "../ui/Button";
import { magicLinkService } from "../../services/magicLinkService";
import { ValidationUtils } from "../../lib/validation";
import { pushToast } from "../../lib/toast";
import { telemetry } from "../../lib/telemetry";
import { cn } from "../../lib/utils";

type ConversionCTAVariant =
  | "switch"
  | "compare"
  | "default"
  | "topic"
  | "guide"
  | "location"
  | "blog";

interface ConversionCTAProperties {
  competitorName?: string;
  variant?: ConversionCTAVariant;
  topicName?: string;
  locationName?: string;
  guideName?: string;
}

const FEATURE_BULLETS = [
  "AI tailors every resume & cover letter",
  "Auto-applies to hundreds of jobs daily",
  "Set up in 2 minutes — no experience needed",
];

export function ConversionCTA({
  competitorName,
  variant = "default",
  topicName,
  locationName,
  guideName,
}: ConversionCTAProperties) {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);

  const showEmailCapture = variant === "blog" || variant === "topic";

  const headlines: Record<ConversionCTAVariant, string> = {
    switch: `Ready to upgrade from ${competitorName || "your current tool"}?`,
    compare: `See why job hunters switch from ${competitorName || "other tools"} to JobHuntin`,
    default: "Get more interviews. Spend less time applying.",
    topic: `Ready to land more interviews${topicName ? ` with ${topicName}` : ""}?`,
    guide: `Put this into action${guideName ? `: ${guideName}` : ""}`,
    location: `Hunting in ${locationName || "your city"}? Let AI do the heavy lifting.`,
    blog: "Start your job hunt on autopilot.",
  };

  const subtitles: Record<ConversionCTAVariant, string> = {
    switch: `Join thousands who switched from ${competitorName || "other tools"}. Set up in about 2 minutes.`,
    compare: `Our AI tailors your resume and cover letter for each role, then applies for you.`,
    default: `Upload your resume once. We match you to roles, tailor each application, and apply — so you can focus on interviews.`,
    topic: `JobHuntin matches you to roles, tailors your applications, and applies. One setup, hundreds of applications.`,
    guide: `Upload your resume once. Our AI matches, tailors, and applies to jobs that fit.`,
    location: `We find roles in ${locationName || "your area"}, tailor your applications, and apply while you focus on interviews.`,
    blog: `Upload your resume once. JobHuntin matches, tailors, and applies to jobs that fit your profile.`,
  };

  const validateEmail = (e: string) =>
    ValidationUtils.validate.email(e.trim()).isValid;

  const handleEmailSubmit = async (e: React.FormEvent) => {
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
      const result = await magicLinkService.sendMagicLink(
        email,
        "/app/onboarding",
      );
      if (!result.success)
        throw new Error(result.error || "Could not send magic link");
      telemetry.track("login_magic_link_requested", {
        source: "conversion_cta",
        variant,
      });
      pushToast({
        title: "Check your inbox",
        description: "Magic link sent!",
        tone: "success",
      });
      setSentEmail(result.email);
      setEmail("");
    } catch (error: unknown) {
      const message =
        typeof (error as Error)?.message === "string" &&
        !(error as Error).message.includes("[object")
          ? (error as Error).message
          : "We couldn't send the magic link. Please try again.";
      setEmailError(message);
      pushToast({
        title: "Could not send magic link",
        description: message,
        tone: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section
      className="mt-20"
      aria-labelledby="conversion-cta-heading"
      aria-describedby="conversion-cta-description"
    >
      <div
        className="relative overflow-hidden rounded-2xl p-12 md:p-16 text-white text-center shadow-2xl"
        style={{
          background:
            "linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)",
          boxShadow:
            "0 32px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)",
        }}
      >
        {/* CSS gradient pattern instead of external texture */}
        <div
          className="absolute inset-0 opacity-[0.07] pointer-events-none"
          style={{
            backgroundImage: `linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                                          linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                                          linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.1) 75%),
                                          linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.1) 75%)`,
            backgroundSize: "24px 24px",
            backgroundPosition: "0 0, 0 12px, 12px -12px, -12px 0px",
            backgroundColor: "transparent",
          }}
        />
        <div
          className="absolute top-0 right-0 w-96 h-96 rounded-full blur-[100px] -mr-48 -mt-48 pointer-events-none"
          style={{ background: "rgba(69,93,211,0.2)" }}
        />
        <div
          className="absolute bottom-0 left-0 w-64 h-64 rounded-full blur-[80px] -ml-32 -mb-32 pointer-events-none"
          style={{ background: "rgba(59,130,246,0.1)" }}
        />

        <div className="relative z-10">
          {/* Trust signals */}
          <div
            className="flex flex-wrap items-center justify-center gap-4 md:gap-6 mb-6 text-sm text-white/70"
            role="list"
            aria-label="Trust signals"
          >
            <span className="flex items-center gap-1.5" role="listitem">
              No credit card required
            </span>
            <span className="flex items-center gap-1.5" role="listitem">
              Cancel anytime
            </span>
          </div>

          <h2
            id="conversion-cta-heading"
            className="text-3xl md:text-5xl font-bold mb-6 font-display leading-tight"
          >
            {headlines[variant]}
          </h2>

          <p
            id="conversion-cta-description"
            className="text-slate-400 mb-8 max-w-2xl mx-auto text-lg font-medium leading-relaxed"
          >
            {subtitles[variant]}
          </p>

          {/* Feature bullets */}
          <ul
            className="flex flex-wrap justify-center gap-4 md:gap-8 mb-10"
            role="list"
            aria-label="Key features"
          >
            {FEATURE_BULLETS.map((bullet, index) => (
              <li
                key={index}
                className="flex items-center gap-2 text-slate-300 text-sm md:text-base font-medium"
                role="listitem"
              >
                <Check
                  className="w-5 h-5 shrink-0 text-emerald-400"
                  aria-hidden
                />
                {bullet}
              </li>
            ))}
          </ul>

          {/* CTA area */}
          {showEmailCapture ? (
            sentEmail ? (
              <div
                className="flex items-center justify-center gap-4 p-5 rounded-xl max-w-md mx-auto"
                style={{
                  background: "rgba(16,185,129,0.15)",
                  border: "1px solid rgba(16,185,129,0.3)",
                }}
                role="status"
                aria-live="polite"
              >
                <Check
                  className="w-5 h-5 text-emerald-400 shrink-0"
                  aria-hidden
                />
                <div className="text-left min-w-0 flex-1">
                  <p className="text-sm font-medium text-white">
                    Check your inbox
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5 truncate">
                    {sentEmail}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSentEmail(null)}
                  className="text-xs font-medium text-emerald-400 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0F1729] rounded"
                  aria-label="Change email address"
                >
                  Change
                </button>
              </div>
            ) : (
              <div>
                <form
                  onSubmit={handleEmailSubmit}
                  className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
                  aria-label="Get started with your email"
                >
                  <input
                    type="email"
                    placeholder="you@example.com"
                    aria-label="Email address"
                    aria-invalid={!!emailError}
                    aria-describedby={emailError ? "email-error" : undefined}
                    className={cn(
                      "flex-1 h-12 px-4 rounded-xl text-base transition-all outline-none",
                      "bg-white/10 border border-white/20 text-white placeholder:text-white/40",
                      "focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/20",
                      emailError && "border-red-400",
                    )}
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailError) setEmailError("");
                    }}
                    disabled={isSubmitting}
                  />
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="h-12 px-8 rounded-xl text-base font-bold bg-[#455DD3] hover:bg-[#3A4FB8] text-white border-none shadow-lg shadow-[#455DD3]/30 disabled:opacity-50"
                    aria-label="Get started free"
                  >
                    {isSubmitting ? "Sending…" : "Get Started"}
                    {!isSubmitting && (
                      <ArrowRight className="w-4 h-4 ml-2" aria-hidden />
                    )}
                  </Button>
                </form>
                {emailError && (
                  <p
                    id="email-error"
                    className="mt-2 text-xs text-red-400 text-center"
                    role="alert"
                  >
                    {emailError}
                  </p>
                )}
              </div>
            )
          ) : (
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                asChild
                className="bg-[#455DD3] hover:bg-[#3A4FB8] text-white px-8 py-5 h-auto rounded-xl font-semibold text-lg shadow-lg border-none"
              >
                <Link to="/login" aria-label="Start hunting for jobs">
                  Get Started
                  <ArrowRight className="w-4 h-4 ml-2" aria-hidden />
                </Link>
              </Button>

              <Button
                asChild
                className="bg-white/10 hover:bg-white/20 text-white px-6 py-5 h-auto rounded-xl font-semibold text-base border border-white/20"
              >
                <Link to="/pricing" aria-label="View pricing plans">
                  View Pricing
                </Link>
              </Button>
            </div>
          )}

          <p className="mt-8 text-slate-500 text-sm font-medium">
            Upload your resume once. We handle the rest.
          </p>
        </div>
      </div>
    </section>
  );
}
