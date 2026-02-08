import * as React from "react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { ArrowRight, Sparkles, Play } from "lucide-react";

interface HeroProps {
  onGetStarted: () => void;
}

export function Hero({ onGetStarted }: HeroProps) {
  return (
    <section className="relative overflow-hidden bg-white">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50/50 to-white" />
      
      {/* Decorative elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-primary-100/50 blur-3xl" />
        <div className="absolute top-20 -left-20 h-72 w-72 rounded-full bg-blue-100/50 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-32 lg:pb-24">
        <div className="mx-auto max-w-4xl text-center">
          <Badge variant="primary" className="mb-6 animate-fade-in">
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            Now open to everyone
          </Badge>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900">
            Apply to <span className="text-primary-600">100 jobs</span>
            <br />
            before breakfast
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 leading-relaxed">
            Skedaddle is your AI job-hunting teammate. We find perfect matches, fill out applications, 
            and handle the tedious work—so you can focus on nailing interviews.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button size="lg" onClick={onGetStarted} className="group min-w-[180px]">
              Start applying free
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              onClick={() => document.getElementById("how")?.scrollIntoView({ behavior: "smooth" })}
              className="group min-w-[180px]"
            >
              <Play className="mr-2 h-4 w-4" />
              See how it works
            </Button>
          </div>

          <p className="mt-4 text-sm text-slate-500">
            No credit card required • 10 free applications • Cancel anytime
          </p>
        </div>

        {/* Trust strip */}
        <div className="mt-20 border-t border-slate-200 pt-8">
          <p className="mb-6 text-center text-sm font-medium text-slate-500">
            Trusted by job seekers from leading companies
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-4">
            {["Google", "Meta", "Stripe", "Airbnb", "Spotify", "Netflix"].map((company) => (
              <span key={company} className="text-lg font-semibold text-slate-400">
                {company}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
