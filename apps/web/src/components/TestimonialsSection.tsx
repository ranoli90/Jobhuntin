import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Quote, ChevronLeft, ChevronRight, Star, Sparkles } from "lucide-react";
import { cn } from "../lib/utils";

interface Testimonial {
  id: string;
  quote: string;
  author: string;
  role: string;
  company: string;
  avatar?: string;
  rating: number;
  avatarGradient: string;
  highlight?: string;
}

const testimonials: Testimonial[] = [
  {
    id: "1",
    quote: "I was skeptical at first, but JobHuntin landed me 3 interviews in my first week. The AI tailoring is incredible — each application felt personalized.",
    author: "Maria Garcia",
    role: "Cashier",
    company: "Now at Walmart",
    rating: 5,
    avatarGradient: "from-[#FFB8A0] to-[#F5886A]",
    highlight: "3 interviews in week 1"
  },
  {
    id: "2",
    quote: "Applied to tons of jobs while I worked my shift. Woke up to multiple responses. This is exactly what I needed.",
    author: "James Wilson",
    role: "Sales Associate",
    company: "Now at Target",
    rating: 5,
    avatarGradient: "from-[#17BEBB] to-[#0D9488]",
    highlight: "Woke up to responses"
  },
  {
    id: "3",
    quote: "The resume tailoring alone is worth it. My callback rate went from 2% to 15% after switching to JobHuntin.",
    author: "Lisa Thompson",
    role: "Retail Manager",
    company: "Now at Home Depot",
    rating: 5,
    avatarGradient: "from-[#A259FF] to-[#7C3AED]",
    highlight: "2% → 15% callbacks"
  },
  {
    id: "4",
    quote: "As a first-time job seeker, I needed help positioning myself. JobHuntin's AI helped me apply to more jobs in a week than I could in a month.",
    author: "David Lee",
    role: "Customer Service Rep",
    company: "Now at Amazon",
    rating: 5,
    avatarGradient: "from-[#FF9F1C] to-[#EA580C]",
    highlight: "Week vs month"
  }
];

interface TestimonialsSectionProps {
  className?: string;
}

