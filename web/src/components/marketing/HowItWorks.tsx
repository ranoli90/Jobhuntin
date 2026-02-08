import * as React from "react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const JOURNEY_STEPS = [
  {
    number: "01",
    title: "Discovery",
    headline: "We hunt while you sleep",
    description: "Our AI agents scan 50+ job boards every hour, analyzing thousands of listings to find roles that actually match your skills, salary expectations, and career goals—not just keyword matches.",
    stat: "2,400+",
    statLabel: "Jobs scanned daily",
    visual: "search",
    color: "from-cyan-500 to-blue-600",
  },
  {
    number: "02",
    title: "Crafting",
    headline: "Applications that get noticed",
    description: "Generic resumes get ignored. We analyze each company's culture, tech stack, and job requirements to craft personalized applications that speak their language and highlight your relevant wins.",
    stat: "87%",
    statLabel: "Response rate vs 3% average",
    visual: "craft",
    color: "from-violet-500 to-fuchsia-600",
  },
  {
    number: "03",
    title: "Execution",
    headline: "One click, infinite applications",
    description: "Review and approve each application in seconds. We handle the tedious forms, cover letters, and submissions. Apply to 50 jobs in the time it takes to drink your coffee.",
    stat: "50x",
    statLabel: "Faster than manual applying",
    visual: "execute",
    color: "from-amber-500 to-orange-600",
  },
  {
    number: "04",
    title: "Victory",
    headline: "Interviews, not inbox zero",
    description: "Track every application in real-time. When responses come in, we surface them instantly. Your only job? Show up and nail the interview. We'll even prep you with company research.",
    stat: "3.2x",
    statLabel: "More interviews per month",
    visual: "win",
    color: "from-emerald-500 to-teal-600",
  },
];

