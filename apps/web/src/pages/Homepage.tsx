import React, { useState, useEffect } from 'react';
import { motion, useScroll, useSpring, useReducedMotion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { magicLinkService } from '../services/magicLinkService';
import {
  CheckCircle, ArrowRight,
  MailCheck, Bell,
  Upload, Search, Send, Lock, Shield, Clock,
  User, FileText, MessageSquare, Briefcase, TrendingUp, Target, Award
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { pushToast } from '../lib/toast';
import { SEO } from '../components/marketing/SEO';

import { Button } from '../components/ui/Button';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Realistic companies - mix of everyday employers
const COMPANIES = [
  // Retail & Service
  "Target", "Walmart", "Costco", "Home Depot", " Lowe's", "Best Buy", "CVS", "Walgreens",
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
  "Notion", "Figma", "Canva", "Webflow", "Shopify", "Square", "Plaid", "Ramp"
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
          time: i === 0 ? "just now" : i === 1 ? "1m ago" : i === 2 ? "2m ago" : `${i + 1}m ago`
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
      <div className="absolute -left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-400 via-violet-400 to-transparent rounded-full" />
      
      <div className="space-y-0">
        {visibleActivities.map((activity, i) => {
          const isNew = activity.id === newItemId;
          return (
            <div
              key={activity.id}
              className={cn(
                "flex items-center gap-3 py-2.5 transition-all duration-500 ease-out will-change-transform",
                i === 0 && "bg-gradient-to-r from-blue-50 via-violet-50 to-transparent -mx-3 px-3 rounded-lg mb-1",
                isNew && "animate-slide-in"
              )}
              style={{
                opacity: i === 0 ? 1 : 0.65,
                transform: isNew ? 'translateY(0)' : 'translateY(0)'
              }}
            >
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-colors duration-300",
                i === 0 
                  ? "bg-gradient-to-br from-blue-500 to-violet-500" 
                  : "bg-slate-100"
              )}>
                {i === 0 ? (
                  <Send className="w-3.5 h-3.5 text-white" />
                ) : (
                  <User className="w-3.5 h-3.5 text-slate-400" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-sm leading-snug truncate transition-opacity duration-300",
                  i === 0 ? "text-slate-900 font-medium" : "text-slate-600"
                )}>
                  <span className="font-semibold">{activity.name}</span>
                  <span className="text-slate-400 mx-1">→</span>
                  <span className="text-blue-600">{activity.role}</span>
                  <span className="text-slate-400 hidden sm:inline"> at {activity.company}</span>
                </p>
                <div className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-400">
                  <span className="sm:hidden">{activity.company}</span>
                  <span className="hidden sm:inline">{activity.location}</span>
                  <span className="text-slate-300">·</span>
                  <span>{activity.time}</span>
                </div>
              </div>
              
              {i === 0 && (
                <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-full text-xs font-medium animate-fade-in">
                  <CheckCircle className="w-3 h-3" />
                  Applied
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      <div className="mt-3 pt-2 border-t border-slate-100">
        <p className="text-xs text-slate-400 text-center flex items-center justify-center gap-1.5">
          <span className={cn(
            "w-1.5 h-1.5 rounded-full transition-colors duration-300",
            isPaused ? "bg-amber-400" : "bg-emerald-400 animate-pulse"
          )} />
          {isPaused ? "Paused" : "Live"} • Updates every few seconds
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
      const result = await magicLinkService.sendMagicLink(email, "/app/onboarding");
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
    <section className="relative min-h-[100svh] flex items-center justify-center overflow-hidden bg-gradient-to-b from-white via-white to-slate-50/50 pb-32 -mb-16">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-gradient-to-br from-blue-100/40 to-violet-100/40 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-gradient-to-tr from-pink-100/30 to-amber-100/30 rounded-full blur-3xl" />
      </div>

      <div className="absolute inset-0 bg-grid-premium opacity-20 pointer-events-none" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 pt-20 lg:pt-0">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-slate-50 border border-slate-200/80 mb-8"
          >
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span className="text-xs sm:text-sm font-medium text-slate-600 tracking-wide">
              The only platform that <span className="font-bold text-slate-900">tailors every resume</span> to each job
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[0.95] mb-6 text-balance-hero max-w-3xl"
          >
            <span className="text-slate-900">We apply to</span>
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-violet-600 to-pink-600 bg-clip-text text-transparent animate-gradient-flow bg-[length:200%_auto]">
              100 jobs daily
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="font-body text-lg sm:text-xl lg:text-2xl text-slate-500 max-w-2xl mb-10 leading-relaxed"
          >
            Upload your resume. Our system matches, tailors, and submits applications
            <span className="hidden sm:inline"> while you focus on interviews.</span>
            <span className="sm:hidden"> automatically.</span>
          </motion.p>

          {!sentEmail ? (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-md"
            >
              <form onSubmit={onSubmit} className="relative">
                <div className="flex flex-col sm:flex-row gap-3 p-2 bg-slate-50 rounded-2xl border border-slate-200/60">
                  <div className="relative flex-1">
                    <MailCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="email"
                      placeholder="your@email.com"
                      className={cn(
                        "w-full pl-12 pr-4 py-3.5 rounded-xl bg-white border transition-all text-slate-900 placeholder:text-slate-400",
                        "focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400",
                        emailError ? "border-red-300 bg-red-50/50" : "border-slate-200"
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
                    className="h-12 sm:h-auto px-8 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
                  >
                    {isSubmitting ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
                        <Briefcase className="w-5 h-5" />
                      </motion.div>
                    ) : (
                      <span className="flex items-center gap-2">
                        Get started <ArrowRight className="w-4 h-4" />
                      </span>
                    )}
                  </Button>
                </div>
              </form>
              
              {emailError && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 text-sm text-red-500 font-medium">
                  {emailError}
                </motion.p>
              )}

              <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-400">
                <span className="flex items-center gap-1.5"><Lock className="w-4 h-4" /> No credit card</span>
                <span className="flex items-center gap-1.5"><Shield className="w-4 h-4" /> Secure</span>
                <span className="flex items-center gap-1.5"><Clock className="w-4 h-4" /> 2-min setup</span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-md bg-gradient-to-br from-slate-50 to-white rounded-2xl border border-slate-200 p-6 text-left shadow-xl"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <MailCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold mb-0.5">Sent</p>
                  <p className="font-semibold text-slate-900">{sentEmail}</p>
                </div>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed mb-4">
                Check your inbox for the magic link. Click it to start your AI job search.
              </p>
              <button onClick={() => setSentEmail(null)} className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
                Use different email
              </button>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="mt-16 w-full max-w-4xl"
          >
            <div className="relative">
              <div className="bg-slate-900 rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl shadow-slate-900/30 border border-slate-800">
                <div className="flex items-center gap-2 px-4 sm:px-5 py-3 border-b border-slate-800 bg-slate-900">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  <div className="flex-1 flex justify-center">
                    <span className="text-xs font-medium text-slate-500">JobHuntin Dashboard</span>
                  </div>
                </div>
                
                <div className="flex">
                  <div className="hidden md:flex flex-col w-48 bg-slate-800/50 border-r border-slate-700/50 p-3 space-y-1">
                    {[
                      { icon: Briefcase, label: "Dashboard", active: true },
                      { icon: Search, label: "Jobs" },
                      { icon: FileText, label: "Applications" },
                      { icon: MessageSquare, label: "Messages" },
                      { icon: User, label: "Profile" },
                    ].map((item, i) => (
                      <div
                        key={i}
                        className={cn(
                          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                          item.active 
                            ? "bg-blue-600/20 text-blue-400 font-medium" 
                            : "text-slate-500 hover:text-slate-300"
                        )}
                      >
                        <item.icon className="w-4 h-4" />
                        {item.label}
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex-1 p-4 sm:p-5">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                      {[
                        { label: "Jobs Matched", value: "2,847", color: "text-blue-400", bg: "bg-blue-500/10" },
                        { label: "Applied", value: "152", color: "text-violet-400", bg: "bg-violet-500/10" },
                        { label: "Interviews", value: "8", color: "text-emerald-400", bg: "bg-emerald-500/10" },
                        { label: "Response Rate", value: "34%", color: "text-amber-400", bg: "bg-amber-500/10" },
                      ].map((stat, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.7 + i * 0.08 }}
                          className={cn("rounded-xl p-3", stat.bg)}
                        >
                          <p className="text-[10px] text-slate-500 uppercase tracking-wider">{stat.label}</p>
                          <p className={cn("text-xl font-bold mt-0.5", stat.color)}>{stat.value}</p>
                        </motion.div>
                      ))}
                    </div>
                    
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recent Applications</p>
                      <span className="text-[10px] text-blue-400">View all →</span>
                    </div>
                    
                    <div className="space-y-2">
                      {[
                        { company: "Stripe", role: "Senior Software Engineer", location: "San Francisco", salary: "$180-220k", status: "Interview", statusColor: "bg-emerald-500/20 text-emerald-400" },
                        { company: "Notion", role: "Product Engineer", location: "Remote", salary: "$150-190k", status: "Applied", statusColor: "bg-blue-500/20 text-blue-400" },
                        { company: "Linear", role: "Full Stack Developer", location: "Remote", salary: "$140-180k", status: "Applied", statusColor: "bg-blue-500/20 text-blue-400" },
                      ].map((job, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.9 + i * 0.12 }}
                          className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50"
                        >
                          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-[10px] font-bold text-white border border-slate-600">
                            {job.company.slice(0, 2).toUpperCase()}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">{job.role}</p>
                            <div className="flex items-center gap-2 text-[10px] text-slate-500">
                              <span>{job.company}</span>
                              <span>•</span>
                              <span>{job.location}</span>
                              <span className="text-slate-400">{job.salary}</span>
                            </div>
                          </div>
                          <span className={cn("px-2 py-1 rounded-full text-[10px] font-medium", job.statusColor)}>
                            {job.status}
                          </span>
                        </motion.div>
                      ))}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-slate-700/50">
                      <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                        <span>Today's Applications</span>
                        <span className="text-white font-medium">47/50</span>
                      </div>
                      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500 rounded-full"
                          initial={{ width: "0%" }}
                          animate={{ width: "94%" }}
                          transition={{ delay: 1.3, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.5, duration: 0.5 }}
                className="absolute -right-3 -bottom-3 bg-emerald-500 text-white px-4 py-2 rounded-xl shadow-lg shadow-emerald-500/30 text-sm font-bold flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                3 new matches!
              </motion.div>
              
              <div className="absolute -bottom-16 left-0 right-0 h-20 bg-gradient-to-b from-transparent via-white/60 to-white pointer-events-none rounded-b-3xl" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const LiveActivitySection = () => {
  return (
    <section className="py-20 sm:py-24 bg-slate-50 relative overflow-hidden -mt-16 pt-32">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-slate-50 to-white pointer-events-none" />
      <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 mb-6"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75 animate-ping" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Live Activity</span>
            </motion.div>
            
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 mb-4"
            >
              Watch it happen<br />
              <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">in real-time</span>
            </motion.h2>
            
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="font-body text-lg text-slate-500 mb-8 leading-relaxed"
            >
              Every few seconds, our AI submits another tailored application. 
              This is happening right now for job seekers just like you.
            </motion.p>
            
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-wrap gap-6 items-center"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
                  <Target className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">ATS-Optimized</p>
                  <p className="text-xs text-slate-500">Passes every filter</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
                  <Award className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Human Quality</p>
                  <p className="text-xs text-slate-500">Professional output</p>
                </div>
              </div>
            </motion.div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xl shadow-slate-200/50"
          >
            <LiveActivityStream />
          </motion.div>
        </div>
      </div>
    </section>
  );
};

const Onboarding = () => {
  const steps = [
    { icon: Upload, title: "Upload", desc: "Drop your resume, we extract everything" },
    { icon: Search, title: "Match", desc: "Find jobs that fit your skills" },
    { icon: FileText, title: "Tailor", desc: "Customize for each application" },
    { icon: MessageSquare, title: "Notify", desc: "Get interview alerts" },
  ];

  return (
    <section id="how-it-works" className="py-24 sm:py-32 bg-white relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-slate-50 to-slate-100 rounded-full blur-3xl opacity-60 pointer-events-none" />

      <div className="container mx-auto px-5 sm:px-8 lg:px-12 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-16 lg:mb-20"
        >
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 mb-4">
            Four steps to <span className="text-blue-600">more interviews</span>
          </h2>
          <p className="font-body text-lg text-slate-500 max-w-xl mx-auto">
            Set up once, let us handle the rest. You only show up for the wins.
          </p>
        </motion.div>

        <div className="relative max-w-4xl mx-auto">
          <div className="absolute top-12 left-0 right-0 h-px bg-slate-200 hidden lg:block" />
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + i * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                viewport={{ once: true }}
                className="relative group"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-5">
                    <div className="w-20 h-20 rounded-2xl bg-slate-900 flex items-center justify-center shadow-xl group-hover:shadow-2xl transition-shadow duration-300">
                      <step.icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
                      {i + 1}
                    </div>
                  </div>
                  <h3 className="font-display text-lg font-bold text-slate-900 mb-1">{step.title}</h3>
                  <p className="font-body text-sm text-slate-500 leading-relaxed">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-50 border border-slate-200">
            <Clock className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-slate-600">Average setup time: <span className="font-bold text-slate-900">2 minutes</span></span>
          </div>
        </motion.div>
      </div>
    </section>
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
            { "@type": "Question", "name": "Is this legit? Will I get banned from job sites?", "acceptedAnswer": { "@type": "Answer", "text": "Absolutely legit. We follow each platform's Terms of Service. We don't spam, we don't use bots that violate rate limits, and we never submit low-quality applications." }},
            { "@type": "Question", "name": "How is this different from just applying myself?", "acceptedAnswer": { "@type": "Answer", "text": "Speed and quality. Most people take 20-30 minutes per application. We do it in under 2 minutes, and we customize every resume and cover letter." }},
            { "@type": "Question", "name": "What happens to my resume and data?", "acceptedAnswer": { "@type": "Answer", "text": "Your data is yours. We store it securely (encrypted at rest), never sell it to third parties, and you can delete everything anytime." }}
          ]
        }}
      />
      <ProgressBar />
      <Hero />
      <LiveActivitySection />
      <Onboarding />
    </>
  );
}