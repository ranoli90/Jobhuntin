import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useMotionValue, useMotionTemplate, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import { 
  Rocket, Sparkles, Bot, Zap, CheckCircle, ArrowRight, UploadCloud, 
  Code, MailCheck, Smartphone, QrCode, UserCircle, Target, Brain
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { Button } from '../components/ui/Button';

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- DATA ---
const TEASER_JOBS = [
  { id: "t1", title: "Marketing Lead", status: "AI Applied 2m ago" },
  { id: "t2", title: "Sales Manager", status: "Matching..." },
  { id: "t3", title: "Operations Dir", status: "Interview Request!" },
];

// --- COMPONENTS ---

// 0. Live Activity Feed
const ActivityFeed = () => {
  const [activities, setActivities] = useState([
    { text: "Sarah just applied to Google", time: "2s ago" },
    { text: "Mike landed an interview at Stripe", time: "5s ago" },
    { text: "David sent 12 apps in 1 min", time: "8s ago" },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      const newActivities = [
        "Sarah just applied to Google",
        "Mike landed an interview at Stripe", 
        "David sent 12 apps in 1 min",
        "Jenny got a reply from Airbnb",
        "Tom's bot is on fire: 50 apps sent",
        "New job match found in Denver",
        "Alex skipped the line at Netflix"
      ];
      const randomActivity = newActivities[Math.floor(Math.random() * newActivities.length)];
      setActivities(prev => [{ text: randomActivity, time: "Just now" }, ...prev.slice(0, 2)]);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-2">
      <AnimatePresence>
        {activities.map((activity, index) => (
          <motion.div
            key={index + activity.text}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex items-center gap-2 text-xs text-slate-500"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium text-slate-700">{activity.text}</span>
            <span className="text-slate-400 opacity-60">{activity.time}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// 3. Progress Bar
const ProgressBar = () => {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  return (
    <div className="fixed top-0 left-0 right-0 h-1 bg-slate-100 z-[60]">
      <motion.div
        className="h-full bg-gradient-to-r from-primary-500 to-amber-500"
        style={{ scaleX, transformOrigin: "0%" }}
      />
    </div>
  );
};

// 7. Hero Section
const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [jobs, setJobs] = useState(TEASER_JOBS);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  
  // Background Particles Data - Refined for a more artistic look
  const particles = React.useMemo(() => {
    return [...Array(25)].map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: i < 5 ? Math.random() * 150 + 100 : Math.random() * 40 + 10,
      duration: Math.random() * 20 + 20,
      delay: Math.random() * 10,
      yMove: (Math.random() - 0.5) * 150,
      xMove: (Math.random() - 0.5) * 150,
      color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.15)' : i % 3 === 1 ? 'rgba(74, 144, 226, 0.15)' : 'rgba(250, 249, 246, 0.3)',
      blur: i < 5 ? 'blur(60px)' : 'none'
    }));
  }, []);
  
  // Mouse Glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const glowBackground = useMotionTemplate`
    radial-gradient(
      650px circle at ${mouseX}px ${mouseY}px,
      rgba(255, 255, 255, 0.4),
      transparent 40%
    )
  `;

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  const validateEmail = (e: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address.");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    setMatchCount(0);

    // Use shared service
    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");

      if (!result.success) {
        throw new Error(result.error || "Failed to send magic link");
      }

      // Safe Animation Trigger - wrapped in try-catch to prevent crashes
      try {
        if (
          typeof window !== 'undefined' &&
          typeof window.performance !== 'undefined' &&
          typeof window.requestAnimationFrame === 'function'
        ) {
          const end = 47;
          const duration = 1000;
          const startTime = performance.now();
          const animateCounter = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            setMatchCount(Math.floor(progress * end));
            if (progress < 1) {
              requestAnimationFrame(animateCounter);
            }
          };
          requestAnimationFrame(animateCounter);
        }
      } catch (e) {
        console.warn("Animation failed", e);
        // Don't crash if animation fails
      }

      // Safe Confetti Trigger - wrapped in try-catch to prevent crashes
      try {
        if (typeof window !== 'undefined' && confetti) {
          confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FF6B35', '#4A90E2', '#FAF9F6']
          });
        }
      } catch (e) {
        console.warn("Confetti failed", e);
        // Don't crash if confetti fails
      }

      pushToast({ title: "Magic Link Sent! 📧", description: "Check your email to start hunting.", tone: "success" });
      setSentEmail(result.email);
      setEmail(""); // Clear
      setIsSubmitting(false);

    } catch (err: any) {
      setIsSubmitting(false);
      setSentEmail(null);
      const message = err?.message || "Failed to send magic link";
      setEmailError(message);
      pushToast({ title: "Error", description: message, tone: "error" });
    }
  };

  const removeJob = (index: number) => {
    setJobs(prev => prev.filter((_, i) => i !== index));
    setTimeout(() => {
      setJobs(prev => [...prev, { 
        id: Math.random().toString(36).substr(2, 9),
        title: "New Match Found!", 
        status: "Analyzing..." 
      }]);
    }, 500);
  };

  return (
    <section className="relative min-h-[85vh] pt-32 pb-12 flex items-center justify-center overflow-hidden bg-slate-50">
      {/* Premium Background Layers */}
      <div className="absolute inset-0 bg-grid-premium opacity-[0.4] pointer-events-none" />
      
      {/* Large Artistic Gradient Blobs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {particles.map((particle) => (
          <motion.div
            key={particle.id}
            className="absolute rounded-full"
            animate={{ 
              y: [0, particle.yMove, 0],
              x: [0, particle.xMove, 0],
              rotate: [0, 360],
              scale: [1, 1.1, 1]
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
              filter: particle.blur,
              willChange: "transform"
            }}
          />
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-6 relative z-10 grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
        {/* Left Content */}
        <div className="text-center lg:text-left pt-10 lg:pt-0">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm mb-6 border border-primary-100"
          >
            <Sparkles className="w-4 h-4 text-primary-500" />
            <span className="text-xs sm:text-sm font-semibold text-slate-600">
              AI Hunts Jobs For You
            </span>
          </motion.div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-black font-display text-slate-900 leading-[0.95] mb-6 sm:mb-8 tracking-tighter">
            Hunt Jobs with <br />
            <span className="relative inline-block mt-2">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 via-amber-500 to-red-500 animate-gradient-x">
                AI Magic
              </span>
              <motion.span 
                className="absolute -top-4 -right-8 sm:-right-10 text-4xl sm:text-5xl pointer-events-none"
                animate={{ 
                  rotate: [0, 15, -15, 0],
                  scale: [1, 1.2, 1],
                }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
              >
                ✨
              </motion.span>
            </span>
          </h1>

          <p className="text-lg sm:text-xl lg:text-2xl text-slate-500 mb-8 sm:mb-10 max-w-lg mx-auto lg:mx-0 leading-tight font-medium">
            Upload once. AI swipes & applies to 100s of jobs while you sleep. 
            <span className="text-slate-900 border-b-2 border-primary-500/30"> Beats Sorce.jobs</span> on every metric.
          </p>

          {!sentEmail && (
          <div 
            className="group relative max-w-md mx-auto lg:mx-0 p-1 rounded-2xl bg-gradient-to-r from-primary-500 to-amber-500 transition-transform hover:scale-[1.01]"
            onMouseMove={handleMouseMove}
          >
            <motion.div
              className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
              style={{
                background: glowBackground,
              }}
            />
            <form onSubmit={onSubmit} className="bg-white rounded-xl p-2 flex flex-col sm:flex-row gap-2 relative z-10">
              <div className="flex-1">
                <input 
                  type="email" 
                  placeholder="you@example.com"  
                  className={cn(
                    "w-full px-4 py-3 rounded-lg bg-slate-50 focus:outline-none focus:ring-2 transition-all text-slate-900",
                    emailError ? "ring-2 ring-red-500 bg-red-50" : "focus:ring-primary-500/20"
                  )}
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError("");
                  }}
                />
              </div>
              <Button 
                type="submit"
                disabled={isSubmitting}
                variant="secondary"
                size="lg"
                className="w-full sm:w-auto px-8 py-3 rounded-lg shadow-lg hover:shadow-primary-500/25 whitespace-nowrap"
              >
                {isSubmitting ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                    <Sparkles className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <>
                    Start Hunt <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </form>
          </div>
          )}
          
          {emailError && (
            <motion.p 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-red-500 text-sm mt-2 font-medium"
            >
              {emailError}
            </motion.p>
          )}

          {matchCount > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center gap-2 justify-center lg:justify-start text-primary-600 font-bold"
            >
              <CheckCircle className="w-5 h-5" />
              Found {matchCount} Denver matches!
            </motion.div>
          )}

          {/* Live Activity Feed */}
          <div className="mt-8 relative h-12 overflow-hidden max-w-sm mx-auto lg:mx-0">
             <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-transparent to-slate-50 z-10 pointer-events-none" />
             <ActivityFeed />
          </div>

          {sentEmail && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-white border border-slate-100 rounded-2xl p-5 shadow-lg text-left"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-primary-50 flex items-center justify-center">
                  <MailCheck className="w-5 h-5 text-primary-500" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold">Magic link en route</p>
                  <p className="text-base font-semibold text-slate-900">Sent to {sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-3">
                Look for an email from <span className="font-semibold">noreply@jobhuntin.com</span>. When you tap the link we’ll drop you straight into onboarding.
              </p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-slate-600">
                <li>Open the inbox (or spam folder) for {sentEmail}.</li>
                <li>Find the message titled <em>“Start your JobHuntin run”</em> and press the button.</li>
                <li>Keep this tab open—onboarding launches as soon as the link opens.</li>
              </ol>
              <div className="flex flex-wrap gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setSentEmail(null)}
                  className="text-sm font-semibold text-primary-600 hover:underline"
                >
                  Use a different email
                </button>
              </div>
            </motion.div>
          )}

          <div className="mt-8 flex items-center justify-center lg:justify-start gap-4 text-sm text-slate-500">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center animate-bounce-slow">
              <UploadCloud className="w-6 h-6 text-primary-500" />
            </div>
            <p className="leading-tight">
              <span className="font-bold text-slate-900">Drag & Drop Resume</span><br/>
              to activate auto-apply
            </p>
          </div>
        </div>

        {/* Right Content - Swipe Cards */}
        <div className="relative h-[400px] sm:h-[500px] flex items-center justify-center perspective-1000 mt-10 lg:mt-0">
           <AnimatePresence>
            {jobs.slice(0, 3).map((job, index) => (
              <motion.div
                key={job.id}
                className="absolute w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6 border border-slate-100 cursor-grab active:cursor-grabbing touch-pan-y"
                style={{ zIndex: jobs.length - index }}
                initial={{ scale: 0.9, y: 50 * index, opacity: 1 - index * 0.3 }}
                animate={{ scale: 1 - index * 0.05, y: 20 * index, opacity: 1 - index * 0.2 }}
                exit={{ x: 200, opacity: 0, rotate: 20 }}
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={(_, info) => {
                  if (info.offset.x > 100 || info.offset.x < -100) {
                    removeJob(index);
                  }
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-blue-500" />
                  </div>
                  <span className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold">
                    98% Match
                  </span>
                </div>
                <h3 className="text-xl font-bold text-slate-900">{job.title}</h3>
                <p className="text-slate-500 mb-4">{job.status}</p>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-primary-500" 
                    initial={{ width: 0 }}
                    animate={{ width: "98%" }}
                    transition={{ duration: 1.5, delay: 0.5 }}
                  />
                </div>
                <p className="text-xs text-right mt-1 text-slate-400">AI Analysis Complete</p>
              </motion.div>
            ))}
          </AnimatePresence>
          
          <motion.div 
            className="absolute bottom-4 sm:bottom-10 right-10 text-slate-400 flex items-center gap-2 pointer-events-none bg-white/50 backdrop-blur px-2 py-1 rounded"
            animate={{ x: [0, 20, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <span className="text-sm font-medium">Swipe to apply</span>
            <ArrowRight className="w-4 h-4" />
          </motion.div>
        </div>
      </div>
      
      {/* Wavy Divider */}
      <div className="absolute bottom-0 left-0 right-0 w-full overflow-hidden leading-none">
        <svg className="relative block w-[calc(100%+1.3px)] h-[50px] sm:h-[100px]" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" className="fill-white"></path>
        </svg>
      </div>
    </section>
  );
};

// 8. Onboarding & Features
const Onboarding = () => {
  return (
    <section id="how-it-works" className="py-32 bg-white relative overflow-hidden">
      {/* Subtle Background Art */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-slate-50 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-24 items-center">
          <div className="relative group">
             <motion.div 
               className="aspect-square bg-slate-50 rounded-[3rem] flex items-center justify-center relative z-10 overflow-hidden shadow-inner"
               initial={{ scale: 0.9, opacity: 0 }}
               whileInView={{ scale: 1, opacity: 1 }}
               viewport={{ once: true }}
             >
                <Bot className="w-48 h-48 text-slate-200 group-hover:text-primary-500/20 transition-colors duration-700" />
                
                {/* Scanner Animation */}
                <motion.div 
                  className="absolute inset-0 bg-gradient-to-b from-transparent via-primary-500/10 to-transparent w-full h-20"
                  animate={{ top: ["-20%", "100%", "-20%"] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                />

                {/* Particle Overlay */}
                <div className="absolute inset-0 opacity-30">
                  {[...Array(10)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="absolute w-1 h-1 bg-primary-500 rounded-full"
                      animate={{ 
                        x: [Math.random() * 400, Math.random() * 400],
                        y: [Math.random() * 400, Math.random() * 400],
                        opacity: [0, 1, 0]
                      }}
                      transition={{ duration: Math.random() * 3 + 2, repeat: Infinity }}
                    />
                  ))}
                </div>
             </motion.div>
             <div className="absolute -top-12 -left-12 w-48 h-48 bg-primary-500/5 rounded-full blur-3xl" />
             <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl" />
          </div>

          <div>
            <div className="inline-block bg-primary-50 text-primary-600 px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-6">
              The Protocol
            </div>
            <h2 className="text-5xl sm:text-6xl font-black font-display text-slate-900 leading-[1.1] mb-12 tracking-tighter">
              One Click. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-amber-500">Infinite Reach.</span>
            </h2>
            <div className="space-y-12">
              {[
                { 
                  icon: UserCircle, 
                  title: "We See The Real You", 
                  desc: "Forget keywords. We build a psychological profile of your career narrative, capturing the nuance, ambition, and potential that resumes often miss. We translate 'you' into a language recruiters crave." 
                },
                { 
                  icon: Target, 
                  title: "Stop Wasting Emotional Energy", 
                  desc: "Applying is draining. Rejection is personal. We detach the emotion from the process. Our agent acts as your relentless, unfeeling advocate, ensuring you only engage when there's a real signal." 
                },
                { 
                  icon: Rocket, 
                  title: "Autonomous Submission", 
                  desc: "Every application is unique. Custom-tailored cover letters and optimized form-filling happen in milliseconds, not minutes. We handle the grind; you handle the interview." 
                }
              ].map((step, i) => (
                <motion.div 
                  key={i}
                  className="flex gap-8 group"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center flex-shrink-0 group-hover:bg-primary-500 group-hover:rotate-6 transition-all duration-500 shadow-sm group-hover:shadow-primary-500/20">
                    <step.icon className="w-8 h-8 text-primary-500 group-hover:text-white transition-colors" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-slate-900 mb-2 tracking-tight">{step.title}</h3>
                    <p className="text-slate-500 text-lg leading-relaxed font-medium">{step.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// 10. Automation Edge & Telegram
const AutomationEdge = () => {
  return (
    <section className="py-24 bg-white overflow-hidden">
      <div className="container mx-auto px-6 relative">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-block bg-blue-50 px-4 py-1 rounded-full text-sm font-mono text-blue-500 mb-6">
            New: Control via Telegram
          </div>
          <h2 className="text-4xl font-bold font-display text-slate-900 mb-6">Control the Hunt via Telegram</h2>
          <p className="text-slate-500 text-lg mb-10">
            Get instant notifications when AI lands you an interview. Approve applications with one tap.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Button 
              className="bg-[#0088cc] text-white px-8 py-4 rounded-2xl font-bold hover:bg-[#0077b5] transition-colors flex items-center gap-3 shadow-lg shadow-blue-500/30 h-auto"
            >
              <Smartphone className="w-6 h-6" />
              Add JobHuntin Bot
            </Button>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <QrCode className="w-4 h-4" />
              <span>or scan QR code</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// --- MAIN PAGE ---
export default function Homepage() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 overflow-x-hidden selection:bg-primary-500/20 selection:text-primary-700">
      <SEO 
        title="JobHuntin: AI Auto-Applies to Jobs | Beat Sorce with Bot Powers"
        description="Upload resume once. AI applies to 100s of jobs daily. Marketing, Sales, Admin & more. Denver focus."
        ogTitle="JobHuntin: AI Auto-Applies to Jobs | Beat Sorce with Bot Powers"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "Is this legit? Will I get banned from job sites?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications."
              }
            },
            {
              "@type": "Question",
              "name": "How is this different from just applying myself?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter using AI."
              }
            },
            {
              "@type": "Question",
              "name": "What happens to my resume and data?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime."
              }
            }
          ]
        }}
      />
      <ProgressBar />
      <main>
        <Hero />
        <Onboarding />
        <AutomationEdge />
      </main>
    </div>
  );
}
