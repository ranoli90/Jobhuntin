import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Bot, Search, FileText, Send, CheckCircle, Sparkles, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { SEO } from '../components/marketing/SEO';

// --- Simulation Components ---

const SimulationLog = () => {
    const [logs, setLogs] = useState<string[]>([
        "Initializing JobHuntin Engine v2.4...",
        "Scanning LinkedIn for 'Senior React Engineer'...",
        "Found matching job at Vercel (Score: 94%)",
        "Tailoring cover letter based on summary..."
    ]);

    useEffect(() => {
        const timer = setInterval(() => {
            const newLogs = [
                "Analyzing req: 'Must have Framer Motion exp'...",
                "Updating resume skillset: +Advanced Animation",
                "Submitting application to Stripe...",
                "Success! ID: app_492013",
                "Next scan in 3.4s..."
            ];
            setLogs(prev => [...prev.slice(-4), newLogs[Math.floor(Math.random() * newLogs.length)]]);
        }, 2500);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="font-mono text-[10px] md:text-sm text-primary-400 p-6 bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl">
            {logs.map((log, i) => (
                <motion.div
                    key={i + log}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="mb-1 flex gap-2"
                >
                    <span className="text-primary-600/50">[{new Date().toLocaleTimeString()}]</span>
                    <span>{log}</span>
                </motion.div>
            ))}
            <motion.div
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="w-2 h-4 bg-primary-500 inline-block align-middle ml-1"
            />
        </div>
    );
};

const ProcessStep = ({ icon: Icon, title, desc, delay }: { icon: any, title: string, desc: string, delay: number }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.8 }}
        viewport={{ once: true }}
        className="relative group"
    >
        <div className="absolute -inset-4 bg-primary-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity blur-xl" />
        <div className="relative z-10 flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-2xl bg-white shadow-xl shadow-slate-200/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
                <Icon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-black text-slate-900 mb-2">{title}</h3>
            <p className="text-slate-500 leading-relaxed font-medium">{desc}</p>
        </div>
    </motion.div>
);

