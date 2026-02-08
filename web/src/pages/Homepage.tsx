/* 
 * DEPLOYMENT INSTRUCTIONS (Vercel/Netlify):
 * 1. Ensure package.json has: "framer-motion", "lucide-react", "canvas-confetti", "react-hook-form".
 * 2. Run: `npm install`
 * 3. Build: `npm run build` (Vite) or `next build` (Next.js)
 * 4. Output directory: `dist` (Vite) or `.next` (Next.js)
 * 5. Environment Variables:
 *    - VITE_GA_ID=G-XXXXXXXXXX
 *    - VITE_HOTJAR_ID=XXXXXXX
 */

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { motion, useScroll, useSpring, useMotionValue, useTransform, AnimatePresence, useMotionTemplate } from 'framer-motion';
import { useForm } from 'react-hook-form';
import confetti from 'canvas-confetti';
import { 
  Rocket, Sparkles, Bot, Zap, CheckCircle, ArrowRight, UploadCloud, 
  Search, Code, X, Github, Gamepad2, Globe, 
  Volume2, VolumeX, MousePointer2, QrCode, Smartphone, Menu,
  MailCheck
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { Link, useNavigate } from 'react-router-dom';

import { SEO } from '../components/marketing/SEO';

const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const MISSING_API_BASE = !API_BASE;

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- DATA ---
const JOBS_DATA = [
  { id: 1, title: "Marketing Manager", company: "Growth Co", score: 97, salary: "$85k", location: "Denver, CO", tags: ["Strategy", "Campaigns", "Social"], color: "bg-yellow-100 text-yellow-800" },
  { id: 2, title: "Customer Success Lead", company: "Service First", score: 94, salary: "$78k", remote: true, tags: ["Client Relations", "Support", "Onboarding"], color: "bg-pink-100 text-pink-800" },
  { id: 3, title: "Operations Coordinator", company: "Logistics Inc", score: 91, salary: "$62k", location: "Boulder", tags: ["Logistics", "Scheduling", "Coordination"], color: "bg-blue-100 text-blue-800" },
  { id: 4, title: "Sales Representative", company: "Tech Solutions", score: 89, salary: "$92k", remote: true, tags: ["B2B", "Sales", "CRM"], color: "bg-indigo-100 text-indigo-800" },
  { id: 5, title: "Project Manager", company: "Build It", score: 95, salary: "$110k", location: "Denver Tech Center", tags: ["Agile", "Planning", "Leadership"], color: "bg-gray-100 text-gray-800" },
  { id: 6, title: "Executive Assistant", company: "Global Corp", score: 93, salary: "$75k", equity: true, tags: ["Admin", "Organization", "Travel"], color: "bg-green-100 text-green-800" },
];

const TEASER_JOBS = [
  { id: "t1", title: "Marketing Lead", status: "AI Applied 2m ago" },
  { id: "t2", title: "Sales Manager", status: "Matching..." },
  { id: "t3", title: "Operations Dir", status: "Interview Request!" },
];

// --- SOUND UTILS ---
const playHoverSound = (muted: boolean) => {
  if (muted) return;
  const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.type = 'sine';
  osc.frequency.setValueAtTime(400, ctx.currentTime);
  osc.frequency.exponentialRampToValueAtTime(800, ctx.currentTime + 0.1);
  gain.gain.setValueAtTime(0.05, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
  osc.start();
  osc.stop(ctx.currentTime + 0.1);
};

const playSuccessSound = (muted: boolean) => {
  if (muted) return;
  const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.type = 'triangle';
  osc.frequency.setValueAtTime(500, ctx.currentTime);
  osc.frequency.linearRampToValueAtTime(1000, ctx.currentTime + 0.1);
  gain.gain.setValueAtTime(0.1, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 0.3);
  osc.start();
  osc.stop(ctx.currentTime + 0.3);
};

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
            className="flex items-center gap-2 text-xs text-gray-500"
          >
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="font-medium text-gray-700">{activity.text}</span>
            <span className="text-gray-400 opacity-60">{activity.time}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// 2. Custom Cursor
const CustomCursor = () => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();
  
  useEffect(() => {
    const moveCursor = (e: MouseEvent) => {
      if (cursorRef.current) {
        cursorRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0)`;
      }
    };
    window.addEventListener('mousemove', moveCursor);
    return () => window.removeEventListener('mousemove', moveCursor);
  }, []);

  return (
    <div 
      ref={cursorRef} 
      className="fixed top-0 left-0 w-8 h-8 pointer-events-none z-[100] hidden lg:block -mt-4 -ml-4 will-change-transform"
    >
      <Bot className="w-8 h-8 text-[#FF6B35] drop-shadow-glow" />
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
    <div className="fixed top-0 left-0 right-0 h-2 bg-gray-100 z-[60]">
      <motion.div
        className="h-full bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]"
        style={{ scaleX, transformOrigin: "0%" }}
      />
      <div className="absolute top-3 right-4 bg-black/80 text-white text-xs px-2 py-1 rounded backdrop-blur-sm hidden sm:block">
        AI Hunt Progress
      </div>
    </div>
  );
};

// 5. Exit Intent Popup
const ExitIntentPopup = () => {
  const [show, setShow] = useState(false);
  const [timeLeft, setTimeLeft] = useState(180); // 3 minutes
  const [email, setEmail] = useState("");

  useEffect(() => {
    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0 && !localStorage.getItem('jobhunt_exit_dismissed')) {
        setShow(true);
      }
    };
    document.addEventListener('mouseleave', handleMouseLeave);
    return () => document.removeEventListener('mouseleave', handleMouseLeave);
  }, []);

  useEffect(() => {
    if (show && timeLeft > 0) {
      const timer = setInterval(() => setTimeLeft(t => t - 1), 1000);
      return () => clearInterval(timer);
    }
  }, [show, timeLeft]);

  const closePopup = () => {
    setShow(false);
    localStorage.setItem('jobhunt_exit_dismissed', 'true');
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        >
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white rounded-2xl p-8 max-w-md w-full relative overflow-hidden shadow-2xl"
          >
            <button onClick={closePopup} className="absolute top-4 right-4 text-gray-400 hover:text-gray-900">
              <X />
            </button>
            
            <div className="absolute top-0 left-0 right-0 h-1 bg-gray-100">
              <motion.div 
                className="h-full bg-red-500" 
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: 180, ease: "linear" }}
              />
            </div>

            <div className="text-center mb-6 mt-2">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-[#FF6B35] animate-bounce" />
              </div>
              <h3 className="text-2xl font-bold font-poppins mb-2">Wait! Don't miss out.</h3>
              <p className="text-gray-600">
                We found <span className="font-bold text-[#FF6B35]">47 Denver matches</span> for your profile. 
                Matches expire in {formatTime(timeLeft)}.
              </p>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); closePopup(); }} className="space-y-4">
              <input 
                type="email" 
                placeholder="Save matches to email..." 
                className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#FF6B35] focus:border-transparent outline-none"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
              <button className="w-full bg-[#FF6B35] text-white py-3 rounded-xl font-bold hover:bg-[#e05a2b] transition-colors shadow-lg shadow-orange-500/30">
                Save My 47 Matches
              </button>
            </form>
            
            <p className="text-xs text-center text-gray-400 mt-4">No spam. Only job offers.</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// 6. Navigation
const Navbar = ({ muted, toggleMute }: { muted: boolean, toggleMute: () => void }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-4 md:px-6 py-4",
      isScrolled ? "bg-white/80 backdrop-blur-md shadow-sm" : "bg-transparent"
    )}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-[#FF6B35] p-2 rounded-xl rotate-3 shadow-glow">
            <Bot className="text-white w-6 h-6" />
          </div>
          <span className="text-xl font-bold font-poppins text-gray-900 tracking-tight">JobHuntin</span>
        </div>
        
        <div className="hidden md:flex items-center gap-8 font-medium text-gray-600">
          <a href="#how-it-works" className="hover:text-[#FF6B35] transition-colors" onMouseEnter={() => playHoverSound(muted)}>How it Works</a>
          <a href="#jobs" className="hover:text-[#FF6B35] transition-colors" onMouseEnter={() => playHoverSound(muted)}>Live Jobs</a>
          <a href="#comparison" className="hover:text-[#FF6B35] transition-colors" onMouseEnter={() => playHoverSound(muted)}>Vs Sorce</a>
          <button 
            onClick={toggleMute}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors text-gray-500"
            title={muted ? "Unmute sounds" : "Mute sounds"}
          >
            {muted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
          </button>
          <button 
            onClick={() => navigate('/login')}
            className="bg-[#2D2D2D] text-white px-6 py-2 rounded-full font-bold hover:bg-[#FF6B35] transition-colors transform hover:scale-105 active:scale-95"
            onMouseEnter={() => playHoverSound(muted)}
          >
            Login
          </button>
        </div>

        <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-full left-0 right-0 bg-white border-b shadow-lg p-6 flex flex-col gap-4 md:hidden"
          >
            <a href="#how-it-works" className="text-lg font-medium">How it Works</a>
            <a href="#jobs" className="text-lg font-medium">Live Jobs</a>
            <a href="#comparison" className="text-lg font-medium">Vs Sorce</a>
            <button 
              onClick={() => navigate('/login')}
              className="bg-[#FF6B35] text-white w-full py-3 rounded-xl font-bold"
            >
              Login
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

// 7. Hero Section (A/B Test Variant)
const Hero = ({ muted }: { muted: boolean }) => {
  const [variant, setVariant] = useState<'swipe' | 'magic'>('magic');
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [matchCount, setMatchCount] = useState(0);
  const [jobs, setJobs] = useState(TEASER_JOBS);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const autoDismissTimer = useRef<number | null>(null);

  // Background Particles Data - Refined for a more artistic look
  const particles = React.useMemo(() => {
    return [...Array(25)].map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: i < 5 ? Math.random() * 150 + 100 : Math.random() * 40 + 10, // Mix of large blobs and small dots
      duration: Math.random() * 20 + 20,
      delay: Math.random() * 10,
      yMove: (Math.random() - 0.5) * 150,
      xMove: (Math.random() - 0.5) * 150,
      rotate: Math.random() * 360,
      color: i % 3 === 0 ? 'rgba(255, 107, 53, 0.15)' : i % 3 === 1 ? 'rgba(74, 144, 226, 0.15)' : 'rgba(250, 249, 246, 0.3)',
      blur: i < 5 ? 'blur(60px)' : 'none'
    }));
  }, []);
  
  // A/B Test Logic
  useEffect(() => {
    try {
      const stored = window?.localStorage?.getItem('jobhunt_ab_test');
      if (stored) {
        setVariant(stored as 'swipe' | 'magic');
      } else {
        const v = Math.random() > 0.5 ? 'swipe' : 'magic';
        setVariant(v);
        window?.localStorage?.setItem('jobhunt_ab_test', v);
      }
    } catch (err) {
      console.warn('A/B storage disabled, falling back to default variant', err);
      setVariant('magic');
    }
  }, []);

  useEffect(() => {
    return () => {
      if (autoDismissTimer.current) {
        window.clearTimeout(autoDismissTimer.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!sentEmail) {
      if (autoDismissTimer.current) {
        window.clearTimeout(autoDismissTimer.current);
      }
      return;
    }
    autoDismissTimer.current = window.setTimeout(() => {
      setSentEmail(null);
    }, 90_000);
    return () => {
      if (autoDismissTimer.current) {
        window.clearTimeout(autoDismissTimer.current);
      }
    };
  }, [sentEmail]);

  // Mouse Glow
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  const validateEmail = (e: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      setEmailError("Robot says: Need a valid email! 🤖");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);
    setMatchCount(0);

    // Call API
    try {
      if (!API_BASE) {
        throw new Error("Missing API URL. Please set VITE_API_URL (e.g. https://api.jobhuntin.com).");
      }

      const normalizedEmail = email.trim().toLowerCase();
      const returnUrl = `${window.location.origin}/app/onboarding`;
      const resp = await fetch(`${API_BASE}/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: normalizedEmail,
          return_to: returnUrl,
        }),
      });

      if (!resp.ok) {
        let bodyText = await resp.text();
        let bodyJson: any = null;
        try {
          bodyJson = JSON.parse(bodyText || '{}');
        } catch (_) {
          // ignore JSON parse errors
        }

        const apiMessage = bodyJson?.error || bodyJson?.message;
        const message = resp.status === 429
          ? "You've hit the limit for magic links. Please wait a bit before trying again."
          : `Magic link failed (${resp.status}): ${apiMessage || bodyText || 'Unknown error'}`;

        console.error('[magic-link] failure', {
          status: resp.status,
          statusText: resp.statusText,
          bodyText,
          bodyJson,
          email: normalizedEmail,
          returnUrl,
        });

        throw new Error(message);
      }

      if (typeof window !== 'undefined') {
        let start = 0;
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

      playSuccessSound(muted);
      confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#FF6B35', '#4A90E2', '#FAF9F6']
      });
      pushToast({ title: "Magic Link Sent! 📧", description: "Check your email to start hunting.", tone: "success" });
      setSentEmail(normalizedEmail);
      setEmail(""); // Clear
      setIsSubmitting(false);

    } catch (err: any) {
      setIsSubmitting(false);
      setSentEmail(null);
      const message = err?.message || "Failed to send magic link";
      console.error('[magic-link] unexpected error', err);
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
    <section className="relative min-h-screen pt-24 pb-12 flex items-center justify-center overflow-hidden bg-[#FAF9F6]">
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

      <div className="container mx-auto px-4 md:px-6 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        {/* Left Content */}
        <div className="text-center lg:text-left">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm mb-6 border border-orange-100"
          >
            <Sparkles className="w-4 h-4 text-[#FF6B35]" />
            <span className="text-sm font-semibold text-gray-600">
              {variant === 'magic' ? "AI Hunts Jobs For You" : "Stop Swiping Manually"}
            </span>
          </motion.div>

          <h1 className="text-5xl sm:text-6xl lg:text-8xl font-black font-poppins text-[#2D2D2D] leading-[0.9] mb-8 tracking-tighter">
            Hunt Jobs with <br />
            <span className="relative inline-block mt-2">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] via-[#FF8B55] to-[#4A90E2] animate-gradient-x">
                AI Magic
              </span>
              <motion.span 
                className="absolute -top-4 -right-10 text-4xl sm:text-5xl pointer-events-none"
                animate={{ 
                  rotate: [0, 15, -15, 0],
                  scale: [1, 1.2, 1],
                  filter: ["drop-shadow(0 0 0px rgba(255,107,53,0))", "drop-shadow(0 0 20px rgba(255,107,53,0.5))", "drop-shadow(0 0 0px rgba(255,107,53,0))"]
                }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
              >
                ✨
              </motion.span>
            </span>
          </h1>

          <p className="text-xl sm:text-2xl text-gray-500 mb-10 max-w-lg mx-auto lg:mx-0 leading-tight font-medium">
            Upload once. AI swipes & applies to 100s of jobs while you sleep. 
            <span className="text-[#2D2D2D] border-b-2 border-[#FF6B35]/30"> Beats Sorce.jobs</span> on every metric.
          </p>

          {MISSING_API_BASE && (
            <div className="mb-4 max-w-md mx-auto lg:mx-0 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <div className="mt-0.5">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <div>
                <p className="font-semibold">API URL not configured</p>
                <p>Set <code>VITE_API_URL</code> (e.g. https://api.jobhuntin.com) so the Start Hunt button can send magic links.</p>
              </div>
            </div>
          )}

          {!sentEmail && (
          <div 
            className="group relative max-w-md mx-auto lg:mx-0 p-1 rounded-2xl bg-gradient-to-r from-[#FF6B35] to-[#4A90E2] transition-transform hover:scale-[1.01]"
            onMouseMove={handleMouseMove}
          >
            <motion.div
              className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
              style={{
                background: useMotionTemplate`
                  radial-gradient(
                    650px circle at ${mouseX}px ${mouseY}px,
                    rgba(255, 255, 255, 0.4),
                    transparent 40%
                  )
                `,
              }}
            />
            <form onSubmit={onSubmit} className="bg-white rounded-xl p-2 flex flex-col sm:flex-row gap-2 relative z-10">
              <div className="flex-1">
                <input 
                  type="email" 
                  placeholder="you@example.com"  
                  className={cn(
                    "w-full px-4 py-3 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 transition-all",
                    emailError ? "ring-2 ring-red-500 bg-red-50" : "focus:ring-[#FF6B35]/20"
                  )}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <button 
                disabled={isSubmitting}
                className="w-full sm:w-auto bg-[#2D2D2D] text-white px-8 py-3 rounded-lg font-bold hover:bg-[#FF6B35] transition-all flex items-center justify-center gap-2 whitespace-nowrap shadow-lg hover:shadow-orange-500/25"
                onMouseEnter={() => playHoverSound(muted)}
              >
                {isSubmitting ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}>
                    <Sparkles className="w-5 h-5" />
                  </motion.div>
                ) : (
                  <>
                    Start Hunt <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
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
              className="mt-4 flex items-center gap-2 justify-center lg:justify-start text-[#FF6B35] font-bold"
            >
              <CheckCircle className="w-5 h-5" />
              Found {matchCount} Denver matches!
            </motion.div>
          )}

          {/* Live Activity Feed */}
          <div className="mt-8 relative h-12 overflow-hidden max-w-sm mx-auto lg:mx-0">
             <div className="absolute inset-0 bg-gradient-to-b from-[#FAF9F6] via-transparent to-[#FAF9F6] z-10 pointer-events-none" />
             <ActivityFeed />
          </div>

          {sentEmail && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 bg-white border border-gray-100 rounded-2xl p-5 shadow-lg text-left"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-[#FF6B35]/10 flex items-center justify-center">
                  <MailCheck className="w-5 h-5 text-[#FF6B35]" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-400 font-semibold">Magic link en route</p>
                  <p className="text-base font-semibold text-[#2D2D2D]">Sent to {sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Look for an email from <span className="font-semibold">noreply@jobhuntin.com</span> (delivered via Resend). When you tap the link we’ll drop you straight into onboarding.
              </p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
                <li>Open the inbox (or spam folder) for {sentEmail}.</li>
                <li>Find the message titled <em>“Start your JobHuntin run”</em> and press the button.</li>
                <li>Keep this tab open—onboarding launches as soon as the link opens.</li>
              </ol>
              <div className="flex flex-wrap gap-3 mt-4">
                <button
                  type="button"
                  onClick={() => setSentEmail(null)}
                  className="text-sm font-semibold text-[#FF6B35] hover:underline"
                >
                  Use a different email
                </button>
                <a
                  href="mailto:support@jobhuntin.com"
                  className="text-sm text-gray-500 hover:text-[#2D2D2D]"
                >
                  Need help? support@jobhuntin.com
                </a>
              </div>
            </motion.div>
          )}

          <div className="mt-8 flex items-center justify-center lg:justify-start gap-4 text-sm text-gray-500">
            <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center animate-bounce-slow">
              <UploadCloud className="w-6 h-6 text-[#FF6B35]" />
            </div>
            <p className="leading-tight">
              <span className="font-bold text-gray-900">Drag & Drop Resume</span><br/>
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
                className="absolute w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6 border border-gray-100 cursor-grab active:cursor-grabbing touch-pan-y"
                style={{ zIndex: jobs.length - index }}
                initial={{ scale: 0.9, y: 50 * index, opacity: 1 - index * 0.3 }}
                animate={{ scale: 1 - index * 0.05, y: 20 * index, opacity: 1 - index * 0.2 }}
                exit={{ x: 200, opacity: 0, rotate: 20 }}
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                onDragEnd={(_, info) => {
                  if (info.offset.x > 100 || info.offset.x < -100) {
                    removeJob(index);
                    playSuccessSound(muted);
                  }
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-[#4A90E2]" />
                  </div>
                  <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold">
                    98% Match
                  </span>
                </div>
                <h3 className="text-xl font-bold text-gray-900">{job.title}</h3>
                <p className="text-gray-500 mb-4">{job.status}</p>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-[#FF6B35]" 
                    initial={{ width: 0 }}
                    animate={{ width: "98%" }}
                    transition={{ duration: 1.5, delay: 0.5 }}
                  />
                </div>
                <p className="text-xs text-right mt-1 text-gray-400">AI Analysis Complete</p>
              </motion.div>
            ))}
          </AnimatePresence>
          
          <motion.div 
            className="absolute bottom-4 sm:bottom-10 right-10 text-gray-400 flex items-center gap-2 pointer-events-none bg-white/50 backdrop-blur px-2 py-1 rounded"
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
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const end = 247;
    const interval = setInterval(() => {
      start += 3;
      if (start >= end) {
        start = end;
        clearInterval(interval);
      }
      setCount(start);
    }, 20);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="how-it-works" className="py-32 bg-white relative overflow-hidden">
      {/* Subtle Background Art */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-gray-50 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-24 items-center">
          <div className="relative group">
             <motion.div 
               className="aspect-square bg-gray-50 rounded-[3rem] flex items-center justify-center relative z-10 overflow-hidden shadow-inner"
               initial={{ scale: 0.9, opacity: 0 }}
               whileInView={{ scale: 1, opacity: 1 }}
               viewport={{ once: true }}
             >
                <Bot className="w-48 h-48 text-gray-200 group-hover:text-[#FF6B35]/20 transition-colors duration-700" />
                
                {/* Scanner Animation */}
                <motion.div 
                  className="absolute inset-0 bg-gradient-to-b from-transparent via-[#FF6B35]/10 to-transparent w-full h-20"
                  animate={{ top: ["-20%", "100%", "-20%"] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                />

                {/* Particle Overlay */}
                <div className="absolute inset-0 opacity-30">
                  {[...Array(10)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="absolute w-1 h-1 bg-[#FF6B35] rounded-full"
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
             <div className="absolute -top-12 -left-12 w-48 h-48 bg-[#FF6B35]/5 rounded-full blur-3xl" />
             <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-[#4A90E2]/5 rounded-full blur-3xl" />
          </div>

          <div>
            <div className="inline-block bg-[#FF6B35]/10 text-[#FF6B35] px-4 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] mb-6">
              The Protocol
            </div>
            <h2 className="text-5xl sm:text-6xl font-black font-poppins text-[#2D2D2D] leading-[1.1] mb-12 tracking-tighter">
              One Click. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2]">Infinite Reach.</span>
            </h2>
            <div className="space-y-12">
              {[
                { icon: Code, title: "Deep Profile Ingestion", desc: "Our AI doesn't just read your resume. It parses your GitHub, projects, and latent skills to build a high-dimensional match vector." },
                { icon: Zap, title: "Precision Filtering", desc: "Skip the noise. We match you with roles that actually align with your trajectory, filtering out the legacy tech and low-growth traps." },
                { icon: Rocket, title: "Autonomous Submission", desc: "Every application is unique. Custom-tailored cover letters and optimized form-filling happen in milliseconds, not minutes." }
              ].map((step, i) => (
                <motion.div 
                  key={i}
                  className="flex gap-8 group"
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center flex-shrink-0 group-hover:bg-[#FF6B35] group-hover:rotate-6 transition-all duration-500 shadow-sm group-hover:shadow-orange-500/20">
                    <step.icon className="w-8 h-8 text-[#FF6B35] group-hover:text-white transition-colors" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-[#2D2D2D] mb-2 tracking-tight">{step.title}</h3>
                    <p className="text-gray-500 text-lg leading-relaxed font-medium">{step.desc}</p>
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

// 9. Featured Jobs with Live Demo
const FeaturedJobs = ({ muted }: { muted: boolean }) => {
  return (
    <section id="jobs" className="py-24 bg-[#FAF9F6]">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold font-poppins mb-4">Fresh Hunts</h2>
          <p className="text-gray-600">AI is currently applying to these roles for users like you.</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {JOBS_DATA.map((job, i) => (
            <motion.div
              key={job.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              whileHover={{ y: -5, scale: 1.02 }}
              onMouseEnter={() => playHoverSound(muted)}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 group relative overflow-hidden"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-xl font-bold text-gray-400">
                  {job.company[0]}
                </div>
                <div className="flex items-center gap-1 text-[#FF6B35] font-bold text-sm">
                  <Sparkles className="w-3 h-3" />
                  {job.score}% Match
                </div>
              </div>
              
              <h3 className="text-xl font-bold text-gray-900 mb-1">{job.title}</h3>
              <p className="text-[#4A90E2] font-medium mb-4">{job.company}</p>
              
              <div className="flex flex-wrap gap-2 mb-6">
                <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 font-medium">{job.salary}</span>
                {job.remote && <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 font-medium">Remote</span>}
                {job.location && <span className="px-2 py-1 bg-gray-100 rounded text-xs text-gray-600 font-medium">{job.location}</span>}
              </div>

              <div className="flex gap-2 mb-6 flex-wrap">
                {job.tags.map(tag => (
                  <span key={tag} className={`text-[10px] px-2 py-1 rounded-full ${job.color} bg-opacity-20`}>
                    {tag}
                  </span>
                ))}
              </div>

              <button className="w-full py-3 rounded-xl border-2 border-[#FF6B35] text-[#FF6B35] font-bold group-hover:bg-[#FF6B35] group-hover:text-white transition-all flex items-center justify-center gap-2">
                <Bot className="w-4 h-4" />
                One-Click Apply
              </button>
            </motion.div>
          ))}
        </div>

        {/* Live Bot Demo */}
        <div className="mt-20 max-w-4xl mx-auto bg-gray-900 rounded-3xl p-8 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#4A90E2]/20 rounded-full blur-3xl" />
          <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
            <div className="flex-1">
              <h3 className="text-2xl font-bold mb-4">See It In Action</h3>
              <p className="text-gray-400 mb-6">Connect your profile. We'll simulate how our AI pitches your skills to recruiters.</p>
              <button className="bg-[#4A90E2] hover:bg-[#357abd] text-white px-6 py-3 rounded-xl font-bold transition-colors flex items-center gap-2">
                <Rocket className="w-5 h-5" /> Test My Profile
              </button>
            </div>
            <div className="w-full md:w-1/2 bg-gray-800 rounded-xl p-4 h-64 overflow-hidden relative border border-gray-700">
               <div className="absolute top-2 left-4 text-xs text-gray-500 font-mono">Simulating Recruiter View...</div>
               <div className="mt-6 space-y-3">
                 {[1,2,3].map((_, i) => (
                   <motion.div 
                     key={i}
                     initial={{ x: 100, opacity: 0 }}
                     animate={{ x: 0, opacity: 1 }}
                     transition={{ delay: i * 1.5, repeat: Infinity, repeatDelay: 5 }}
                     className="bg-gray-700 p-3 rounded-lg flex items-center gap-3"
                   >
                     <div className="w-8 h-8 bg-gray-600 rounded-full" />
                     <div className="flex-1">
                       <div className="h-2 w-20 bg-gray-500 rounded mb-1" />
                       <div className="h-2 w-32 bg-gray-600 rounded" />
                     </div>
                     <CheckCircle className="w-4 h-4 text-green-400" />
                   </motion.div>
                 ))}
               </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// 10. Automation Edge & Telegram
const AutomationEdge = ({ muted }: { muted: boolean }) => {
  return (
    <section className="py-24 bg-white overflow-hidden">
      <div className="container mx-auto px-6 relative">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-block bg-blue-50 px-4 py-1 rounded-full text-sm font-mono text-[#4A90E2] mb-6">
            New: Control via Telegram
          </div>
          <h2 className="text-4xl font-bold font-poppins mb-6">Control the Hunt via Telegram</h2>
          <p className="text-gray-600 text-lg mb-10">
            Get instant notifications when AI lands you an interview. Approve applications with one tap.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <button 
              className="bg-[#0088cc] text-white px-8 py-4 rounded-2xl font-bold hover:bg-[#0077b5] transition-colors flex items-center gap-3 shadow-lg shadow-blue-500/30"
              onMouseEnter={() => playHoverSound(muted)}
            >
              <Smartphone className="w-6 h-6" />
              Add JobHuntin Bot
            </button>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <QrCode className="w-4 h-4" />
              <span>or scan QR code</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// 11. Comparison Slider (removed)

// 12. Footer with Easter Egg
const Footer = ({ muted }: { muted: boolean }) => {
  const [showEasterEgg, setShowEasterEgg] = useState(false);

  const handleScroll = () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 50) {
      setShowEasterEgg(true);
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <footer className="bg-white pt-24 pb-12 border-t border-gray-200 relative overflow-hidden">
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-6">
               <div className="bg-[#FF6B35] p-2 rounded-lg">
                <Bot className="text-white w-5 h-5" />
              </div>
              <span className="text-xl font-bold font-poppins">JobHuntin</span>
            </div>
            <p className="text-gray-500 mb-6 max-w-sm">
              The AI agent that applies to jobs for you. Built for job seekers, by engineers.
              Stop grinding, start interviewing.
            </p>
            <div className="flex gap-4">
              <a href="https://github.com/jobhuntin" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" aria-label="JobHuntin GitHub" onMouseEnter={() => playHoverSound(muted)}>
                <Github className="w-5 h-5" />
              </a>
              <a href="https://twitter.com/jobhuntin" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" aria-label="JobHuntin Twitter" onMouseEnter={() => playHoverSound(muted)}>
                <Gamepad2 className="w-5 h-5" />
              </a>
              <a href="https://jobhuntin.com" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" aria-label="JobHuntin Website" onMouseEnter={() => playHoverSound(muted)}>
                <Globe className="w-5 h-5" />
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="font-bold text-gray-900 mb-6">Platform</h4>
            <ul className="space-y-3 text-gray-500">
              <li>
                <Link to="/pricing" className="hover:text-[#FF6B35] transition-colors">Pricing</Link>
              </li>
              <li>
                <Link to="/success-stories" className="hover:text-[#FF6B35] transition-colors">Success Stories</Link>
              </li>
              <li>
                <Link to="/chrome-extension" className="hover:text-[#FF6B35] transition-colors">Chrome Extension</Link>
              </li>
              <li>
                <Link to="/recruiters" className="hover:text-[#FF6B35] transition-colors">For Recruiters</Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-gray-900 mb-6">Directory</h4>
            <ul className="space-y-3 text-gray-500">
              <li>
                <Link to="/guides" className="hover:text-[#FF6B35] transition-colors">Job Search Guides</Link>
              </li>
              <li>
                <Link to="/vs/sorce" className="hover:text-[#FF6B35] transition-colors">Compare Alternatives</Link>
              </li>
              <li>
                <Link to="/jobs/marketing-manager/denver" className="hover:text-[#FF6B35] transition-colors">Denver Jobs</Link>
              </li>
              <li>
                <Link to="/jobs/software-engineer/remote" className="hover:text-[#FF6B35] transition-colors">Remote Roles</Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-gray-900 mb-6">Join the Hunt</h4>
            <p className="text-sm text-gray-500 mb-4">Get the weekly drop of stealth-mode jobs.</p>
            <div className="flex gap-2">
              <input type="email" placeholder="Email" className="px-4 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm w-full focus:outline-none focus:ring-1 focus:ring-[#FF6B35]" />
              <button className="bg-[#2D2D2D] text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-[#FF6B35] transition-colors">Join</button>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-200 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-gray-400">
          <p>&copy; 2026 JobHuntin AI. All rights reserved.</p>
          <div className="flex gap-6 mt-4 md:mt-0">
            <Link to="/privacy" className="hover:text-[#FF6B35]">Privacy</Link>
            <Link to="/terms" className="hover:text-[#FF6B35]">Terms</Link>
            <a href="/sitemap.xml" className="hover:text-[#FF6B35]">Sitemap</a>
          </div>
        </div>
      </div>

      {/* Denver Skyline Easter Egg */}
      {showEasterEgg && (
        <motion.div 
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none opacity-20"
          style={{ 
            backgroundImage: "url('https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Denver_skyline_silhouette.svg/2560px-Denver_skyline_silhouette.svg.png')",
            backgroundSize: "cover",
            backgroundPosition: "bottom"
          }}
        >
          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-xs font-mono text-[#FF6B35]">
            5280ft above boring job sites
          </div>
        </motion.div>
      )}
    </footer>
  );
};

// --- MAIN PAGE ---
export default function Homepage() {
  const [muted, setMuted] = useState(false);

  return (
    <div className="min-h-screen bg-[#FAF9F6] font-inter text-[#2D2D2D] overflow-x-hidden selection:bg-[#FF6B35] selection:text-white cursor-none sm:cursor-auto">
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
      <CustomCursor />
      <ProgressBar />
      <Navbar muted={muted} toggleMute={() => setMuted(!muted)} />
      <main>
        <Hero muted={muted} />
        <Onboarding />
        <FeaturedJobs muted={muted} />
        <AutomationEdge muted={muted} />
      </main>
      <Footer muted={muted} />
      <ExitIntentPopup />
    </div>
  );
}
