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
  Search, Code, X, Github, Gamepad2, Globe, MapPin, 
  Volume2, VolumeX, MousePointer2, QrCode, Smartphone, Menu
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- DATA ---
const JOBS_DATA = [
  { id: 1, title: "Snapchat Automation Engineer", company: "Snap", score: 97, salary: "$165k", location: "Denver, CO", tags: ["Python", "SnapKit", "Appium"], color: "bg-yellow-100 text-yellow-800" },
  { id: 2, title: "Tinder Bot AI Specialist", company: "Match Group", score: 94, salary: "$178k", remote: true, tags: ["TensorFlow", "Computer Vision", "Automation"], color: "bg-pink-100 text-pink-800" },
  { id: 3, title: "OnlyFans Automation Architect", company: "Creator Platform", score: 91, salary: "$192k", location: "Boulder", tags: ["Node.js", "Payment APIs", "Scale"], color: "bg-blue-100 text-blue-800" },
  { id: 4, title: "Discord Bot DevOps", company: "Gaming Studio", score: 89, salary: "$142k", remote: true, tags: ["Go", "Discord.js", "Kubernetes"], color: "bg-indigo-100 text-indigo-800" },
  { id: 5, title: "TikTok Automation Lead", company: "ByteDance", score: 95, salary: "$210k", location: "Denver Tech Center", tags: ["Video Processing", "AI", "Mobile"], color: "bg-gray-100 text-gray-800" },
  { id: 6, title: "AI Resume Generator Dev", company: "Your Next Gig", score: 93, salary: "$155k", equity: true, tags: ["LLM", "OpenAI", "React"], color: "bg-green-100 text-green-800" },
];

