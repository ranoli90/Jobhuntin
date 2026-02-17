import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useReducedMotion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import {
  CheckCircle, ArrowRight,
  MailCheck, Bell,
  Upload, Search, Send, Lock, Shield, Clock,
  User, FileText, MessageSquare, Briefcase, TrendingUp, Target, Award, Moon, Sparkles
} from 'lucide-react';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';
import { cn } from '../lib/utils';

import { Button } from '../components/ui/Button';

// Realistic companies - mix of everyday employers
const COMPANIES = [
  // Retail & Service
  "Target", "Walmart", "Costco", "Home Depot", "Lowe's", "Best Buy", "CVS", "Walgreens",
  "Starbucks", "McDonald's", "Chick-fil-A", "Kroger", "Whole Foods", "Trader Joe's",
  // Healthcare
  "UnitedHealth", "Cigna", "Humana", "Kaiser", "HCA Healthcare", "Labcorp", "Quest Diagnostics",
  // Finance & Insurance  
  "State Farm", "Allstate", "Liberty Mutual", "USAA", "Nationwide", "Capital One", "Discover",
  "Wells Fargo", "Chase", "Bank of America", "US Bank", "PNC Bank",
  // Tech & Telecom
  "Verizon", "T-Mobile", "AT&T", "Comcast", "Spectrum", "Cisco", "Dell", "HP", "IBM",
  "Oracle", "SAP", "Salesforce", "Adobe", "Intuit", "PayPal", "Square",
  // Manufacturing & Logistics
  "FedEx", "UPS", "Amazon", "J.B. Hunt", "XPO Logistics", "C.H. Robinson", "RR Donnelley",
  "Caterpillar", "John Deere", "3M", "Honeywell", "GE", "Siemens", "Boeing", "Lockheed Martin",
  // Energy & Utilities
  "Duke Energy", "Southern Company", "NextEra", "Dominion Energy", "Exelon", "PG&E",
  // Professional Services
  "Deloitte", "PwC", "EY", "KPMG", "Accenture", "Capgemini", "Cognizant", "Infosys",
  "Robert Half", "Manpower", "Kelly Services", "Adecco",
  // Media & Entertainment
  "Disney", "Warner Bros", "Paramount", "NBCUniversal", "Spotify", "Netflix", "HBO Max",
  // Real Estate
  "Zillow", "Redfin", "Compass", "Realogy", "CBRE", "JLL",
  // Automotive
  "Ford", "GM", "Toyota", "Honda", "Tesla", "CarMax", "AutoNation",
  // Startups & Tech
  "Stripe", "Square", "Airbnb", "Uber", "Lyft", "DoorDash", "Instacart", "Slack", "Zoom",
  "Notion", "Figma", "Canva", "Webflow", "Shopify", "Plaid", "Ramp"
];

// Everyday positions for normal people
const ROLES = [
  // Sales
  "Sales Representative", "Account Executive", "Inside Sales", "Sales Manager", "Business Development",
  "Account Manager", "Sales Associate", "Retail Sales", "Sales Coordinator",
  // Customer Service & Support  
  "Customer Service Rep", "Customer Success Manager", "Support Specialist", "Client Services",
  "Call Center Rep", "Technical Support", "Help Desk Analyst", "Service Coordinator",
  // Marketing
  "Marketing Coordinator", "Digital Marketing", "Social Media Manager", "Content Writer",
  "Marketing Analyst", "SEO Specialist", "Email Marketing", "Marketing Assistant",
  // Operations & Admin
  "Operations Manager", "Office Manager", "Executive Assistant", "Administrative Assistant",
  "Operations Coordinator", "Project Coordinator", "Program Manager", "Logistics Coordinator",
  // Finance & Accounting
  "Accountant", "Financial Analyst", "Bookkeeper", "Accounts Payable", "Accounts Receivable",
  "Payroll Specialist", "Finance Manager", "Budget Analyst", "Tax Preparer",
  // HR & Recruiting
  "HR Coordinator", "Recruiter", "Talent Acquisition", "HR Generalist", "HR Assistant",
  "People Operations", "Benefits Coordinator", "Training Specialist",
  // IT & Tech
  "IT Support", "System Administrator", "Network Engineer", "Help Desk", "Software Developer",
  "Web Developer", "Data Analyst", "Business Intelligence Analyst", "QA Tester", "DevOps Engineer",
  // Healthcare (Non-clinical)
  "Medical Billing", "Medical Coding", "Healthcare Admin", "Patient Services", "Insurance Verification",
  // Supply Chain
  "Supply Chain Analyst", "Procurement Specialist", "Inventory Manager", "Warehouse Supervisor",
  "Purchasing Agent", "Logistics Manager", "Shipping Coordinator",
  // Skilled Trades
  "Electrician", "Plumber", "HVAC Technician", "Maintenance Tech", "Facilities Manager",
  "Carpenter", "Welder", "Mechanic", "Machine Operator",
  // Education
  "Teacher", "Tutor", "Academic Advisor", "School Counselor", "Education Coordinator",
  // Legal
  "Paralegal", "Legal Assistant", "Compliance Analyst", "Contract Administrator",
  // Creative
  "Graphic Designer", "UX Designer", "Video Editor", "Copywriter", "Photographer",
  // Real Estate
  "Real Estate Agent", "Property Manager", "Leasing Agent", "Appraiser",
  // Entry Level
  "Data Entry", "Receptionist", "File Clerk", "Warehouse Worker", "Delivery Driver",
  "Security Guard", "Cashier", "Stock Associate", "Production Worker"
];

