import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
    Bot, Zap, Target, Users, Rocket, Heart,
    ArrowRight, Sparkles, Globe, Shield, Clock,
    TrendingUp, Award, Coffee
} from 'lucide-react';
import { Button } from '../components/ui/Button';

// Animated counter component
function AnimatedCounter({ end, duration = 2, suffix = '' }: { end: number; duration?: number; suffix?: string }) {
    const [count, setCount] = React.useState(0);

    React.useEffect(() => {
        let startTime: number;
        const animate = (timestamp: number) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
            setCount(Math.floor(progress * end));
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    }, [end, duration]);

    return <span>{count.toLocaleString()}{suffix}</span>;
}

// Interactive team member card
function TeamMemberCard({
    name,
    role,
    emoji,
    color
}: {
    name: string;
    role: string;
    emoji: string;
    color: string;
}) {
    return (
        <motion.div
            whileHover={{ y: -8, scale: 1.02 }}
            className={`relative p-6 rounded-3xl bg-gradient-to-br ${color} border border-white/20 shadow-xl overflow-hidden group`}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
                <div className="text-5xl mb-4">{emoji}</div>
                <h3 className="text-xl font-bold text-white mb-1">{name}</h3>
                <p className="text-white/80 text-sm font-medium">{role}</p>
            </div>
            <motion.div
                className="absolute -bottom-4 -right-4 text-[120px] opacity-10"
                animate={{ rotate: [0, 10, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
            >
                {emoji}
            </motion.div>
        </motion.div>
    );
}

// Value proposition card with animation
function ValueCard({
    icon: Icon,
    title,
    description,
    delay
}: {
    icon: React.ElementType;
    title: string;
    description: string;
    delay: number;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay, duration: 0.5 }}
            whileHover={{ scale: 1.03 }}
            className="relative p-6 rounded-2xl bg-white border border-slate-200/50 shadow-lg hover:shadow-xl transition-shadow group"
        >
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center mb-4 shadow-lg shadow-primary-500/20 group-hover:scale-110 transition-transform">
                <Icon className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
            <p className="text-slate-600 text-sm leading-relaxed">{description}</p>
        </motion.div>
    );
}

export default function About() {
    // Background particles for visual interest
    const particles = useMemo(() => {
        return [...Array(15)].map((_, i) => ({
            id: i,
            left: Math.random() * 100,
            top: Math.random() * 100,
            size: Math.random() * 100 + 50,
            duration: Math.random() * 20 + 20,
            delay: Math.random() * 5,
            yMove: (Math.random() - 0.5) * 50,
            color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.08)' : i % 3 === 1 ? 'rgba(74, 144, 226, 0.08)' : 'rgba(139, 92, 246, 0.08)',
        }));
    }, []);

    const stats = [
        { value: 50000, suffix: '+', label: 'Applications Sent' },
        { value: 2500, suffix: '+', label: 'Jobs Landed' },
        { value: 95, suffix: '%', label: 'Time Saved' },
        { value: 24, suffix: '/7', label: 'AI Working' },
    ];

    const values = [
        {
            icon: Zap,
            title: 'Speed Over Everything',
            description: 'In the job market, timing is everything. We built JobHuntin to move faster than humanly possible.',
        },
        {
            icon: Target,
            title: 'Precision Targeting',
            description: 'No spray-and-pray. Our AI learns your preferences and only applies to jobs that actually match.',
        },
        {
            icon: Shield,
            title: 'Your Data, Your Control',
            description: 'Your resume and data stay secure. We never share your information with anyone.',
        },
        {
            icon: Heart,
            title: 'Built for Humans',
            description: 'Technology should reduce stress, not add it. We handle the grind so you can focus on landing the role.',
        },
    ];

    return (
        <div className="min-h-screen bg-slate-50 overflow-hidden">
            {/* Animated Background */}
            <div className="fixed inset-0 pointer-events-none">
                {particles.map((particle) => (
                    <motion.div
                        key={particle.id}
                        className="absolute rounded-full blur-3xl"
                        animate={{
                            y: [0, particle.yMove, 0],
                            scale: [1, 1.1, 1],
                            opacity: [0.5, 0.7, 0.5]
                        }}
                        transition={{
                            duration: particle.duration,
                            repeat: Infinity,
                            ease: "easeInOut",
                            delay: particle.delay
                        }}
                        style={{
                            left: `${particle.left}%`,
                            top: `${particle.top}%`,
                            width: particle.size,
                            height: particle.size,
                            background: particle.color,
                        }}
                    />
                ))}
            </div>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 px-6">
                <div className="max-w-6xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center"
                    >
                        <motion.div
                            className="inline-flex items-center gap-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-bold mb-8"
                            whileHover={{ scale: 1.05 }}
                        >
                            <Sparkles className="w-4 h-4" />
                            Meet the Team Behind the Magic
                        </motion.div>

                        <h1 className="text-5xl md:text-7xl font-black text-slate-900 mb-6 leading-tight">
                            We're on a Mission to{' '}
                            <span className="relative">
                                <span className="relative z-10 text-transparent bg-clip-text bg-gradient-to-r from-primary-500 via-purple-500 to-blue-500">
                                    End Job Search Misery
                                </span>
                                <motion.span
                                    className="absolute inset-0 bg-gradient-to-r from-primary-200 via-purple-200 to-blue-200 blur-2xl opacity-50 -z-10"
                                    animate={{ scale: [1, 1.1, 1] }}
                                    transition={{ duration: 3, repeat: Infinity }}
                                />
                            </span>
                        </h1>

                        <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-12 leading-relaxed">
                            Job hunting sucks. The endless scrolling, the repetitive applications, the ghosting.
                            We built JobHuntin because we've been there—and we knew there had to be a smarter way.
                        </p>

                        {/* Interactive Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
                            {stats.map((stat, index) => (
                                <motion.div
                                    key={stat.label}
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.2 + index * 0.1 }}
                                    whileHover={{ scale: 1.05 }}
                                    className="p-6 rounded-2xl bg-white border border-slate-200/50 shadow-lg"
                                >
                                    <div className="text-4xl font-black text-slate-900 mb-1">
                                        <AnimatedCounter end={stat.value} suffix={stat.suffix} />
                                    </div>
                                    <div className="text-sm text-slate-500 font-medium">{stat.label}</div>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Story Section */}
            <section className="relative py-20 px-6 bg-white">
                <div className="max-w-4xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="prose prose-lg max-w-none"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg shadow-primary-500/20">
                                <Coffee className="w-6 h-6 text-white" />
                            </div>
                            <h2 className="text-3xl font-black text-slate-900 m-0">Our Story</h2>
                        </div>

                        <div className="space-y-6 text-slate-600 leading-relaxed">
                            <p className="text-lg">
                                It started with frustration. Our founder was applying to 50+ jobs a week, spending hours
                                tailoring each application, only to hear nothing back. The process was broken.
                            </p>
                            <p className="text-lg">
                                The realization? Most of the work was repetitive and mechanical—perfect for AI.
                                So we built an agent that could do in minutes what took hours: find matching jobs,
                                tailor applications, and apply—all while you sleep.
                            </p>
                            <p className="text-lg">
                                Today, JobHuntin has helped thousands of job seekers reclaim their time and sanity.
                                We're not just another job board. We're your 24/7 job-hunting companion.
                            </p>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Values Section */}
            <section className="relative py-20 px-6">
                <div className="max-w-6xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-black text-slate-900 mb-4">What We Believe</h2>
                        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                            These aren't just words on a wall. They're the principles that guide every feature we build.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {values.map((value, index) => (
                            <ValueCard key={value.title} {...value} delay={index * 0.1} />
                        ))}
                    </div>
                </div>
            </section>

            {/* Team Section */}
            <section className="relative py-20 px-6 bg-slate-900">
                <div className="max-w-6xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-4xl font-black text-white mb-4">The Humans Behind the Bot</h2>
                        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                            A small team obsessed with making job hunting not terrible.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-3 gap-6">
                        <TeamMemberCard
                            name="The Architect"
                            role="Building the brain"
                            emoji="🧠"
                            color="from-purple-600 to-purple-800"
                        />
                        <TeamMemberCard
                            name="The Designer"
                            role="Making it beautiful"
                            emoji="🎨"
                            color="from-pink-600 to-pink-800"
                        />
                        <TeamMemberCard
                            name="The Hustler"
                            role="Spreading the word"
                            emoji="🚀"
                            color="from-blue-600 to-blue-800"
                        />
                    </div>

                    <motion.p
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                        className="text-center text-slate-500 mt-12 text-sm"
                    >
                        + one very hardworking AI that never sleeps 🤖
                    </motion.p>
                </div>
            </section>

            {/* CTA Section */}
            <section className="relative py-24 px-6 bg-gradient-to-br from-primary-500 via-primary-600 to-purple-600 overflow-hidden">
                <motion.div
                    className="absolute inset-0 opacity-30"
                    animate={{
                        backgroundPosition: ['0% 0%', '100% 100%'],
                    }}
                    transition={{ duration: 20, repeat: Infinity, repeatType: 'reverse' }}
                    style={{
                        backgroundImage: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.15"%3E%3Cpath d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
                    }}
                />

                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-4xl md:text-5xl font-black text-white mb-6">
                            Ready to Let AI Do the Heavy Lifting?
                        </h2>
                        <p className="text-xl text-white/80 mb-10 max-w-2xl mx-auto">
                            Join thousands of job seekers who've already discovered the smarter way to land their dream job.
                        </p>
                        <Link to="/login">
                            <Button
                                variant="secondary"
                                size="lg"
                                className="rounded-full px-10 py-6 text-lg font-bold shadow-2xl hover:scale-105 transition-transform"
                            >
                                Start Hunting for Free
                                <ArrowRight className="w-5 h-5 ml-2" />
                            </Button>
                        </Link>
                    </motion.div>
                </div>
            </section>
        </div>
    );
}
