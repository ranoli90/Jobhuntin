import * as React from "react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowUpRight, Quote, Star, TrendingUp, Clock, Briefcase } from "lucide-react";

const TESTIMONIALS = [
  {
    quote: "I applied to 47 jobs in one afternoon. Got 6 interviews that week. JobHuntin is like having a personal recruiter who never sleeps.",
    author: "Sarah Chen",
    role: "Product Designer",
    avatar: "SC",
    bgColor: "from-cyan-500 to-blue-600",
    result: "Landed at Stripe",
    timeframe: "3 weeks",
    previous: "Airbnb",
    stats: { applications: 47, interviews: 6, responseRate: "87%" },
  },
  {
    quote: "I was skeptical about AI job applications, but the quality blew me away. Every cover letter felt genuinely personal—not template garbage.",
    author: "Marcus Johnson",
    role: "Software Engineer",
    avatar: "MJ",
    bgColor: "from-violet-500 to-fuchsia-600",
    result: "3 offers, 15% bump",
    timeframe: "4 weeks",
    previous: "Meta",
    stats: { applications: 62, offers: 3, salaryIncrease: "15%" },
  },
  {
    quote: "As a career switcher, I didn't know how to position myself. JobHuntin figured out my transferable skills and found roles I'd never have found.",
    author: "Priya Patel",
    role: "Former Teacher",
    newRole: "UX Researcher",
    avatar: "PP",
    bgColor: "from-emerald-500 to-teal-600",
    result: "Career changed",
    timeframe: "2 months",
    previous: "Education",
    company: "Spotify",
    stats: { applications: 38, interviews: 5, industry: "Tech" },
  },
];

const GLOBAL_STATS = [
  { value: "847K+", label: "Applications sent", icon: Briefcase, trend: "+12% this week" },
  { value: "73%", label: "Interview rate", icon: TrendingUp, trend: "vs 8% average" },
  { value: "14 days", label: "Avg. time to offer", icon: Clock, trend: "Industry: 63 days" },
];

function TestimonialCard({ testimonial, index }: { testimonial: typeof TESTIMONIALS[0]; index: number }) {
  const cardRef = useRef(null);
  const isInView = useInView(cardRef, { once: true, margin: "-50px" });
  const isLarge = index === 0;

  return (
    <motion.div
      ref={cardRef}
      className={`relative group ${isLarge ? 'md:col-span-2 lg:col-span-1' : ''}`}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.15 }}
    >
      <div className="h-full rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 p-6 lg:p-8 overflow-hidden relative">
        {/* Glow effect on hover */}
        <div className={`absolute -inset-px bg-gradient-to-br ${testimonial.bgColor} opacity-0 group-hover:opacity-10 transition-opacity duration-500 rounded-2xl`} />
        
        {/* Quote icon */}
        <Quote className="absolute top-6 right-6 w-8 h-8 text-slate-700" />

        {/* Header with avatar */}
        <div className="flex items-start gap-4 mb-6">
          <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${testimonial.bgColor} flex items-center justify-center text-white font-bold text-lg shadow-lg`}>
            {testimonial.avatar}
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-white">{testimonial.author}</h4>
            <p className="text-sm text-slate-400">{testimonial.role}</p>
            {testimonial.newRole && (
              <p className="text-xs text-emerald-400 mt-0.5">→ {testimonial.newRole}</p>
            )}
          </div>
          <div className="hidden sm:flex items-center gap-1">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
            ))}
          </div>
        </div>

        {/* Quote */}
        <p className="text-slate-300 leading-relaxed text-lg mb-6">
          "{testimonial.quote}"
        </p>

        {/* Stats row */}
        <div className="flex flex-wrap gap-4 mb-6">
          {Object.entries(testimonial.stats).map(([key, value]) => (
            <div key={key} className="px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
              <span className="text-xs text-slate-500 uppercase tracking-wider">{key}</span>
              <p className="text-sm font-semibold text-white">{value}</p>
            </div>
          ))}
        </div>

        {/* Result badge */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <div>
            <p className="text-xs text-slate-500 mb-1">Result</p>
            <p className={`text-sm font-semibold bg-gradient-to-r ${testimonial.bgColor} bg-clip-text text-transparent`}>
              {testimonial.result}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500 mb-1">Timeline</p>
            <p className="text-sm font-medium text-white">{testimonial.timeframe}</p>
          </div>
        </div>

        {/* Previous company tag */}
        <div className="absolute bottom-0 left-0 right-0 px-6 py-2 bg-slate-800/50 border-t border-slate-800">
          <p className="text-xs text-slate-500">Previously: <span className="text-slate-400">{testimonial.previous}</span></p>
        </div>
      </div>
    </motion.div>
  );
}

export function Testimonials() {
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });

  return (
    <section ref={sectionRef} className="relative py-24 lg:py-32 bg-slate-950 overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-cyan-500/5 to-blue-600/5 blur-[100px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-violet-500/5 to-fuchsia-600/5 blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div 
          className="mb-16 lg:mb-20"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div>
              <span className="inline-block px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-sm font-medium text-slate-400 mb-6">
                Success Stories
              </span>
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight">
                Real people.
                <br />
                <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 bg-clip-text text-transparent">
                  Real results.
                </span>
              </h2>
            </div>
            <p className="text-lg text-slate-400 max-w-md lg:text-right">
              Thousands of job seekers have transformed their search with Skedaddle. Here's what they achieved.
            </p>
          </div>
        </motion.div>

        {/* Global stats bar */}
        <motion.div 
          className="mb-16 lg:mb-20"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
            {GLOBAL_STATS.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div 
                  key={stat.label}
                  className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 p-6 lg:p-8"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 to-blue-500/0 group-hover:from-cyan-500/5 group-hover:to-blue-500/5 transition-all duration-500" />
                  <div className="relative">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center">
                        <Icon className="w-5 h-5 text-cyan-400" />
                      </div>
                      <span className="text-sm text-slate-500">{stat.trend}</span>
                    </div>
                    <p className="text-4xl lg:text-5xl font-bold text-white mb-2">{stat.value}</p>
                    <p className="text-slate-400">{stat.label}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Testimonials grid - asymmetric layout */}
        <div className="grid gap-6 lg:gap-8 md:grid-cols-2 lg:grid-cols-3">
          {TESTIMONIALS.map((testimonial, index) => (
            <TestimonialCard key={testimonial.author} testimonial={testimonial} index={index} />
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div 
          className="mt-16 lg:mt-20 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <a 
            href="#pricing" 
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold hover:from-cyan-400 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/25 group"
          >
            Join 12,000+ successful job seekers
            <ArrowUpRight className="w-5 h-5 transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
          </a>
        </motion.div>
      </div>
    </section>
  );
}