const LOCATIONS = [
  "Remote", "Remote", "Remote", // More remote jobs
  "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
  "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
  "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
  "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
  "Boston, MA", "El Paso, TX", "Nashville, TN", "Detroit, MI", "Portland, OR",
  "Las Vegas, NV", "Memphis, TN", "Louisville, KY", "Baltimore, MD", "Milwaukee, WI",
  "Albuquerque, NM", "Tucson, AZ", "Fresno, CA", "Sacramento, CA", "Kansas City, MO",
  "Atlanta, GA", "Miami, FL", "Oakland, CA", "Minneapolis, MN", "Tulsa, OK",
  "Cleveland, OH", "San Juan, PR", "Raleigh, NC", "Omaha, NE", "Colorado Springs, CO"
];

const FIRST_NAMES = [
  "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
  "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
  "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
  "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
  "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
  "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
  "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
  "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
  "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
  "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
  "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
  "Frank", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Jack", "Catherine"
];

const LAST_INITIALS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R", "S", "T", "W", "Y", "Z"];

function getRandomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateActivity(): { name: string; role: string; company: string; location: string; time: string; id: string } {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: `${getRandomItem(FIRST_NAMES)} ${getRandomItem(LAST_INITIALS)}.`,
    role: getRandomItem(ROLES),
    company: getRandomItem(COMPANIES),
    location: getRandomItem(LOCATIONS),
    time: "just now"
  };
}

