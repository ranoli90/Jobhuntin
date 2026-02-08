import * as React from "react";
import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { Check, Zap, Users, Building2, ArrowRight, Sparkles } from "lucide-react";
import { cn } from "../../lib/utils";

const PLANS = [
  {
    name: "Starter",
    description: "Perfect for testing the waters",
    price: { monthly: 0, yearly: 0 },
    priceLabel: "Free",
    period: "forever",
    highlight: "10 applications",
    cta: "Get started",
    ctaStyle: "outline" as const,
    features: [
      "10 job applications",
      "Basic AI matching",
      "Standard resume parsing",
      "Email support",
      "7-day activity history",
    ],
    excluded: [
      "Custom cover letters",
      "Interview prep",
      "Priority support",
    ],
    icon: Sparkles,
    color: "from-slate-600 to-slate-700",
    badge: null,
  },
  {
    name: "Pro",
    description: "For serious job seekers",
    price: { monthly: 19, yearly: 15 },
    priceLabel: null,
    period: "month",
    highlight: "Unlimited",
    cta: "Start free trial",
    ctaStyle: "primary" as const,
    features: [
      "Unlimited applications",
      "Advanced AI matching",
      "Custom cover letters per job",
      "Interview preparation kit",
      "Priority email support",
      "30-day analytics",
      "Resume A/B testing",
    ],
    excluded: [],
    icon: Zap,
    color: "from-cyan-500 to-blue-600",
    badge: "Most popular",
  },
  {
    name: "Team",
    description: "For agencies & bootcamps",
    price: { monthly: 49, yearly: 39 },
    priceLabel: null,
    period: "per seat / month",
    highlight: "Collaborative",
    cta: "Contact sales",
    ctaStyle: "outline" as const,
    features: [
      "Everything in Pro",
      "Multi-seat management",
      "Shared job pipelines",
      "Admin dashboard",
      "White-label options",
      "API access",
      "Dedicated account manager",
      "Custom integrations",
    ],
    excluded: [],
    icon: Building2,
    color: "from-violet-500 to-fuchsia-600",
    badge: "For teams",
  },
];

function PricingCard({ plan, index, isYearly }: { plan: typeof PLANS[0]; index: number; isYearly: boolean }) {
  const cardRef = useRef(null);
  const isInView = useInView(cardRef, { once: true, margin: "-50px" });
  const isPopular = plan.badge === "Most popular";
  const Icon = plan.icon;
  
  const price = isYearly && plan.price.yearly > 0 ? plan.price.yearly : plan.price.monthly;

  return (
    <motion.div
      ref={cardRef}
      className={cn(
        "relative rounded-2xl overflow-hidden",
        isPopular ? "lg:scale-105 lg:z-10" : ""
      )}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.15 }}
    >
      {/* Popular badge */}
      {plan.badge && (
        <div className="absolute top-0 left-0 right-0 z-20">
          <div className={cn(
            "mx-auto max-w-[200px] px-4 py-1.5 rounded-b-xl text-xs font-semibold text-center text-white bg-gradient-to-r",
            plan.color
          )}>
            {plan.badge}
          </div>
        </div>
      )}

      {/* Card background with gradient border effect */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-500",
        plan.color,
        isPopular && "opacity-20"
      )} />
      
      <div className={cn(
        "relative h-full rounded-2xl border bg-slate-900/90 backdrop-blur-sm",
        isPopular 
          ? "border-cyan-500/50 shadow-xl shadow-cyan-500/10" 
          : "border-slate-800"
      )}>
        <div className="p-6 lg:p-8">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className={cn(
                "inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 bg-gradient-to-br",
                plan.color
              )}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white">{plan.name}</h3>
              <p className="text-sm text-slate-400 mt-1">{plan.description}</p>
            </div>
          </div>

          {/* Price */}
          <div className="mb-6">
            {plan.priceLabel ? (
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-white">{plan.priceLabel}</span>
                <span className="text-slate-500">{plan.period}</span>
              </div>
            ) : (
              <div className="flex items-baseline gap-2">
                <span className="text-slate-500">$</span>
                <span className="text-5xl font-bold text-white">{price}</span>
                <span className="text-slate-500">/{plan.period}</span>
              </div>
            )}
            {isYearly && plan.price.yearly > 0 && (
              <p className="text-sm text-emerald-400 mt-1">
                Save ${(plan.price.monthly - plan.price.yearly) * 12}/year
              </p>
            )}
          </div>

          {/* Highlight */}
          <div className={cn(
            "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium mb-6",
            "bg-slate-800 border border-slate-700"
          )}>
            <span className={cn("w-2 h-2 rounded-full bg-gradient-to-r", plan.color)} />
            <span className="text-slate-300">{plan.highlight}</span>
          </div>

          {/* CTA Button */}
          <button
            className={cn(
              "w-full py-3 px-4 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center gap-2 group",
              plan.ctaStyle === "primary"
                ? "bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/25"
                : "bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
            )}
          >
            {plan.cta}
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>

          {/* Divider */}
          <div className="my-6 h-px bg-slate-800" />

          {/* Features */}
          <ul className="space-y-3">
            {plan.features.map((feature) => (
              <li key={feature} className="flex items-start gap-3">
                <div className={cn(
                  "shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 bg-gradient-to-br",
                  plan.color
                )}>
                  <Check className="w-3 h-3 text-white" />
                </div>
                <span className="text-sm text-slate-300">{feature}</span>
              </li>
            ))}
            {plan.excluded.map((feature) => (
              <li key={feature} className="flex items-start gap-3 opacity-50">
                <div className="shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 bg-slate-800">
                  <span className="text-slate-500 text-xs">—</span>
                </div>
                <span className="text-sm text-slate-500 line-through">{feature}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </motion.div>
  );
}

export function Pricing() {
  const [isYearly, setIsYearly] = useState(false);
  const sectionRef = useRef(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-100px" });

  return (
    <section id="pricing" ref={sectionRef} className="relative py-24 lg:py-32 bg-slate-950 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-cyan-500/5 to-transparent blur-[100px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-gradient-to-br from-violet-500/5 to-transparent blur-[80px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-sm font-medium text-slate-400 mb-6">
            <Users className="w-4 h-4" />
            Simple Pricing
          </span>
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight mb-6">
            Choose your path to
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              your next role
            </span>
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Start free, upgrade when you're ready. No hidden fees, no surprises.
          </p>

          {/* Billing toggle */}
          <div className="mt-8 inline-flex items-center gap-3 p-1 rounded-full bg-slate-900 border border-slate-800">
            <button
              onClick={() => setIsYearly(false)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-all",
                !isYearly ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
              )}
            >
              Monthly
            </button>
            <button
              onClick={() => setIsYearly(true)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2",
                isYearly ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
              )}
            >
              Yearly
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs">
                Save 20%
              </span>
            </button>
          </div>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid gap-6 lg:gap-8 lg:grid-cols-3 items-start">
          {PLANS.map((plan, index) => (
            <PricingCard key={plan.name} plan={plan} index={index} isYearly={isYearly} />
          ))}
        </div>

        {/* Trust footer */}
        <motion.div 
          className="mt-16 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              Cancel anytime
            </span>
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              No credit card required to start
            </span>
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-500" />
              30-day money back guarantee
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
