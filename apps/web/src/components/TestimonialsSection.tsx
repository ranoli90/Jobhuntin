import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Quote, ChevronLeft, ChevronRight, Star } from "lucide-react";
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
}

const testimonials: Testimonial[] = [
  {
    id: "1",
    quote: "I was skeptical at first, but JobHuntin landed me 3 interviews in my first week. The AI tailoring is incredible - each application felt personalized.",
    author: "Sarah Chen",
    role: "Senior Product Manager",
    company: "Previously at Startup",
    rating: 5,
    avatarGradient: "from-rose-400 to-orange-500"
  },
  {
    id: "2",
    quote: "Applied to 200+ jobs while I slept. Woke up to 12 responses. This is the future of job searching.",
    author: "Marcus Johnson",
    role: "Full Stack Developer",
    company: "Now at Stripe",
    rating: 5,
    avatarGradient: "from-blue-400 to-indigo-600"
  },
  {
    id: "3",
    quote: "The resume tailoring alone is worth it. My callback rate went from 2% to 15% after switching to JobHuntin.",
    author: "Emily Rodriguez",
    role: "UX Designer",
    company: "Now at Figma",
    rating: 5,
    avatarGradient: "from-purple-400 to-pink-500"
  },
  {
    id: "4",
    quote: "As a career changer, I needed help positioning my skills. JobHuntin's AI understood my transferable experience better than I did.",
    author: "David Park",
    role: "Data Scientist",
    company: "Now at Netflix",
    rating: 5,
    avatarGradient: "from-emerald-400 to-teal-600"
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
      x: direction > 0 ? 300 : -300,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      x: direction < 0 ? 300 : -300,
      opacity: 0
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

  // Auto-advance - respects reduced motion and pause state
  React.useEffect(() => {
    if (prefersReducedMotion || isPaused) return;
    const timer = setInterval(() => {
      paginate(1);
    }, 6000);
    return () => clearInterval(timer);
  }, [prefersReducedMotion, isPaused]);

  const current = testimonials[currentIndex];

  return (
    <section className={cn("py-20 bg-slate-50 dark:bg-slate-900", className)}>
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-slate-900 dark:text-slate-100 mb-4">
            Loved by job seekers
          </h2>
          <p className="text-slate-500 dark:text-slate-400 text-lg">
            Join thousands who've transformed their job search
          </p>
        </div>

        <div className="relative bg-white dark:bg-slate-800 rounded-3xl shadow-xl p-8 md:p-12">
          {/* Quote icon */}
          <div className="absolute top-6 left-6 w-12 h-12 bg-primary-50 dark:bg-primary-900/20 rounded-xl flex items-center justify-center">
            <Quote className="w-6 h-6 text-primary-600" />
          </div>

          {/* Navigation */}
          <div className="absolute top-6 right-6 flex gap-2">
            <button
              onClick={() => paginate(-1)}
              className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 transition-colors"
              aria-label="Previous testimonial"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => paginate(1)}
              className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 transition-colors"
              aria-label="Next testimonial"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Testimonial content */}
          <div className="pt-8 min-h-[280px] flex flex-col" onMouseEnter={() => setIsPaused(true)} onMouseLeave={() => setIsPaused(false)}>
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={current.id}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="flex-1 flex flex-col"
              >
                {/* Rating */}
                <div className="flex gap-1 mb-6">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      className={cn(
                        "w-5 h-5",
                        i < current.rating
                          ? "text-amber-400 fill-amber-400"
                          : "text-slate-300"
                      )}
                    />
                  ))}
                </div>

                {/* Quote */}
                <blockquote className="text-xl md:text-2xl text-slate-700 dark:text-slate-300 font-medium leading-relaxed mb-8 flex-1">
                  "{current.quote}"
                </blockquote>

                {/* Author */}
                <div className="flex items-center gap-4">
                  <div className={cn("w-14 h-14 rounded-full bg-gradient-to-br flex items-center justify-center text-white text-xl font-bold shadow-lg", current.avatarGradient)}>
                    {current.author.split(" ").map(n => n[0]).join("")}
                  </div>
                  <div>
                    <p className="font-bold text-slate-900 dark:text-slate-100">
                      {current.author}
                    </p>
                    <p className="text-sm text-slate-500">
                      {current.role} · {current.company}
                    </p>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Dots indicator */}
          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => {
                  setDirection(index > currentIndex ? 1 : -1);
                  setCurrentIndex(index);
                }}
                className={cn(
                  "w-2 h-2 rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2",
                  index === currentIndex
                    ? "w-6 bg-primary-600"
                    : "bg-slate-300 hover:bg-slate-400"
                )}
                aria-label={`Go to testimonial ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default TestimonialsSection;