const LiveActivityStream = () => {
  const [activities, setActivities] = useState(() =>
    Array.from({ length: 8 }, () => generateActivity())
  );
  const [isPaused, setIsPaused] = useState(false);
  const [newItemId, setNewItemId] = useState<string | null>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion || isPaused) return;

    const interval = setInterval(() => {
      const newActivity = generateActivity();
      setNewItemId(newActivity.id);
      setActivities(prev => {
        const updated = [newActivity, ...prev.slice(0, 10)];
        return updated.map((a, i) => ({
          ...a,
          time: i === 0 ? "just now" : `${i}m ago`
        }));
      });
      setTimeout(() => setNewItemId(null), 600);
    }, 4000);

    return () => clearInterval(interval);
  }, [shouldReduceMotion, isPaused]);

  const visibleActivities = activities.slice(0, 4);

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="absolute -left-2 sm:-left-4 top-0 bottom-0 w-0.5 sm:w-1 bg-gradient-to-b from-blue-400 via-violet-400 to-transparent rounded-full" />

      <div className="space-y-1 sm:space-y-2">
        {visibleActivities.map((activity, i) => {
          const isNew = activity.id === newItemId;
          return (
            <div
              key={activity.id}
              className={cn(
                "flex items-center gap-2 sm:gap-3 py-2 sm:py-3 transition-all duration-500 ease-out will-change-transform",
                i === 0 && "bg-gradient-to-r from-blue-900/20 via-violet-900/20 to-transparent -mx-2 sm:-mx-3 px-2 sm:px-3 rounded-lg sm:rounded-xl mb-1",
                isNew && "animate-slide-in"
              )}
              style={{
                opacity: i === 0 ? 1 : 0.65,
                transform: isNew ? 'translateY(0)' : 'translateY(0)'
              }}
            >
              <div className={cn(
                "w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors duration-300",
                i === 0
                  ? "bg-gradient-to-br from-blue-500 to-violet-500"
                  : "bg-slate-700"
              )}>
                {i === 0 ? (
                  <Send className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-white" />
                ) : (
                  <User className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-slate-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-xs sm:text-sm leading-snug truncate transition-opacity duration-300 typography-premium text-perfect",
                  i === 0 ? "text-white font-medium" : "text-slate-400"
                )}>
                  <span className="font-semibold">{activity.name}</span>
                  <span className="text-slate-500 mx-1">→</span>
                  <span className="text-blue-400">{activity.role}</span>
                  <span className="text-slate-500 hidden sm:inline"> at {activity.company}</span>
                </p>
                <div className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-500">
                  <span className="sm:hidden">{activity.company}</span>
                  <span className="hidden sm:inline">{activity.location}</span>
                  <span className="text-slate-600">·</span>
                  <span>{activity.time}</span>
                </div>
              </div>

              {i === 0 && (
                <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 bg-emerald-900/30 text-emerald-400 rounded-full text-xs font-medium animate-fade-in">
                  <CheckCircle className="w-3 h-3" />
                  Applied
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-3 sm:mt-4 pt-2 sm:pt-3 border-t border-slate-700">
        <p className="text-xs text-slate-500 text-center flex items-center justify-center gap-1.5 typography-premium text-perfect">
          <span className={cn(
            "w-1.5 h-1.5 rounded-full transition-colors duration-300",
            isPaused ? "bg-amber-400" : "bg-emerald-400 animate-pulse"
          )} />
          <span className="text-xs sm:text-sm">{isPaused ? "Paused" : "Live"} • Updates every few seconds</span>
        </p>
      </div>
    </div>
  );
};

const ProgressBar = () => {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });

  return (
    <div className="fixed top-0 left-0 right-0 h-1 bg-slate-100 z-[60]">
      <motion.div className="h-full bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500" style={{ scaleX, transformOrigin: "0%" }} />
    </div>
  );
};

const Hero = () => {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [sentEmail, setSentEmail] = useState<string | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const validateEmail = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    if (!validateEmail(email)) {
      setEmailError("Enter a valid email");
      return;
    }
    setEmailError("");
    setIsSubmitting(true);
    setSentEmail(null);

    try {
      const result = await magicLinkService.sendMagicLink(email, "/app/dashboard");
      if (!result.success) throw new Error(result.error || "Failed");

      if (typeof window !== 'undefined' && confetti && !shouldReduceMotion) {
        confetti({ particleCount: 80, spread: 60, origin: { y: 0.7 }, colors: ['#3b82f6', '#8b5cf6', '#ec4899'] });
      }

      pushToast({ title: "Check your inbox", description: "Magic link sent!", tone: "success" });
      setSentEmail(result.email);
      setEmail("");
      setIsSubmitting(false);
    } catch (err: any) {
      setIsSubmitting(false);
      setEmailError(err?.message || "Failed to send");
      pushToast({ title: "Error", description: err?.message || "Failed", tone: "error" });
    }
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Sophisticated background layers */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Subtle image overlay */}
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=2071&auto=format&fit=crop')] bg-cover bg-center opacity-10 mix-blend-screen" />

        {/* Premium gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950/20 via-transparent to-violet-950/20" />

        {/* Film grain texture */}
        <div className="absolute inset-0 bg-film-grain" />

        {/* Subtle grid */}
        <div className="absolute inset-0 bg-grid-premium opacity-3" />

        {/* Ambient light orbs */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-500/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-pink-500/3 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="flex flex-col items-center text-center max-w-5xl mx-auto">
          {/* Sophisticated badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="mb-8 sm:mb-12"
          >
            <div className="inline-flex items-center gap-3 px-4 sm:px-6 py-2 sm:py-3 rounded-full surface-premium border-organic hover-organic typography-premium">
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity, repeatDelay: 2 }}
              >
                <Sparkles className="w-4 h-4 text-blue-400" />
              </motion.div>
              <span className="text-sm sm:text-base font-medium text-slate-300 spacing-premium text-perfect">
                For those who <span className="font-semibold text-blue-400">work smarter</span>, not harder
              </span>
            </div>
          </motion.div>

          {/* Premium headline */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="mb-6 sm:mb-8"
          >
            <h1 className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight leading-[0.9] sm:leading-[0.85] text-balance text-shadow-premium typography-premium spacing-premium text-perfect">
              <span className="block text-white/95 mb-2 heading-large-mobile-optimized heading-large-desktop-optimized">Your next career move</span>
              <span className="block bg-gradient-to-r from-blue-400 via-violet-400 to-pink-400 bg-clip-text text-transparent text-shadow-strong heading-large-mobile-optimized heading-large-desktop-optimized">
                happens while you sleep
              </span>
            </h1>
          </motion.div>

          {/* Refined description */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="font-body text-lg sm:text-xl lg:text-2xl text-slate-400 max-w-3xl mb-8 sm:mb-12 leading-relaxed text-balance typography-premium spacing-premium text-perfect text-mobile-optimized"
          >
            Upload your resume once. We handle the rest—tailored applications, strategic timing,
            and interview opportunities that align with your ambitions.
          </motion.p>

          {/* Premium email capture */}
          {!sentEmail ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-lg sm:max-w-xl mb-8 sm:mb-10"
            >
              <form onSubmit={onSubmit} className="relative">
                <div className="relative group">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-violet-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <div className="relative glass-premium-dark rounded-2xl border-organic p-1">
                    <div className="flex flex-col sm:flex-row gap-2 p-3 sm:p-4">
                      <div className="relative flex-1">
                        <MailCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 transition-colors group-focus-within:text-blue-400" />
                        <input
                          type="email"
                          placeholder="Enter your email"
                          className={cn(
                            "w-full pl-12 pr-4 py-4 sm:py-5 rounded-xl bg-transparent border-0 text-white placeholder:text-slate-500",
                            "focus:outline-none focus:ring-0 typography-premium spacing-premium text-perfect text-mobile-optimized",
                            "transition-all duration-300",
                            emailError && "text-red-400 placeholder:text-red-400/50"
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
                        className="px-6 sm:px-8 py-4 sm:py-5 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-500 to-violet-500 hover:from-blue-600 hover:to-violet-600 transition-all duration-300 shadow-lg hover:shadow-xl hover-lift typography-premium border-0 text-perfect"
                      >
                        {isSubmitting ? (
                          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                            <Briefcase className="w-5 h-5" />
                          </motion.div>
                        ) : (
                          <span className="flex items-center gap-2 text-sm sm:text-base">
                            Get Started <ArrowRight className="w-4 h-4" />
                          </span>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </form>

              {emailError && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 text-sm text-red-400 font-medium typography-premium text-perfect">
                  {emailError}
                </motion.p>
              )}

              {/* Sophisticated trust indicators */}
              <div className="mt-6 sm:mt-8 flex flex-wrap items-center justify-center gap-x-6 sm:gap-x-8 gap-y-3 text-sm text-slate-500 typography-premium text-perfect">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <Lock className="w-2.5 h-2.5 text-emerald-400" />
                  </div>
                  <span className="text-xs sm:text-sm">Bank-level security</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Shield className="w-2.5 h-2.5 text-blue-400" />
                  </div>
                  <span className="text-xs sm:text-sm">Privacy first</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-violet-500/20 flex items-center justify-center">
                    <Clock className="w-2.5 h-2.5 text-violet-400" />
                  </div>
                  <span className="text-xs sm:text-sm">2-minute setup</span>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-lg sm:max-w-xl glass-premium-dark rounded-2xl border-organic p-6 sm:p-8 text-center shadow-2xl"
            >
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center shadow-xl mx-auto mb-6">
                <MailCheck className="w-8 h-8 text-white" />
              </div>
              <p className="text-lg sm:text-xl font-semibold text-white mb-2 typography-premium text-perfect">Check your inbox</p>
              <p className="text-slate-400 mb-6 leading-relaxed typography-premium text-perfect text-mobile-optimized">
                We've sent a magic link to <span className="text-white font-medium">{sentEmail}</span>.
                Click it to begin your journey.
              </p>
              <button
                onClick={() => setSentEmail(null)}
                className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors typography-premium hover-organic px-4 py-2 rounded-lg text-perfect"
              >
                Use a different email
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
};

const LiveActivitySection = () => {
  return (
    <section className="py-24 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Sophisticated background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-film-grain" />
        <div className="absolute inset-0 bg-grid-premium opacity-2" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/3 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-violet-500/3 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="grid lg:grid-cols-2 gap-16 lg:gap-20 items-center">
          <div>
            {/* Premium badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="mb-8"
            >
              <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full surface-premium border-organic hover-organic typography-premium">
                <div className="relative">
                  <div className="w-2 h-2 bg-blue-400 rounded-full" />
                  <div className="absolute inset-0 w-2 h-2 bg-blue-400 rounded-full animate-ping opacity-75" />
                </div>
                <span className="text-sm font-semibold text-blue-400 uppercase tracking-wider spacing-premium">Live Activity</span>
              </div>
            </motion.div>

            {/* Premium headline */}
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="font-display text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold tracking-tight text-white mb-4 sm:mb-6 text-shadow-premium typography-premium spacing-premium text-perfect heading-mobile-optimized heading-desktop-optimized"
            >
              Watch opportunities<br />
              <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-pink-400 bg-clip-text text-transparent text-shadow-strong heading-mobile-optimized heading-desktop-optimized">
                arrive in real-time
              </span>
            </motion.h2>

            {/* Refined description */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="font-body text-lg sm:text-xl text-slate-400 mb-8 sm:mb-10 leading-relaxed max-w-lg typography-premium spacing-premium text-perfect text-mobile-optimized"
            >
              While you focus on what matters, our AI continuously identifies and applies to positions that match your expertise and aspirations.
            </motion.p>

            {/* Premium features */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="space-y-4"
            >
              <div className="flex items-start gap-4 p-4 sm:p-6 surface-elevated rounded-xl border-organic hover-organic transition-all duration-300">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                  <Target className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white mb-1 typography-premium text-perfect text-mobile-optimized">Precision Matching</h3>
                  <p className="text-sm text-slate-400 typography-premium text-perfect text-mobile-optimized">Advanced algorithms ensure every opportunity aligns with your unique profile</p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 sm:p-6 surface-elevated rounded-xl border-organic hover-organic transition-all duration-300">
                <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                  <Award className="w-6 h-6 text-violet-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-white mb-1 typography-premium text-perfect text-mobile-optimized">Curated Quality</h3>
                  <p className="text-sm text-slate-400 typography-premium text-perfect text-mobile-optimized">Each application is crafted with the attention of a seasoned career consultant</p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Premium activity display */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="relative"
          >
            <div className="glass-premium-dark rounded-2xl sm:rounded-3xl border-organic p-6 sm:p-8 shadow-2xl">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg sm:text-xl font-semibold text-white typography-premium text-perfect text-mobile-optimized">Recent Activity</h3>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-xs sm:text-sm text-emerald-400 font-medium typography-premium text-perfect">Live</span>
                </div>
              </div>
              <LiveActivityStream />
            </div>

            {/* Ambient glow effect */}
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/10 to-violet-500/10 rounded-3xl blur-xl -z-10" />
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const Onboarding = () => {
  const steps = [
    {
      icon: Upload,
      title: "Initialize",
      desc: "Upload your resume and let our AI analyze your unique value proposition",
      detail: "Skills, experience, and potential extracted in seconds"
    },
    {
      icon: Search,
      title: "Strategic Matching",
      desc: "We identify opportunities that align with your career trajectory",
      detail: "Thousands of positions filtered for perfect fit"
    },
    {
      icon: FileText,
      title: "Crafted Applications",
      desc: "Each submission is tailored to resonate with hiring managers",
      detail: "Personalized narratives that highlight your strengths"
    },
    {
      icon: MessageSquare,
      title: "Interview Ready",
      desc: "Receive curated interview opportunities with preparation insights",
      detail: "Connect with companies actively seeking your expertise"
    },
  ];

  return (
    <section className="py-24 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
      {/* Sophisticated background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-film-grain" />
        <div className="absolute inset-0 bg-grid-premium opacity-2" />
        <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-blue-500/2 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-violet-500/2 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        {/* Premium header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-20"
        >
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold tracking-tight text-white mb-4 sm:mb-6 text-shadow-premium typography-premium spacing-premium text-perfect heading-mobile-optimized heading-desktop-optimized">
            The path to your <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-pink-400 bg-clip-text text-transparent text-shadow-strong heading-mobile-optimized heading-desktop-optimized">next chapter</span>
          </h2>
          <p className="font-body text-lg sm:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed typography-premium spacing-premium text-perfect text-mobile-optimized">
            A sophisticated approach to career advancement that works while you focus on growth
          </p>
        </motion.div>

        {/* Premium steps */}
        <div className="relative max-w-6xl mx-auto">
          <div className="absolute top-1/2 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-700/30 to-transparent hidden lg:block" />

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.15, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                viewport={{ once: true }}
                className="relative group"
              >
                <div className="flex flex-col items-center text-center">
                  {/* Premium step number */}
                  <div className="relative mb-8">
                    <div className="absolute -inset-2 bg-gradient-to-r from-blue-500/20 to-violet-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    <div className="relative surface-elevated rounded-2xl border-organic p-6 hover-organic transition-all duration-300">
                      <step.icon className="w-8 h-8 text-white mb-4" />
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-sm font-bold text-white shadow-lg">
                        {i + 1}
                      </div>
                    </div>
                  </div>

                  {/* Premium content */}
                  <h3 className="font-display text-lg sm:text-xl font-bold text-white mb-2 sm:mb-3 typography-premium spacing-premium text-perfect text-mobile-optimized">{step.title}</h3>
                  <p className="font-body text-sm sm:text-base text-slate-400 leading-relaxed mb-2 sm:mb-3 typography-premium spacing-premium text-perfect text-mobile-optimized">{step.desc}</p>
                  <p className="font-body text-xs sm:text-sm text-slate-500 uppercase tracking-wider typography-premium text-perfect text-mobile-optimized">{step.detail}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Premium footer */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="mt-20 text-center"
        >
          <div className="inline-flex items-center gap-3 sm:gap-4 px-4 sm:px-6 py-2 sm:py-3 rounded-full surface-premium border-organic hover-organic typography-premium">
            <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400" />
            <span className="text-sm sm:text-base font-medium text-slate-300 spacing-premium text-perfect text-mobile-optimized">
              Complete setup in <span className="font-bold text-white">under 2 minutes</span>
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

const StickyMobileCTA = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsVisible(window.scrollY > 400);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass-premium-dark border-t border-slate-600/50 p-4 shadow-2xl"
    >
      <Button
        className="w-full rounded-xl py-4 font-bold text-base bg-gradient-to-r from-blue-500 to-violet-500 hover:from-blue-600 hover:to-violet-600 shadow-xl hover-lift typography-premium border-0"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      >
        <Sparkles className="w-5 h-5 mr-2" />
        Begin Your Journey
        <ArrowRight className="w-5 h-5 ml-2" />
      </Button>
    </motion.div>
  );
};

export default function Homepage() {
  return (
    <>
      <SEO
        title="JobHuntin — We Apply to Jobs While You Sleep"
        description="Upload your resume once. We tailor and apply to hundreds of jobs daily. Land 3.4× more interviews with zero effort."
        ogTitle="JobHuntin — We Apply to Jobs While You Sleep"
        canonicalUrl="https://jobhuntin.com/"
        schema={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          "mainEntity": [
            { "@type": "Question", "name": "Is this legit? Will I get banned from job sites?", "acceptedAnswer": { "@type": "Answer", "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications." } },
            { "@type": "Question", "name": "How is this different from just applying myself?", "acceptedAnswer": { "@type": "Answer", "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter." } },
            { "@type": "Question", "name": "What happens to my resume and data?", "acceptedAnswer": { "@type": "Answer", "text": "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime." } }
          ]
        }}
      />
      <ProgressBar />
      <Hero />
      <LiveActivitySection />
      <Onboarding />
      <StickyMobileCTA />
    </>
  );
}