const TEASER_JOBS = [
  { title: "Snapchat Auto-Dev", status: "AI Applied 2m ago" },
  { title: "Tinder Algorithm Eng", status: "Matching..." },
  { title: "Discord Bot Ninja", status: "Interview Request!" },
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

// 1. SEO & Head
const HeadSEO = () => {
  useEffect(() => {
    document.title = "JobHuntin: AI Auto-Applies to Jobs | Beat Sorce with Bot Powers";
    
    const updateMeta = (name: string, content: string) => {
      let el = document.querySelector(`meta[name="${name}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute('name', name);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content);
    };

    updateMeta("description", "Upload resume once. AI swipes 100s of tech jobs daily. Snapchat/Tinder bot devs get 92% match rate. Denver focus.");
    updateMeta("og:title", "JobHuntin: AI Auto-Applies to Jobs");
    updateMeta("og:description", "Beat Sorce.jobs with automation. Upload resume, we swipe and apply.");
    updateMeta("og:type", "website");
    updateMeta("og:url", "https://jobhuntin.com");
    updateMeta("theme-color", "#FF6B35");

    // Dynamic OG Image
    // Uses the new Python API endpoint to generate a branded card
    // Default fallback if no params provided
    const ogUrl = new URL("https://sorce-web.onrender.com/api/og"); // Adjust domain if needed
    ogUrl.searchParams.set("job", "AI Job Hunter");
    ogUrl.searchParams.set("company", "JobHuntin");
    ogUrl.searchParams.set("score", "100");
    ogUrl.searchParams.set("location", "Global");
    
    updateMeta("og:image", ogUrl.toString());
    updateMeta("twitter:card", "summary_large_image");
    updateMeta("twitter:image", ogUrl.toString());

    // Canonical
    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', 'https://jobhuntin.com');

    // Schema
    const script = document.createElement('script');
    script.type = "application/ld+json";
    script.text = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "JobHuntin",
      "url": "https://jobhuntin.com",
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://jobhuntin.com/search?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    });
    document.head.appendChild(script);

    // Mock GA4/Hotjar
    console.log("GA4 & Hotjar scripts initialized (mock)");

    return () => {
      document.head.removeChild(script);
    };
  }, []);
  return null;
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
      className="fixed top-0 left-0 w-8 h-8 pointer-events-none z-[100] hidden lg:block -mt-4 -ml-4 transition-transform duration-75 ease-out will-change-transform"
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

// 4. Social Proof Pulse
const SocialProofPulse = () => {
  const [count, setCount] = useState(1247);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setCount(prev => prev + Math.floor(Math.random() * 3));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-6 left-6 z-40 flex flex-col gap-2 pointer-events-none">
      <motion.div 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="bg-white/90 backdrop-blur border border-gray-200 shadow-lg rounded-full px-4 py-2 flex items-center gap-2 text-sm font-medium text-gray-700 pointer-events-auto"
      >
        <div className="relative">
          <div className="w-2 h-2 bg-green-500 rounded-full" />
          <div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-ping" />
        </div>
        {count.toLocaleString()} Hunters Active
      </motion.div>
      <motion.div 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-white/90 backdrop-blur border border-gray-200 shadow-lg rounded-full px-4 py-2 flex items-center gap-2 text-xs font-medium text-gray-500 pointer-events-auto"
      >
        <MapPin className="w-3 h-3 text-[#FF6B35]" />
        Denver: 324 Online
      </motion.div>
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
            <button className="bg-[#FF6B35] text-white w-full py-3 rounded-xl font-bold">
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
  
  // A/B Test Logic
  useEffect(() => {
    const stored = localStorage.getItem('jobhunt_ab_test');
    if (stored) {
      setVariant(stored as 'swipe' | 'magic');
    } else {
      const v = Math.random() > 0.5 ? 'swipe' : 'magic';
      setVariant(v);
      localStorage.setItem('jobhunt_ab_test', v);
    }
  }, []);

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

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmail(email)) {
      setEmailError("Robot says: Need a valid email! 🤖");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    playSuccessSound(muted);
    
    setTimeout(() => {
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
        } else {
          setIsSubmitting(false);
          confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#FF6B35', '#4A90E2', '#FAF9F6']
          });
        }
      };
      requestAnimationFrame(animateCounter);
    }, 1500);
  };

  const removeJob = (index: number) => {
    setJobs(prev => prev.filter((_, i) => i !== index));
    setTimeout(() => {
      setJobs(prev => [...prev, { title: "New Match Found!", status: "Analyzing..." }]);
    }, 500);
  };

  return (
    <section className="relative min-h-screen pt-24 pb-12 flex items-center justify-center overflow-hidden bg-[#FAF9F6]">
      {/* Background Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute rounded-full opacity-20"
            initial={{ x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight }}
            animate={{ 
              y: [null, Math.random() * -100],
              x: [null, (Math.random() - 0.5) * 50]
            }}
            transition={{ duration: Math.random() * 10 + 10, repeat: Infinity, ease: "linear" }}
            style={{
              width: Math.random() * 50 + 10,
              height: Math.random() * 50 + 10,
              background: i % 2 === 0 ? '#FF6B35' : '#4A90E2'
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

          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold font-poppins text-[#2D2D2D] leading-tight mb-6 tracking-tight">
            Hunt Jobs with <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FF6B35] to-[#4A90E2] relative inline-block">
              AI Magic
              <motion.span 
                className="absolute -top-2 -right-6 text-2xl sm:text-3xl"
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                ✨
              </motion.span>
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-lg mx-auto lg:mx-0 leading-relaxed">
            Upload your resume. AI swipes & applies to 100s of jobs while you sleep. 
            <span className="font-semibold text-gray-900"> Beats Sorce.jobs</span> for tech pros.
          </p>

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
                  placeholder="tech-wizard@example.com" 
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
                key={job.title + index}
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
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" className="stroke-[#FF6B35] stroke-2 fill-none opacity-30"></path>
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
    <section id="how-it-works" className="py-24 bg-white relative">
      <div className="container mx-auto px-6">
        {/* Local Stat Bar */}
        <div className="bg-gray-900 text-white rounded-2xl p-6 mb-16 flex flex-col md:flex-row items-center justify-between shadow-xl transform -translate-y-12">
          <div className="flex items-center gap-4 mb-4 md:mb-0">
            <MapPin className="text-[#FF6B35] w-8 h-8" />
            <div>
              <p className="text-gray-400 text-sm uppercase tracking-wider">Detected Location</p>
              <h3 className="text-2xl font-bold">Denver Tech Jobs: <span className="text-[#4A90E2]">{count} Open</span></h3>
            </div>
          </div>
          <div className="flex gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-[#FF6B35]">10x</div>
              <div className="text-xs text-gray-400">Faster Apps</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-[#4A90E2]">47%</div>
              <div className="text-xs text-gray-400">Higher Response</div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div className="relative">
             <motion.div 
               className="aspect-square bg-[#FAF9F6] rounded-full flex items-center justify-center relative z-10"
               initial={{ scale: 0.8, opacity: 0 }}
               whileInView={{ scale: 1, opacity: 1 }}
               viewport={{ once: true }}
             >
                <Bot className="w-32 h-32 text-gray-300" />
                <motion.div 
                  className="absolute inset-0 bg-gradient-to-b from-transparent via-[#FF6B35]/20 to-transparent w-full h-8"
                  animate={{ top: ["0%", "100%", "0%"] }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                />
             </motion.div>
             <div className="absolute -top-10 -left-10 w-20 h-20 bg-[#FF6B35]/20 rounded-full blur-xl" />
             <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-[#4A90E2]/20 rounded-full blur-xl" />
          </div>

          <div>
            <h2 className="text-4xl font-bold font-poppins mb-8">One Click.<br/>Infinite Applications.</h2>
            <div className="space-y-8">
              {[
                { icon: Code, title: "AI Reads Your Superpowers", desc: "We analyze your GitHub & Resume to find your edge." },
                { icon: Zap, title: "Swipes 100s of Matches", desc: "Better than Sorce. We filter out spam & mismatch." },
                { icon: Rocket, title: "Auto-Applies Instantly", desc: "Custom cover letters generated for every single role." }
              ].map((step, i) => (
                <motion.div 
                  key={i}
                  className="flex gap-4"
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.2 }}
                  viewport={{ once: true }}
                >
                  <div className="w-12 h-12 bg-gray-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <step.icon className="w-6 h-6 text-[#FF6B35]" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">{step.title}</h3>
                    <p className="text-gray-600">{step.desc}</p>
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
              <h3 className="text-2xl font-bold mb-4">See Your Bot In Action</h3>
              <p className="text-gray-400 mb-6">Connect your GitHub or specific bot repo. We'll simulate how our AI pitches your skills to recruiters.</p>
              <button className="bg-[#4A90E2] hover:bg-[#357abd] text-white px-6 py-3 rounded-xl font-bold transition-colors flex items-center gap-2">
                <Github className="w-5 h-5" /> Test My Snapchat Bot
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
            beta_feature: telegram_bot_v1
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

// 11. Comparison
const Comparison = () => {
  return (
    <section id="comparison" className="py-24 bg-[#FAF9F6]">
      <div className="container mx-auto px-6">
        <h2 className="text-4xl font-bold text-center font-poppins mb-16">Why we crush <span className="line-through text-gray-300">Sorce</span></h2>
        
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
           {/* Sorce Card */}
           <div className="bg-white p-8 rounded-3xl opacity-60 hover:opacity-100 transition-opacity border border-gray-100">
              <h3 className="text-2xl font-bold text-gray-500 mb-6">The Old Way</h3>
              <ul className="space-y-4 text-gray-500">
                <li className="flex items-center gap-3"><X className="w-5 h-5" /> Manual swiping fatigue</li>
                <li className="flex items-center gap-3"><X className="w-5 h-5" /> Generic "Dear Hiring Manager"</li>
                <li className="flex items-center gap-3"><X className="w-5 h-5" /> Limited to 10 apps/day</li>
              </ul>
           </div>

           {/* JobHuntin Card */}
           <div className="bg-gradient-to-br from-[#FF6B35] to-[#FF8F66] p-8 rounded-3xl text-white shadow-xl transform scale-105">
              <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                JobHuntin <Bot className="w-6 h-6" />
              </h3>
              <ul className="space-y-4 font-medium">
                <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5" /> 24/7 Auto-Apply Agent</li>
                <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5" /> Hyper-personalized Cover Letters</li>
                <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5" /> Unlimited Applications</li>
                <li className="flex items-center gap-3"><CheckCircle className="w-5 h-5" /> Undetectable "Stealth Mode"</li>
              </ul>
           </div>
        </div>
      </div>
    </section>
  );
};

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
              The AI agent that applies to jobs for you. Built for engineers, by engineers.
              Stop grinding, start interviewing.
            </p>
            <div className="flex gap-4">
              <a href="#" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" onMouseEnter={() => playHoverSound(muted)}>
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" onMouseEnter={() => playHoverSound(muted)}>
                <Gamepad2 className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 hover:text-[#FF6B35] hover:bg-orange-50 transition-all" onMouseEnter={() => playHoverSound(muted)}>
                <Globe className="w-5 h-5" />
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="font-bold text-gray-900 mb-6">Platform</h4>
            <ul className="space-y-3 text-gray-500">
              <li><a href="#" className="hover:text-[#FF6B35] transition-colors">Pricing</a></li>
              <li><a href="#" className="hover:text-[#FF6B35] transition-colors">Success Stories</a></li>
              <li><a href="#" className="hover:text-[#FF6B35] transition-colors">Chrome Extension</a></li>
              <li><a href="#" className="hover:text-[#FF6B35] transition-colors">For Recruiters</a></li>
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
            <a href="#" className="hover:text-[#FF6B35]">Privacy</a>
            <a href="#" className="hover:text-[#FF6B35]">Terms</a>
            <a href="#" className="hover:text-[#FF6B35]">Sitemap</a>
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
      <HeadSEO />
      <CustomCursor />
      <ProgressBar />
      <Navbar muted={muted} toggleMute={() => setMuted(!muted)} />
      <main>
        <Hero muted={muted} />
        <Onboarding />
        <FeaturedJobs muted={muted} />
        <AutomationEdge muted={muted} />
        <Comparison />
      </main>
      <Footer muted={muted} />
      <ExitIntentPopup />
      <SocialProofPulse />
    </div>
  );
}
