import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ArrowRight } from 'lucide-react';
import { Button } from '../ui/Button';

interface ConversionCTAProps {
    competitorName?: string;
    variant?: 'switch' | 'compare' | 'default';
}

export function ConversionCTA({ competitorName, variant = 'default' }: ConversionCTAProps) {
    const headlines: Record<string, string> = {
        switch: `Ready to upgrade from ${competitorName || 'your current tool'}?`,
        compare: `See why job hunters switch from ${competitorName || 'other tools'} to JobHuntin`,
        default: 'Stop grinding. Start interviewing.',
    };

    const subtitles: Record<string, string> = {
        switch: `Join thousands who already switched from ${competitorName || 'other tools'} to JobHuntin's autonomous AI agent. Set it up in 2 minutes.`,
        compare: `Our AI agent tailors every resume, writes every cover letter, and applies autonomously — while you sleep.`,
        default: `Let our AI agent hunt for roles, tailor your resume, and auto-apply to hundreds of jobs daily.`,
    };

    return (
        <section className="mt-20">
            <div className="bg-slate-900 rounded-[3rem] p-12 md:p-16 text-white text-center relative overflow-hidden shadow-2xl">
                {/* Decorative elements */}
                <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10" />
                <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/20 rounded-full blur-[100px] -mr-48 -mt-48" />
                <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[80px] -ml-32 -mb-32" />

                <div className="relative z-10">
                    <div className="inline-flex items-center gap-2 bg-primary-500/20 text-primary-300 px-4 py-1.5 rounded-full text-sm font-bold mb-6 border border-primary-500/20">
                        <Zap className="w-4 h-4" />
                        Free to start • No credit card required
                    </div>

                    <h2 className="text-3xl md:text-5xl font-bold mb-6 font-display leading-tight">
                        {headlines[variant]}
                    </h2>

                    <p className="text-slate-400 mb-10 max-w-2xl mx-auto text-lg font-medium leading-relaxed">
                        {subtitles[variant]}
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                        <Button
                            asChild
                            className="bg-primary-600 hover:bg-primary-700 text-white px-10 py-6 h-auto rounded-2xl font-bold text-xl shadow-xl shadow-primary-500/20 border-none"
                        >
                            <Link to="/login">
                                Start Hunting Free
                                <ArrowRight className="w-5 h-5 ml-2" />
                            </Link>
                        </Button>

                        <Button
                            asChild
                            className="bg-white/10 hover:bg-white/20 text-white px-8 py-6 h-auto rounded-2xl font-bold text-lg border border-white/10"
                        >
                            <Link to="/pricing">
                                View Pricing
                            </Link>
                        </Button>
                    </div>

                    <p className="mt-6 text-slate-500 text-sm font-medium">
                        Average user lands 3x more interviews within 14 days
                    </p>
                </div>
            </div>
        </section>
    );
}
