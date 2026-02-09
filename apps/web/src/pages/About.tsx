import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Bot } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function About() {
    const containerRef = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"]
    });

    const opacity1 = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
    const opacity2 = useTransform(scrollYProgress, [0.15, 0.3, 0.45], [0, 1, 0]);
    const opacity3 = useTransform(scrollYProgress, [0.45, 0.6, 0.75], [0, 1, 0]);
    const opacity4 = useTransform(scrollYProgress, [0.75, 0.9], [0, 1]);

    const y1 = useTransform(scrollYProgress, [0, 0.15], [0, -50]);
    const y2 = useTransform(scrollYProgress, [0.15, 0.3], [50, 0]);
    const y3 = useTransform(scrollYProgress, [0.45, 0.6], [50, 0]);
    const y4 = useTransform(scrollYProgress, [0.75, 0.9], [50, 0]);

    return (
        <div ref={containerRef} className="bg-slate-50">
            {/* Sticky scroll container */}
            <div className="h-[400vh] relative">
                <div className="sticky top-0 h-screen overflow-hidden">
                    {/* Background gradient that shifts */}
                    <motion.div
                        className="absolute inset-0"
                        style={{
                            background: `radial-gradient(ellipse 80% 50% at 50% 50%, rgba(255, 107, 53, 0.08) 0%, transparent 60%)`
                        }}
                    />

                    {/* Scene 1: The Problem */}
                    <motion.div
                        className="absolute inset-0 flex items-center justify-center px-6"
                        style={{ opacity: opacity1, y: y1 }}
                    >
                        <div className="max-w-4xl text-center">
                            <motion.div
                                initial={{ scale: 0.9 }}
                                animate={{ scale: 1 }}
                                transition={{ duration: 0.8 }}
                            >
                                <p className="text-lg md:text-xl text-slate-500 mb-4 font-medium">You know the feeling.</p>
                                <h1 className="text-4xl md:text-6xl lg:text-7xl font-black text-slate-900 leading-tight mb-8">
                                    50 applications.<br />
                                    <span className="text-slate-400">Zero responses.</span>
                                </h1>
                                <p className="text-xl md:text-2xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
                                    Hours spent tailoring each one. Copy. Paste. Tweak. Repeat.<br />
                                    <span className="text-slate-400">It's exhausting.</span>
                                </p>
                            </motion.div>

                            {/* Scroll indicator */}
                            <motion.div
                                className="absolute bottom-12 left-1/2 -translate-x-1/2"
                                animate={{ y: [0, 10, 0] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            >
                                <div className="w-6 h-10 border-2 border-slate-300 rounded-full flex justify-center pt-2">
                                    <div className="w-1 h-2 bg-slate-400 rounded-full" />
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* Scene 2: The Realization */}
                    <motion.div
                        className="absolute inset-0 flex items-center justify-center px-6"
                        style={{ opacity: opacity2, y: y2 }}
                    >
                        <div className="max-w-4xl">
                            <div className="grid md:grid-cols-2 gap-12 items-center">
                                <div>
                                    <p className="text-primary-600 font-bold mb-4 tracking-wide uppercase text-sm">The realization</p>
                                    <h2 className="text-4xl md:text-5xl font-black text-slate-900 leading-tight mb-6">
                                        What if a machine could do the boring parts?
                                    </h2>
                                    <p className="text-lg text-slate-600 leading-relaxed">
                                        Not a bot that spams everywhere. Something smarter.
                                        Something that actually reads job posts, understands what they want,
                                        and writes applications that sound like <em>you</em>.
                                    </p>
                                </div>
                                <div className="relative">
                                    {/* Abstract representation - flowing lines */}
                                    <svg viewBox="0 0 400 400" className="w-full max-w-md mx-auto">
                                        <motion.path
                                            d="M50 200 Q150 100 200 200 Q250 300 350 200"
                                            stroke="url(#gradient1)"
                                            strokeWidth="3"
                                            fill="none"
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: 1 }}
                                            transition={{ duration: 2, ease: "easeInOut" }}
                                        />
                                        <motion.path
                                            d="M50 220 Q150 120 200 220 Q250 320 350 220"
                                            stroke="url(#gradient2)"
                                            strokeWidth="2"
                                            fill="none"
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: 1 }}
                                            transition={{ duration: 2, delay: 0.3, ease: "easeInOut" }}
                                        />
                                        <motion.circle
                                            cx="350"
                                            cy="200"
                                            r="8"
                                            fill="#FF6B35"
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            transition={{ duration: 0.5, delay: 1.8 }}
                                        />
                                        <defs>
                                            <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stopColor="#94a3b8" />
                                                <stop offset="100%" stopColor="#FF6B35" />
                                            </linearGradient>
                                            <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                                                <stop offset="0%" stopColor="#cbd5e1" />
                                                <stop offset="100%" stopColor="#f97316" />
                                            </linearGradient>
                                        </defs>
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Scene 3: What We Built */}
                    <motion.div
                        className="absolute inset-0 flex items-center justify-center px-6"
                        style={{ opacity: opacity3, y: y3 }}
                    >
                        <div className="max-w-5xl">
                            <div className="text-center mb-16">
                                <p className="text-primary-600 font-bold mb-4 tracking-wide uppercase text-sm">So we built it</p>
                                <h2 className="text-4xl md:text-5xl font-black text-slate-900 leading-tight">
                                    An AI that hunts jobs<br />while you sleep.
                                </h2>
                            </div>

                            {/* Visual representation */}
                            <div className="relative max-w-3xl mx-auto">
                                <div className="bg-white rounded-3xl shadow-2xl shadow-slate-200/50 border border-slate-100 p-8 md:p-12">
                                    <div className="flex items-start gap-6">
                                        <div className="flex-shrink-0">
                                            <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/20">
                                                <Bot className="w-8 h-8 text-white" />
                                            </div>
                                        </div>
                                        <div className="flex-1 space-y-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                                                <span className="text-sm font-medium text-slate-500">Working right now</span>
                                            </div>
                                            <div className="space-y-3">
                                                <motion.div
                                                    className="h-3 bg-slate-100 rounded-full overflow-hidden"
                                                    initial={{ width: 0 }}
                                                    animate={{ width: "100%" }}
                                                >
                                                    <motion.div
                                                        className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full"
                                                        initial={{ width: "0%" }}
                                                        animate={{ width: "75%" }}
                                                        transition={{ duration: 2, delay: 0.5 }}
                                                    />
                                                </motion.div>
                                                <p className="text-sm text-slate-500">Found 23 matching jobs · Applied to 18 · 3 responses</p>
                                            </div>
                                            <p className="text-slate-600 leading-relaxed">
                                                It scans thousands of listings. Finds the ones that actually match your skills.
                                                Writes cover letters that don't sound like a robot. Submits. Tracks. Follows up.
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Floating elements */}
                                <motion.div
                                    className="absolute -top-4 -right-4 bg-green-100 text-green-700 px-4 py-2 rounded-full text-sm font-bold shadow-lg"
                                    animate={{ y: [0, -5, 0] }}
                                    transition={{ duration: 3, repeat: Infinity }}
                                >
                                    Interview request! 🎉
                                </motion.div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Scene 4: CTA */}
                    <motion.div
                        className="absolute inset-0 flex items-center justify-center px-6"
                        style={{ opacity: opacity4, y: y4 }}
                    >
                        <div className="max-w-3xl text-center">
                            <h2 className="text-4xl md:text-6xl font-black text-slate-900 leading-tight mb-8">
                                Your next job is out there.<br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-primary-600">
                                    Let us find it.
                                </span>
                            </h2>
                            <p className="text-xl text-slate-600 mb-12 max-w-xl mx-auto">
                                Join thousands who've stopped the scroll and started getting interviews.
                            </p>
                            <Link to="/login">
                                <Button
                                    variant="primary"
                                    size="lg"
                                    className="rounded-full px-10 py-6 text-lg font-bold shadow-2xl shadow-primary-500/20 hover:shadow-primary-500/40 transition-shadow"
                                >
                                    Start Hunting Free
                                    <ArrowRight className="w-5 h-5 ml-2" />
                                </Button>
                            </Link>
                            <p className="text-sm text-slate-400 mt-6">No credit card. Cancel anytime. Actually works.</p>
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Final static section */}
            <div className="bg-slate-900 py-24 px-6">
                <div className="max-w-4xl mx-auto text-center">
                    <p className="text-slate-400 text-lg mb-2">Built by people who were tired of job hunting.</p>
                    <p className="text-slate-500 text-sm">
                        We're a small team that believes finding a job shouldn't be a full-time job.
                    </p>
                </div>
            </div>
        </div>
    );
}
