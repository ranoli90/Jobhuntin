import * as React from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { ChevronDown, MessageCircle, Shield, Zap, Lock, Eye, Edit3, CreditCard, ArrowRight } from "lucide-react";
import { cn } from "../../lib/utils";

const FAQS = [
  {
    question: "Is this legit? Will I get banned from job sites?",
    answer: "100% compliant with every platform's Terms of Service. We send tailored, high-quality applications — the kind recruiters actually want to read.",
    icon: Shield,
    color: "from-emerald-500 to-teal-600",
    highlight: "100% compliant",
  },
  {
    question: "How is this different from just applying myself?",
    answer: "You spend 30 minutes per app. We do it in under 2 — with a custom resume and cover letter for every single role. 50 tailored applications a day, every day, while you focus on interviews.",
    icon: Zap,
    color: "from-amber-500 to-orange-600",
    highlight: "50x faster",
  },
  {
    question: "What happens to my resume and data?",
    answer: "Encrypted, never sold, deletable anytime with one click. We only use your resume to generate applications — you approve every one before it sends.",
    icon: Lock,
    color: "from-violet-500 to-fuchsia-600",
    highlight: "Bank-level security",
  },
  {
    question: "Do employers know I used JobHuntin?",
    answer: "Nope. Every application comes from your email with your name. Employers see a polished candidate — never a bot.",
    icon: Eye,
    color: "from-cyan-500 to-blue-600",
    highlight: "Invisible to employers",
  },
  {
    question: "What if I want to customize an application?",
    answer: "You see every application before it goes out. Edit the cover letter, tweak resume bullets, or skip entirely — you're always in control.",
    icon: Edit3,
    color: "from-pink-500 to-rose-600",
    highlight: "Full control",
  },
  {
    question: "How much does it cost?",
    answer: "Free to start — 10 applications on us, no credit card. Pro is $19/mo for unlimited, Teams $49/seat. One interview covers it for life.",
    icon: CreditCard,
    color: "from-blue-500 to-primary-600",
    highlight: "Start free",
  },
];

function FAQItem({ faq, index, isOpen, onToggle }: { 
  faq: typeof FAQS[0]; 
  index: number; 
  isOpen: boolean;
  onToggle: () => void;
}) {
  const Icon = faq.icon;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className={cn(
        "relative rounded-2xl border transition-all duration-300 overflow-hidden",
        isOpen 
          ? "bg-slate-900 border-slate-700 shadow-xl shadow-black/20" 
          : "bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
      )}
    >
      {/* Gradient border glow when open */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-300",
        faq.color,
        isOpen && "opacity-5"
      )} />

      <button
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls={`faq-panel-${index}`}
        className="relative w-full flex items-center gap-4 p-6 text-left"
      >
        {/* Icon with gradient background */}
        <div className={cn(
          "shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300",
          isOpen 
            ? `bg-gradient-to-br ${faq.color} text-white shadow-lg` 
            : "bg-slate-800 text-slate-400"
        )}>
          <Icon className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className={cn(
              "font-semibold transition-colors",
              isOpen ? "text-white" : "text-slate-300"
            )}>
              {faq.question}
            </h3>
            {/* Highlight badge */}
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium transition-all duration-300",
              isOpen 
                ? `bg-gradient-to-r ${faq.color} text-white` 
                : "bg-slate-800 text-slate-500"
            )}>
              {faq.highlight}
            </span>
          </div>
        </div>

        {/* Expand icon */}
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className={cn(
            "shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors",
            isOpen ? "bg-slate-800 text-white" : "bg-slate-800/50 text-slate-500"
          )}
        >
          <ChevronDown className="w-5 h-5" />
        </motion.div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id={`faq-panel-${index}`}
            role="region"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            <div className="px-6 pb-6 pl-[88px]">
              <p className="text-slate-400 leading-relaxed">
                {faq.answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });

  return (
    <section ref={sectionRef} className="relative py-24 lg:py-32 bg-slate-950 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-0 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-cyan-500/5 to-transparent blur-[100px] -translate-y-1/2" />
        <div className="absolute top-1/2 right-0 w-[400px] h-[400px] rounded-full bg-gradient-to-br from-violet-500/5 to-transparent blur-[80px] -translate-y-1/2" />
      </div>

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div 
          className="mb-16 text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-sm font-medium text-slate-400 mb-6">
            <MessageCircle className="w-4 h-4" />
            Common Questions
          </span>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight">
            Straight answers.
            <br />
            <span className="text-slate-500">No corporate speak.</span>
          </h2>
          <p className="mt-6 text-lg text-slate-400 max-w-2xl mx-auto">
            We know job hunting is stressful enough. Here's everything you need to know, 
            explained like a human would.
          </p>
        </motion.div>

        {/* FAQ items */}
        <div className="space-y-4">
          {FAQS.map((faq, index) => (
            <FAQItem
              key={index}
              faq={faq}
              index={index}
              isOpen={openIndex === index}
              onToggle={() => setOpenIndex(openIndex === index ? null : index)}
            />
          ))}
        </div>

        {/* Still have questions CTA */}
        <motion.div 
          className="mt-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex flex-col sm:flex-row items-center gap-6 p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800">
            <div className="text-center sm:text-left">
              <h3 className="text-lg font-semibold text-white mb-1">Still have questions?</h3>
              <p className="text-slate-400">Our team usually responds within 2 hours.</p>
            </div>
            <a 
              href="mailto:hello@jobhuntin.com" 
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800 text-white font-medium hover:bg-slate-700 transition-colors group"
            >
              Chat with us
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