export function TestimonialsSection({ className }: TestimonialsSectionProps) {
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [direction, setDirection] = React.useState(0);
  const [isPaused, setIsPaused] = React.useState(false);
  const prefersReducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 80 : -80,
      opacity: 0,
      scale: 0.98
    }),
    center: {
      x: 0,
      opacity: 1,
      scale: 1
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 80 : -80,
      opacity: 0,
      scale: 0.98
    })
  };

  const paginate = (newDirection: number) => {
    setDirection(newDirection);
    setCurrentIndex((prev) => {
      const next = prev + newDirection;
      if (next < 0) return testimonials.length - 1;
      if (next >= testimonials.length) return 0;
      return next;
    });
  };

  React.useEffect(() => {
    if (prefersReducedMotion || isPaused) return;
    const timer = setInterval(() => paginate(1), 6000);
    return () => clearInterval(timer);
  }, [prefersReducedMotion, isPaused]);

  const current = testimonials[currentIndex];

  return (
    <section className={cn("py-[80px] sm:py-[100px] relative overflow-hidden", className)} style={{ background: 'linear-gradient(180deg, #FFFBF7 0%, #FFF5ED 50%, #FFEFE3 100%)' }}>
      {/* Decorative elements — warm, brandable */}
      <div className="absolute top-0 left-0 w-[300px] h-[300px] rounded-full opacity-[0.15] pointer-events-none" style={{ background: 'radial-gradient(circle, #FF9F1C 0%, transparent 70%)' }} />
      <div className="absolute bottom-0 right-0 w-[250px] h-[250px] rounded-full opacity-[0.12] pointer-events-none" style={{ background: 'radial-gradient(circle, #17BEBB 0%, transparent 70%)' }} />

      <div className="relative max-w-[900px] mx-auto px-6">
        <div className="text-center mb-[48px]">
          <p className="text-[12px] font-bold text-[#0D9488] uppercase tracking-[0.2em] mb-[8px]">Real stories</p>
          <h2 className="text-[clamp(2rem,4vw,40px)] font-bold text-[#2D2A26] leading-tight mb-[12px]" style={{ letterSpacing: '-1.5px' }}>
            Loved by job seekers
          </h2>
          <p className="text-[16px] text-[#787774] max-w-[400px] mx-auto">
            Join thousands who've transformed their job search — no more endless scrolling.
          </p>
        </div>

        <div className="relative rounded-[20px] overflow-hidden border border-[#F5E6DC]/80 shadow-[0_24px_48px_rgba(45,42,38,0.08)]" style={{ background: 'linear-gradient(165deg, #FFFFFF 0%, #FFFBF7 100%)' }}>
          {/* Accent bar */}
          <div className="h-1.5 w-full" style={{ background: 'linear-gradient(90deg, #FF9F1C, #17BEBB, #0D9488)' }} />

          <div className="p-8 md:p-12 relative">
            {/* Quote mark — brand teal */}
            <div className="absolute top-8 left-8 w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(13,148,136,0.1)', border: '1px solid rgba(13,148,136,0.2)' }}>
              <Quote className="w-7 h-7 text-[#0D9488]" />
            </div>

            {/* Nav buttons — warm, not generic gray */}
            <div className="absolute top-8 right-8 flex gap-2">
              <button
                onClick={() => paginate(-1)}
                className="w-11 h-11 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-[#0D9488]/30 focus:ring-offset-2"
                style={{ background: 'rgba(45,42,38,0.06)', color: '#2D2A26' }}
                aria-label="Previous testimonial"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => paginate(1)}
                className="w-11 h-11 rounded-xl flex items-center justify-center transition-all hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-[#0D9488]/30 focus:ring-offset-2"
                style={{ background: 'rgba(45,42,38,0.06)', color: '#2D2A26' }}
                aria-label="Next testimonial"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            <div className="pt-4 min-h-[260px] flex flex-col" onMouseEnter={() => setIsPaused(true)} onMouseLeave={() => setIsPaused(false)}>
              <AnimatePresence mode="wait" custom={direction}>
                <motion.div
                  key={current.id}
                  custom={direction}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ type: "spring", damping: 28, stiffness: 220 }}
                  className="flex-1 flex flex-col"
                >
                  {/* Highlight pill */}
                  {current.highlight && (
                    <div className="flex items-center gap-1.5 mb-5">
                      <Sparkles className="w-4 h-4 text-[#FF9F1C]" />
                      <span className="text-[12px] font-bold text-[#92400E] bg-[#FEF3C7] px-3 py-1 rounded-full">
                        {current.highlight}
                      </span>
                    </div>
                  )}

                  {/* Stars */}
                  <div className="flex gap-1 mb-5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className={cn("w-5 h-5", i < current.rating ? "text-[#FF9F1C] fill-[#FF9F1C]" : "text-[#E8E7E4]")} />
                    ))}
                  </div>

                  <blockquote className="text-[clamp(1.125rem,2.5vw,22px)] text-[#2D2A26] font-medium leading-[1.5] mb-8 flex-1">
                    "{current.quote}"
                  </blockquote>

                  <div className="flex items-center gap-4">
                    <div className={cn("w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center text-white text-lg font-bold shadow-lg", current.avatarGradient)}>
                      {current.author.split(" ").map(n => n[0]).join("")}
                    </div>
                    <div>
                      <p className="font-bold text-[#2D2A26]">{current.author}</p>
                      <p className="text-[14px] text-[#787774]">{current.role} · {current.company}</p>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Dots — stable, no glitches */}
            <div className="flex justify-center gap-2 pb-6">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => { setDirection(index > currentIndex ? 1 : -1); setCurrentIndex(index); }}
                  className={cn("rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-[#0D9488]/30 focus:ring-offset-2", index === currentIndex ? "w-8 h-2.5" : "w-2.5 h-2.5")}
                  style={{ background: index === currentIndex ? '#0D9488' : 'rgba(45,42,38,0.2)' }}
                  aria-label={`Go to testimonial ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default TestimonialsSection;