// Custom visual component for each step
function StepVisual({ type, color }: { type: string; color: string }) {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <motion.div 
      ref={containerRef}
      className="relative w-full h-full min-h-[300px] lg:min-h-[400px] rounded-2xl overflow-hidden bg-gradient-to-br from-slate-900 to-slate-950 border border-white/5"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      {/* Background glow */}
      <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-10`} />
      
      {/* Grid pattern */}
      <svg className="absolute inset-0 w-full h-full opacity-30">
        <defs>
          <pattern id={`grid-${type}`} width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-white" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill={`url(#grid-${type})`} />
      </svg>

      {/* Step-specific animations */}
      {type === "search" && (
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Radar search animation */}
          <div className="relative">
            <motion.div
              className="w-32 h-32 rounded-full border-2 border-cyan-500/30"
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.div
              className="absolute inset-0 w-32 h-32 rounded-full border-2 border-cyan-500/30"
              animate={{ scale: [1, 1.8, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
            />
            <div className={`w-32 h-32 rounded-full bg-gradient-to-br ${color} flex items-center justify-center shadow-2xl`}>
              <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          {/* Floating job icons */}
          {[0, 1, 2, 3].map((i) => (
            <motion.div
              key={i}
              className="absolute w-8 h-8 rounded-lg bg-white/10 backdrop-blur-sm flex items-center justify-center"
              style={{
                top: `${20 + i * 20}%`,
                left: `${10 + i * 25}%`,
              }}
              animate={{ y: [0, -10, 0], opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 3, repeat: Infinity, delay: i * 0.5 }}
            >
              <div className="w-4 h-4 rounded bg-gradient-to-br from-white/40 to-white/20" />
            </motion.div>
          ))}
        </div>
      )}

      {type === "craft" && (
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Document crafting animation */}
          <div className="relative w-48 h-64">
            {/* Background document */}
            <motion.div
              className="absolute inset-0 rounded-lg bg-white/5 border border-white/10 backdrop-blur-sm"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            />
            {/* Middle document */}
            <motion.div
              className="absolute inset-2 rounded-lg bg-white/10 border border-white/20 backdrop-blur-sm p-4"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
            >
              <div className="space-y-2">
                <div className="h-2 w-3/4 bg-white/20 rounded" />
                <div className="h-2 w-full bg-white/10 rounded" />
                <div className="h-2 w-5/6 bg-white/10 rounded" />
                <div className="h-2 w-2/3 bg-white/10 rounded" />
              </div>
            </motion.div>
            {/* Front document with active editing */}
            <motion.div
              className="absolute inset-4 rounded-lg bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/30 backdrop-blur-sm p-4"
              animate={{ y: [0, -12, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-400 to-fuchsia-400" />
                  <div className="h-2 w-16 bg-white/30 rounded" />
                </div>
                <motion.div 
                  className="h-2 w-full bg-gradient-to-r from-violet-400/40 to-fuchsia-400/40 rounded"
                  animate={{ width: ["60%", "100%", "60%"] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                />
                <div className="h-2 w-full bg-white/20 rounded" />
                <div className="h-2 w-4/5 bg-white/10 rounded" />
              </div>
              {/* Cursor */}
              <motion.div
                className="absolute bottom-4 right-4 w-0.5 h-4 bg-violet-400"
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              />
            </motion.div>
          </div>
        </div>
      )}

      {type === "execute" && (
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Rocket/launch animation */}
          <div className="relative">
            {/* Launch particles */}
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-1 h-8 rounded-full bg-gradient-to-t from-amber-500 to-transparent"
                style={{
                  left: `${50 + (i - 4) * 15}%`,
                  top: "60%",
                }}
                animate={{ 
                  y: [0, 60, 0], 
                  opacity: [0, 1, 0],
                  scaleY: [0.5, 1.5, 0.5]
                }}
                transition={{ 
                  duration: 1.5, 
                  repeat: Infinity, 
                  delay: i * 0.1,
                  ease: "easeOut"
                }}
              />
            ))}
            {/* Rocket body */}
            <motion.div
              className={`w-20 h-32 rounded-t-full bg-gradient-to-b ${color} relative shadow-2xl`}
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            >
              {/* Window */}
              <div className="absolute top-6 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white/30 border-2 border-white/50" />
              {/* Fins */}
              <div className="absolute bottom-0 -left-4 w-6 h-12 bg-gradient-to-b from-amber-600 to-amber-800 rounded-l-lg" />
              <div className="absolute bottom-0 -right-4 w-6 h-12 bg-gradient-to-b from-amber-600 to-amber-800 rounded-r-lg" />
            </motion.div>
            {/* Speed lines */}
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-16 h-0.5 bg-white/20 rounded-full"
                style={{
                  left: `${20 + i * 15}%`,
                  top: `${30 + i * 10}%`,
                }}
                animate={{ 
                  x: [-20, 20, -20],
                  opacity: [0.2, 0.5, 0.2]
                }}
                transition={{ 
                  duration: 2, 
                  repeat: Infinity, 
                  delay: i * 0.2,
                }}
              />
            ))}
          </div>
        </div>
      )}

      {type === "win" && (
        <div className="absolute inset-0 flex items-center justify-center">
          {/* Trophy/celebration animation */}
          <div className="relative">
            {/* Confetti particles */}
            {[...Array(12)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 rounded-sm"
                style={{
                  backgroundColor: ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"][i % 4],
                  left: "50%",
                  top: "50%",
                }}
                animate={{ 
                  x: [0, (i - 6) * 30, (i - 6) * 40],
                  y: [0, -100 - i * 10, -150],
                  rotate: [0, 360, 720],
                  opacity: [1, 1, 0]
                }}
                transition={{ 
                  duration: 2, 
                  repeat: Infinity, 
                  delay: i * 0.1,
                  ease: "easeOut"
                }}
              />
            ))}
            {/* Trophy */}
            <motion.div
              className={`w-24 h-32 rounded-t-lg bg-gradient-to-b ${color} relative shadow-2xl`}
              animate={{ 
                scale: [1, 1.05, 1],
                rotate: [0, -2, 2, 0]
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              {/* Cup body */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-20 h-20 bg-gradient-to-b from-yellow-400 to-amber-600 rounded-b-3xl rounded-t-lg" />
              {/* Handles */}
              <div className="absolute top-4 -left-3 w-6 h-12 border-4 border-yellow-500 rounded-l-full" />
              <div className="absolute top-4 -right-3 w-6 h-12 border-4 border-yellow-500 rounded-r-full" />
              {/* Star */}
              <motion.div
                className="absolute top-6 left-1/2 -translate-x-1/2"
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              >
                <svg className="w-8 h-8 text-yellow-200" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </motion.div>
            </motion.div>
          </div>
        </div>
      )}
    </motion.div>
  );
}

export function HowItWorks() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section id="how" className="relative py-24 lg:py-32 bg-slate-950 overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
      </div>

      <div ref={containerRef} className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div 
          className="mb-20 lg:mb-32 text-center"
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          <span className="inline-block px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-sm font-medium text-slate-400 mb-6">
            How Skedaddle Works
          </span>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white">
            From search to offer,
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              completely automated
            </span>
          </h2>
          <p className="mt-6 text-lg text-slate-400 max-w-2xl mx-auto">
            Four powerful stages that transform job hunting from a grind into a competitive advantage
          </p>
        </motion.div>

        {/* Journey steps */}
        <div className="space-y-24 lg:space-y-32">
          {JOURNEY_STEPS.map((step, index) => {
            const isEven = index % 2 === 0;
            
            return (
              <motion.div
                key={step.number}
                className={`grid lg:grid-cols-2 gap-12 lg:gap-20 items-center ${isEven ? '' : 'lg:flex-row-reverse'}`}
                initial={{ opacity: 0, y: 60 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
              >
                {/* Content */}
                <div className={`${isEven ? 'lg:order-1' : 'lg:order-2'}`}>
                  <div className="flex items-center gap-4 mb-6">
                    <span className={`text-5xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                      {step.number}
                    </span>
                    <div className="h-px flex-1 bg-gradient-to-r from-slate-800 to-transparent" />
                  </div>
                  
                  <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">
                    {step.title}
                  </span>
                  
                  <h3 className="mt-3 text-3xl sm:text-4xl font-bold text-white">
                    {step.headline}
                  </h3>
                  
                  <p className="mt-4 text-lg text-slate-400 leading-relaxed">
                    {step.description}
                  </p>
                  
                  {/* Stat highlight */}
                  <div className="mt-8 inline-flex items-center gap-3 px-5 py-3 rounded-xl bg-slate-900 border border-slate-800">
                    <span className={`text-2xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                      {step.stat}
                    </span>
                    <span className="text-sm text-slate-500">{step.statLabel}</span>
                  </div>
                </div>

                {/* Visual */}
                <div className={`${isEven ? 'lg:order-2' : 'lg:order-1'}`}>
                  <StepVisual type={step.visual} color={step.color} />
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <motion.div 
          className="mt-24 lg:mt-32 text-center"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex flex-col sm:flex-row items-center gap-4 p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800">
            <span className="text-lg text-slate-300">Ready to transform your job search?</span>
            <button 
              onClick={() => document.getElementById("pricing")?.scrollIntoView({ behavior: "smooth" })}
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium hover:from-cyan-400 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/25"
            >
              Get started free
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
