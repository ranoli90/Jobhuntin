import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Zap, ArrowRight, Check } from 'lucide-react';
import { Button } from '../ui/Button';
import { magicLinkService } from '../../services/magicLinkService';
import { ValidationUtils } from '../../lib/validation';
import { pushToast } from '../../lib/toast';
import { telemetry } from '../../lib/telemetry';
import { cn } from '../../lib/utils';

type ConversionCTAVariant = 'switch' | 'compare' | 'default' | 'topic' | 'guide' | 'location' | 'blog';

interface ConversionCTAProps {
    competitorName?: string;
    variant?: ConversionCTAVariant;
    topicName?: string;
    locationName?: string;
    guideName?: string;
}

const FEATURE_BULLETS = [
    'AI tailors every resume & cover letter',
    'Auto-applies to hundreds of jobs daily',
    'Set up in 2 minutes — no experience needed',
];

export function ConversionCTA({
    competitorName,
    variant = 'default',
    topicName,
    locationName,
    guideName,
}: ConversionCTAProps) {
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [emailError, setEmailError] = useState('');
    const [sentEmail, setSentEmail] = useState<string | null>(null);

    const showEmailCapture = variant === 'blog' || variant === 'topic';

    const headlines: Record<ConversionCTAVariant, string> = {
        switch: `Ready to upgrade from ${competitorName || 'your current tool'}?`,
        compare: `See why job hunters switch from ${competitorName || 'other tools'} to JobHuntin`,
        default: 'Stop grinding. Start interviewing.',
        topic: `Ready to land more interviews${topicName ? ` with ${topicName}` : ''}?`,
        guide: `Put this into action${guideName ? `: ${guideName}` : ''}`,
        location: `Hunting in ${locationName || 'your city'}? Let AI do the heavy lifting.`,
        blog: 'Start your job hunt on autopilot — free.',
    };

    const subtitles: Record<ConversionCTAVariant, string> = {
        switch: `Join thousands who already switched from ${competitorName || 'other tools'} to JobHuntin's autonomous AI agent. Set it up in 2 minutes.`,
        compare: `Our AI agent tailors every resume, writes every cover letter, and applies autonomously — while you sleep.`,
        default: `Let our AI agent hunt for roles, tailor your resume, and auto-apply to hundreds of jobs daily.`,
        topic: `JobHuntin's AI applies to hundreds of roles for you — tailored resumes, cover letters, and one-click setup.`,
        guide: `Upload your resume once. Our AI matches, tailors, and applies to hundreds of jobs every day.`,
        location: `Our AI agent finds roles in ${locationName || 'your area'}, tailors your applications, and applies while you focus on interviews.`,
        blog: `Upload your resume once. JobHuntin matches, tailors, and auto-applies to hundreds of jobs — every single day.`,
    };

    const validateEmail = (e: string) => ValidationUtils.validate.email(e.trim()).isValid;

    const handleEmailSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSubmitting) return;
        if (!validateEmail(email)) {
            setEmailError('Enter a valid email');
            return;
        }
        setEmailError('');
        setIsSubmitting(true);
        setSentEmail(null);
        try {
            const result = await magicLinkService.sendMagicLink(email, '/app/onboarding');
            if (!result.success) throw new Error(result.error || 'Failed');
            telemetry.track('login_magic_link_requested', { source: 'conversion_cta', variant });
            pushToast({ title: 'Check your inbox', description: 'Magic link sent!', tone: 'success' });
            setSentEmail(result.email);
            setEmail('');
        } catch (err: unknown) {
            const msg =
                typeof (err as Error)?.message === 'string' && !(err as Error).message.includes('[object')
                    ? (err as Error).message
                    : 'Something went wrong.';
            setEmailError(msg);
            pushToast({ title: 'Error', description: msg, tone: 'error' });
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
                    background: 'linear-gradient(165deg, #0F1729 0%, #1A2744 50%, #0d1320 100%)',
                    boxShadow: '0 32px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.05)',
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
                        backgroundSize: '24px 24px',
                        backgroundPosition: '0 0, 0 12px, 12px -12px, -12px 0px',
                        backgroundColor: 'transparent',
                    }}
                />
                <div
                    className="absolute top-0 right-0 w-96 h-96 rounded-full blur-[100px] -mr-48 -mt-48 pointer-events-none"
                    style={{ background: 'rgba(69,93,211,0.2)' }}
                />
                <div
                    className="absolute bottom-0 left-0 w-64 h-64 rounded-full blur-[80px] -ml-32 -mb-32 pointer-events-none"
                    style={{ background: 'rgba(59,130,246,0.1)' }}
                />

                <div className="relative z-10">
                    {/* Trust signals */}
                    <div
                        className="flex flex-wrap items-center justify-center gap-6 md:gap-8 mb-6 text-sm text-white/70"
                        role="list"
                        aria-label="Trust signals"
                    >
                        <span className="flex items-center gap-1.5" role="listitem">
                            <span className="font-semibold text-white">10,000+</span>
                            job seekers trust us
                        </span>
                        <span className="flex items-center gap-1.5" role="listitem">
                            <span className="font-semibold text-amber-400">4.9★</span>
                            rating
                        </span>
                        <span className="flex items-center gap-1.5" role="listitem">
                            No credit card required
                        </span>
                    </div>

                    <div
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold mb-6 border"
                        style={{
                            background: 'rgba(69,93,211,0.2)',
                            color: 'rgba(167,139,250,1)',
                            borderColor: 'rgba(69,93,211,0.2)',
                        }}
                    >
                        <Zap className="w-4 h-4" aria-hidden />
                        Free to start
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
                        {FEATURE_BULLETS.map((bullet, i) => (
                            <li
                                key={i}
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
                                    background: 'rgba(16,185,129,0.15)',
                                    border: '1px solid rgba(16,185,129,0.3)',
                                }}
                                role="status"
                                aria-live="polite"
                            >
                                <Check className="w-5 h-5 text-emerald-400 shrink-0" aria-hidden />
                                <div className="text-left min-w-0 flex-1">
                                    <p className="text-sm font-medium text-white">Check your inbox</p>
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
                                        aria-describedby={emailError ? 'email-error' : undefined}
                                        className={cn(
                                            'flex-1 h-12 px-4 rounded-xl text-base transition-all outline-none',
                                            'bg-white/10 border border-white/20 text-white placeholder:text-white/40',
                                            'focus:border-[#455DD3] focus:ring-2 focus:ring-[#455DD3]/20',
                                            emailError && 'border-red-400'
                                        )}
                                        value={email}
                                        onChange={(e) => {
                                            setEmail(e.target.value);
                                            if (emailError) setEmailError('');
                                        }}
                                        disabled={isSubmitting}
                                    />
                                    <Button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="h-12 px-8 rounded-xl text-base font-bold bg-[#455DD3] hover:bg-[#3A4FB8] text-white border-none shadow-lg shadow-[#455DD3]/30 disabled:opacity-50"
                                        aria-label="Get started free"
                                    >
                                        {isSubmitting ? 'Sending…' : 'Get Started'}
                                        {!isSubmitting && <ArrowRight className="w-4 h-4 ml-2" aria-hidden />}
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
                                className="bg-[#455DD3] hover:bg-[#3A4FB8] text-white px-10 py-6 h-auto rounded-2xl font-bold text-xl shadow-xl border-none"
                                style={{ boxShadow: '0 10px 40px rgba(69,93,211,0.3)' }}
                            >
                                <Link
                                    to="/login"
                                    aria-label="Start hunting for jobs free"
                                >
                                    Start Hunting Free
                                    <ArrowRight className="w-5 h-5 ml-2" aria-hidden />
                                </Link>
                            </Button>

                            <Button
                                asChild
                                className="bg-white/10 hover:bg-white/20 text-white px-8 py-6 h-auto rounded-2xl font-bold text-lg border border-white/20"
                            >
                                <Link to="/pricing" aria-label="View pricing plans">
                                    View Pricing
                                </Link>
                            </Button>
                        </div>
                    )}

                    {/* Social proof + urgency */}
                    <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-6 text-sm">
                        <div className="flex items-center gap-3" aria-label="Recent signups">
                            <div className="flex -space-x-2" aria-hidden>
                                {[1, 2, 3, 4].map((i) => (
                                    <div
                                        key={i}
                                        className="w-8 h-8 rounded-full border-2 border-[#0F1729] bg-gradient-to-br from-slate-500 to-slate-600 flex items-center justify-center text-xs font-bold text-white"
                                    >
                                        {String.fromCharCode(64 + i)}
                                    </div>
                                ))}
                            </div>
                            <span className="text-slate-400 font-medium">
                                <span className="text-white font-semibold">+2,847</span> joined this
                                week
                            </span>
                        </div>
                        <span
                            className="text-slate-500 font-medium"
                            aria-label="Average time to first interview"
                        >
                            Average time to first interview: <span className="text-emerald-400 font-semibold">12 days</span>
                        </span>
                    </div>

                    <p className="mt-6 text-slate-500 text-sm font-medium">
                        Average user lands 3x more interviews within 14 days
                    </p>
                </div>
            </div>
        </section>
    );
}