export default function About() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"]
    });

    const heroScale = useTransform(scrollYProgress, [0, 0.1], [1, 0.85]);
    const heroOpacity = useTransform(scrollYProgress, [0, 0.1], [1, 0]);

    return (
        <div className="bg-white dark:bg-slate-950 overflow-x-hidden">
            <SEO
                title="About JobHuntin | AI Job Search Automation That Works While You Sleep"
                description="JobHuntin is an AI-powered job search automation platform. Our autonomous agent discovers jobs, tailors resumes, and auto-applies 24/7. Built by job seekers, for job seekers."
                ogTitle="About JobHuntin | AI Job Search Automation"
                ogImage="https://jobhuntin.com/og/about.png"
                canonicalUrl="https://jobhuntin.com/about"
                includeDate={true}
                schema={[
                    {
                        "@context": "https://schema.org",
                        "@type": "AboutPage",
                        "name": "About JobHuntin",
                        "description": "AI-powered job search automation platform",
                        "url": "https://jobhuntin.com/about",
                        "mainEntity": {
                            "@type": "Organization",
                            "name": "JobHuntin",
                            "url": "https://jobhuntin.com",
                            "description": "Autonomous AI job search automation"
                        }
                    },
                    {
                        "@context": "https://schema.org",
                        "@type": "Organization",
                        "name": "JobHuntin",
                        "url": "https://jobhuntin.com",
                        "logo": "https://jobhuntin.com/favicon.svg",
                        "description": "AI-powered job search automation platform",
                        "foundingDate": "2025",
                        "contactPoint": {
                            "@type": "ContactPoint",
                            "email": "support@jobhuntin.com",
                            "contactType": "customer service"
                        }
                    }
                ]}
            />
            {/* --- HERO SECTION --- */}
            <section className="relative min-h-[90vh] flex items-center justify-center pt-24 px-6">
                <div className="absolute inset-0 z-0">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-[120px] animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] animate-pulse delay-1000" />
                </div>

                <motion.div
                    style={{ scale: heroScale, opacity: heroOpacity }}
                    className="max-w-5xl mx-auto text-center relative z-10"
                >
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 bg-slate-900/5 backdrop-blur-sm border border-slate-900/10 px-4 py-2 rounded-full text-sm font-bold text-slate-800 mb-8"
                    >
                        <Sparkles className="w-4 h-4 text-primary-600" />
                        <span>12,000+ job seekers stopped scrolling</span>
                    </motion.div>

                    <h1 className="text-6xl md:text-8xl font-black text-slate-900 dark:text-slate-100 leading-[0.9] tracking-tighter mb-8">
                        The end of the <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-primary-600">infinite scroll.</span>
                    </h1>

                    <p className="text-xl md:text-2xl text-slate-500 dark:text-slate-400 max-w-3xl mx-auto font-medium leading-relaxed mb-12">
                        We built JobHuntin because finding a job shouldn't be a full-time job.
                        So we moved the hard part to an engine that never sleeps.
                    </p>

                    <div className="flex flex-wrap justify-center gap-4">
                        <Link to="/login">
                            <Button variant="primary" size="lg" className="rounded-2xl px-8 py-6 text-lg font-bold shadow-2xl shadow-primary-500/20">
                                Experience the magic
                            </Button>
                        </Link>
                        <Button variant="ghost" size="lg" className="rounded-2xl px-8 py-6 text-lg font-bold">
                            Watch the story
                        </Button>
                    </div>
                </motion.div>
            </section>

            {/* --- SUPERIOR TECHNOLOGY SECTION --- */}
            <section className="py-32 px-6 relative">
                <div className="max-w-7xl mx-auto">
                    <div className="grid lg:grid-cols-2 gap-20 items-center">
                        <div className="space-y-8">
                            <div className="space-y-4">
                                <p className="text-primary-600 font-black tracking-widest uppercase text-sm">Enterprise-Grade Intelligence</p>
                                <h2 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-slate-100 leading-tight">
                                    A digital double that <br /> hunts for you.
                                </h2>
                                <p className="text-lg text-slate-500 font-medium leading-relaxed">
                                    Our system doesn't just "find" jobs. It analyzes your unique skills, matches them against real market demand,
                                    and handles the entire application lifecycle — from the initial find to the final submit.
                                </p>
                            </div>

                            <div className="space-y-6">
                                <div className="flex gap-4 p-6 rounded-3xl bg-slate-50 border border-slate-100 transition-transform hover:-translate-y-1">
                                    <div className="flex-shrink-0 w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center">
                                        <ShieldCheck className="w-6 h-6 text-green-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-slate-900">Privacy First</h4>
                                        <p className="text-sm text-slate-500 font-medium">Encrypted, never sold. Recruiters only see what you approve.</p>
                                    </div>
                                </div>
                                <div className="flex gap-4 p-6 rounded-3xl bg-slate-50 border border-slate-100 transition-transform hover:-translate-y-1">
                                    <div className="flex-shrink-0 w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center">
                                        <Zap className="w-6 h-6 text-primary-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-slate-900">Lightning Precision</h4>
                                        <p className="text-sm text-slate-500 font-medium">Thousands of jobs parsed per minute. Your match scores update in milliseconds.</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="relative">
                            <div className="absolute -inset-4 bg-gradient-to-tr from-primary-500 to-blue-500 rounded-[3rem] blur-2xl opacity-10 animate-pulse" />
                            <div className="relative bg-white rounded-[2.5rem] border border-slate-100 shadow-2xl overflow-hidden p-8 aspect-square flex flex-col justify-center gap-8">
                                <SimulationLog />
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-primary-50 rounded-2xl border border-primary-100 text-center">
                                        <p className="text-[10px] uppercase font-black text-primary-600 mb-1">Success Rate</p>
                                        <p className="text-3xl font-black text-primary-700">92%</p>
                                    </div>
                                    <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 text-center">
                                        <p className="text-[10px] uppercase font-black text-blue-600 mb-1">Time Saved</p>
                                        <p className="text-3xl font-black text-blue-700">40h+</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* --- THE PROCESS --- */}
            <section className="py-32 bg-slate-50/50 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-24 max-w-3xl mx-auto">
                        <h2 className="text-4xl md:text-5xl font-black text-slate-900 mb-6 tracking-tight">How the engine works.</h2>
                        <p className="text-lg text-slate-500 font-medium leading-relaxed">
                            Four steps. Zero effort from you. Applications that actually get responses.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-4 gap-12">
                        <ProcessStep
                            icon={Bot}
                            title="Parse"
                            desc="We build your digital twin from your resume and LinkedIn."
                            delay={0.1}
                        />
                        <ProcessStep
                            icon={Search}
                            title="Scout"
                            desc="AI agents scan the web for jobs that match your DNA."
                            delay={0.2}
                        />
                        <ProcessStep
                            icon={FileText}
                            title="Tailor"
                            desc="Resumes and cover letters are rewritten for every single job."
                            delay={0.3}
                        />
                        <ProcessStep
                            icon={Send}
                            title="Apply"
                            desc="Submissions happen automatically. You just track notifications."
                            delay={0.4}
                        />
                    </div>
                </div>
            </section>

            {/* --- THE VISION --- */}
            <section className="py-40 px-6 relative overflow-hidden">
                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <h2 className="text-5xl md:text-7xl font-black text-slate-900 mb-8 leading-tight tracking-tight">
                        Every day you wait,<br />
                        someone else gets hired.
                    </h2>
                    <p className="text-xl text-slate-500 mb-12 font-medium">
                        Your time should be spent in interviews, not on job boards. The people who start today land roles 3x faster.
                    </p>
                    <Link to="/login">
                        <Button size="lg" className="rounded-2xl px-12 py-8 text-xl font-bold bg-slate-900 text-white hover:bg-black hover:shadow-2xl transition-all group">
                            Get Started for Free
                            <ArrowRight className="ml-3 group-hover:translate-x-1 transition-transform" />
                        </Button>
                    </Link>
                    <p className="mt-8 text-slate-400 font-medium text-sm">No credit card required. Cancel anytime. Actually works.</p>
                </div>

                {/* Floating Background Sparkles */}
                <div className="absolute top-1/2 left-0 w-full h-full pointer-events-none">
                    <motion.div
                        animate={{ y: [0, -20, 0], opacity: [0.3, 0.6, 0.3] }}
                        transition={{ repeat: Infinity, duration: 5 }}
                        className="absolute top-0 left-10 w-2 h-2 bg-primary-500 rounded-full"
                    />
                    <motion.div
                        animate={{ y: [0, 30, 0], opacity: [0.2, 0.5, 0.2] }}
                        transition={{ repeat: Infinity, duration: 7, delay: 1 }}
                        className="absolute bottom-10 right-20 w-3 h-3 bg-blue-500 rounded-full"
                    />
                </div>
            </section>


        </div>
    );
}
