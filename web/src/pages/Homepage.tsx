import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Hero } from "../components/marketing/Hero";
import { HowItWorks } from "../components/marketing/HowItWorks";
import { Testimonials } from "../components/marketing/Testimonials";
import { FAQ } from "../components/marketing/FAQ";
import { Pricing } from "../components/marketing/Pricing";
import { ArrowRight, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export default function Homepage() {
  const navigate = useNavigate();

  return (
    <div className="overflow-hidden bg-slate-950">
      <Hero onGetStarted={() => navigate("/login")} />
      <HowItWorks />
      <Testimonials />
      <Pricing />
      <FAQ />

      {/* Final CTA */}
      <section className="relative py-24 lg:py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950" />
        <div className="absolute inset-0">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-cyan-500/10 to-blue-600/10 blur-[120px]" />
        </div>

        <motion.div 
          className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          {/* Icon */}
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 mb-8">
            <Sparkles className="w-10 h-10 text-cyan-400" />
          </div>

          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight mb-6">
            Ready to transform
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              your job search?
            </span>
          </h2>
          
          <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            Join thousands of job seekers who stopped grinding and started winning. 
            Your first 10 applications are free.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button 
              size="lg"
              onClick={() => navigate("/login")}
              className="group bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white border-0 shadow-lg shadow-cyan-500/25 h-14 px-8 text-base"
            >
              Start free — 10 applications
              <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Button>
          </div>

          <p className="mt-6 text-sm text-slate-500">
            No credit card required. Cancel anytime.
          </p>
        </motion.div>
      </section>
    </div>
  );
}
