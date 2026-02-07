import * as React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Hero } from "../components/marketing/Hero";
import { HowItWorks } from "../components/marketing/HowItWorks";
import { Testimonials } from "../components/marketing/Testimonials";
import { FAQ } from "../components/marketing/FAQ";
import { HeartPulse } from "lucide-react";

export default function Homepage() {
  const navigate = useNavigate();

  return (
    <div className="overflow-hidden">
      <Hero onGetStarted={() => navigate("/app/dashboard")} />
      <HowItWorks />
      <Testimonials />
      <FAQ />

      {/* Final CTA */}
      <section className="bg-brand-shell px-6 py-20">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 text-center">
          <div className="rounded-full bg-brand-lagoon/20 p-4">
            <HeartPulse className="h-10 w-10 text-brand-lagoon" />
          </div>
          <h3 className="font-display text-4xl text-brand-ink">
            Ready to skedaddle?
          </h3>
          <p className="text-lg text-brand-ink/70">
            Join 10,000+ job seekers who stopped stressing and started landing interviews.
          </p>
          <Button size="lg" wobble onClick={() => navigate("/app/dashboard")}>
            Start free — 10 applications on us
          </Button>
        </div>
      </section>
    </div>
  );
}
