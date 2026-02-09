import * as React from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Button } from "../ui/Button";
import { ArrowRight, Play, MousePointer, Zap } from "lucide-react";

interface HeroProps {
  onGetStarted: () => void;
}

// Custom animated job application particle
function ApplicationParticle({ delay, x, y, color }: { delay: number; x: number; y: number; color: string }) {
  return (
    <motion.div
      className={`absolute w-3 h-3 rounded-full ${color}`}
      initial={{ x, y, opacity: 0, scale: 0 }}
      animate={{
        x: [x, x + 30, x + 60, x + 100],
        y: [y, y - 20, y + 10, y],
        opacity: [0, 1, 1, 0],
        scale: [0, 1, 1, 0.5],
      }}
      transition={{
        duration: 4,
        delay,
        repeat: Infinity,
        repeatDelay: 2,
        ease: "easeInOut",
      }}
    />
  );
}

// Floating document card animation
function FloatingCard({ 
  children, 
  delay, 
  x, 
  y, 
  rotate = 0,
  className = ""
}: { 
  children: React.ReactNode; 
  delay: number; 
  x: number | string; 
  y: number | string;
  rotate?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={`absolute ${className}`}
      initial={{ x, y, opacity: 0, rotate }}
      animate={{
        y: typeof y === 'number' ? [y, y - 15, y] : y,
        opacity: 1,
        rotate: [rotate, rotate + 2, rotate - 2, rotate],
      }}
      transition={{
        y: { duration: 5, repeat: Infinity, ease: "easeInOut" },
        rotate: { duration: 8, repeat: Infinity, ease: "easeInOut" },
        opacity: { duration: 0.8, delay },
      }}
    >
      {children}
    </motion.div>
  );
}

export function Hero({ onGetStarted }: HeroProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });
  
  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);
  const textY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <section 
      ref={containerRef}
      className="relative min-h-screen overflow-hidden bg-slate-950"
    >
      {/* Deep space gradient background */}
      <motion.div 
        className="absolute inset-0"
        style={{ y: backgroundY }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />
        
        {/* Animated mesh gradient */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-1/4 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-cyan-500/10 to-blue-600/10 blur-[120px] animate-pulse" />
          <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-violet-500/10 to-fuchsia-600/10 blur-[100px] animate-pulse" style={{ animationDelay: "2s" }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] rounded-full bg-gradient-to-br from-amber-500/5 to-orange-600/5 blur-[150px] animate-pulse" style={{ animationDelay: "4s" }} />
        </div>

        {/* Constellation grid */}
        <svg className="absolute inset-0 w-full h-full opacity-20">
          <defs>
            <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" fill="currentColor" className="text-slate-600" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </motion.div>

      {/* Floating application visualization */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Document cards floating around */}
        <FloatingCard delay={0.2} x={100} y={150} rotate={-5} className="hidden lg:block">
          <div className="w-48 h-32 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 p-3 shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500" />
              <div className="h-2 w-20 bg-white/20 rounded" />
            </div>
            <div className="space-y-1.5">
              <div className="h-1.5 w-full bg-white/10 rounded" />
              <div className="h-1.5 w-3/4 bg-white/10 rounded" />
              <div className="h-1.5 w-1/2 bg-white/10 rounded" />
            </div>
            <div className="mt-3 flex gap-1">
              <span className="px-2 py-0.5 text-[10px] bg-cyan-500/20 text-cyan-300 rounded">React</span>
              <span className="px-2 py-0.5 text-[10px] bg-violet-500/20 text-violet-300 rounded">Senior</span>
            </div>
          </div>
        </FloatingCard>

        <FloatingCard delay={0.4} x={"calc(100vw - 300px)"} y={200} rotate={3} className="hidden lg:block">
          <div className="w-44 h-28 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 p-3 shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-5 h-5 rounded bg-gradient-to-br from-amber-400 to-orange-500" />
              <div className="h-2 w-16 bg-white/20 rounded" />
            </div>
            <div className="space-y-1">
              <div className="h-1.5 w-full bg-white/10 rounded" />
              <div className="h-1.5 w-2/3 bg-white/10 rounded" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-400">
              <Zap className="w-3 h-3" />
              <span>Applied 2m ago</span>
            </div>
          </div>
        </FloatingCard>

        <FloatingCard delay={0.6} x={150} y={"calc(100vh - 250px)"} rotate={-3} className="hidden lg:block">
          <div className="w-40 h-24 rounded-lg bg-white/5 backdrop-blur-sm border border-emerald-500/20 p-3 shadow-2xl">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-xs text-emerald-400 font-medium">Interview Scheduled</span>
            </div>
            <div className="text-[10px] text-white/50">Today at 2:00 PM</div>
          </div>
        </FloatingCard>

        {/* Animated particles showing applications flowing */}
        <ApplicationParticle delay={0} x={300} y={300} color="bg-cyan-400" />
        <ApplicationParticle delay={0.8} x={500} y={400} color="bg-violet-400" />
        <ApplicationParticle delay={1.6} x={400} y={250} color="bg-amber-400" />
        <ApplicationParticle delay={2.4} x={600} y={350} color="bg-emerald-400" />
        <ApplicationParticle delay={3.2} x={350} y={450} color="bg-fuchsia-400" />
      </div>

      {/* Main content */}
      <motion.div 
        className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-32 lg:pt-40 pb-20"
        style={{ y: textY, opacity }}
      >
        <div className="mx-auto max-w-4xl text-center">
          {/* Animated badge - Reduced delay for LCP */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-8"
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-sm font-medium text-cyan-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              AI-Powered Job Hunting
            </span>
          </motion.div>

          {/* Main headline - Removed delay for LCP */}
          <motion.h1 
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="block">Apply to</span>
            <span className="block mt-2 bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 bg-clip-text text-transparent">
              100 jobs
            </span>
            <span className="block mt-2">before breakfast</span>
          </motion.h1>

          {/* Subheadline - Staggered slightly */}
          <motion.p 
            className="mx-auto mt-6 max-w-2xl text-lg sm:text-xl text-slate-400 leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Your AI teammate that finds perfect matches, crafts personalized applications, 
            and submits them while you sleep. You just nail the interviews.
          </motion.p>

          {/* CTA buttons */}
          <motion.div 
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Button 
              size="lg" 
              onClick={onGetStarted} 
              className="group relative overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white border-0 shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all min-w-[200px] h-14 text-base"
            >
              <span className="relative z-10 flex items-center">
                Start applying free
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </span>
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
              className="group min-w-[200px] h-14 text-base border-slate-700 bg-slate-900/50 text-slate-300 hover:bg-slate-800 hover:text-white backdrop-blur-sm"
            >
              <Play className="mr-2 h-5 w-5" />
              See how it works
            </Button>
          </motion.div>

          {/* Trust indicators */}
          <motion.div 
            className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              No credit card required
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              10 free applications
            </span>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Cancel anytime
            </span>
          </motion.div>
        </div>
      </motion.div>

      {/* Scroll indicator */}
      <motion.div 
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="flex flex-col items-center gap-2 text-slate-500"
        >
          <span className="text-xs uppercase tracking-widest">Scroll</span>
          <MousePointer className="w-4 h-4 rotate-180" />
        </motion.div>
      </motion.div>
    </section>
  );
}
