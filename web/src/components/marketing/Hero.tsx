import * as React from "react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { ArrowRight, Sparkles } from "lucide-react";

interface HeroProps {
  onGetStarted: () => void;
}

export function Hero({ onGetStarted }: HeroProps) {
  return (
    <section className="relative overflow-hidden px-6 py-20 lg:py-32">
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-20 left-10 h-72 w-72 rounded-full bg-brand-sunrise/20 blur-3xl" />
        <div className="absolute bottom-20 right-10 h-96 w-96 rounded-full bg-brand-lagoon/20 blur-3xl" />
      </div>

      <div className="mx-auto max-w-4xl text-center">
        <Badge variant="sunrise" className="mb-6 animate-fade-in">
          <Sparkles className="mr-1 h-3 w-3" />
          Now open to everyone
        </Badge>

        <h1 className="font-display text-5xl leading-tight text-brand-ink lg:text-7xl">
          Apply to 100 jobs
          <br />
          <span className="text-brand-sunrise">before breakfast</span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-brand-ink/70 lg:text-xl">
          Skedaddle is your AI job-hunting teammate. We find perfect matches, fill out applications, 
          and handle the boring stuff—so you can focus on nailing interviews.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Button size="lg" variant="primary" wobble onClick={onGetStarted} className="group">
            Start applying free
            <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Button>
          <Button size="lg" variant="ghost">
            See how it works
          </Button>
        </div>

        <p className="mt-4 text-sm text-brand-ink/50">
          No credit card required • 10 free applications • Cancel anytime
        </p>
      </div>

      {/* Trust strip */}
      <div className="mx-auto mt-16 max-w-5xl">
        <p className="mb-4 text-center text-xs uppercase tracking-[0.3em] text-brand-ink/40">
          Trusted by job seekers at
        </p>
        <div className="flex flex-wrap items-center justify-center gap-8 opacity-60 grayscale">
          {["Google", "Meta", "Stripe", "Airbnb", "Spotify"].map((company) => (
            <span key={company} className="font-display text-xl text-brand-ink">
              {company}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
