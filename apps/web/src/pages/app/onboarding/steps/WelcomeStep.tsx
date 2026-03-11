import * as React from "react";
import { motion } from "framer-motion";
import {
  Rocket,
  MapPin,
  ArrowRight,
  Sparkles,
  Clock,
  Zap,
  Target,
} from "lucide-react";
import { Button } from "../../../../components/ui/Button";
import { t, getLocale } from "../../../../lib/i18n";
import { cn } from "../../../../lib/utils";

interface WelcomeStepProperties {
    onNext: () => void;
    shouldReduceMotion?: boolean;
    firstName?: string;
}

export function WelcomeStep({ onNext, shouldReduceMotion, firstName }: WelcomeStepProperties) {
  const locale = getLocale();
  const [titleRevealed, setTitleRevealed] = React.useState(
    shouldReduceMotion ?? false,
  );

  const features = [
    {
      titleKey: "onboarding.feature1Title",
      descKey: "onboarding.feature1Desc",
      icon: Sparkles,
      color: "from-[#455DD3] to-[#3A4FB8]",
    },
    {
      titleKey: "onboarding.feature2Title",
      descKey: "onboarding.feature2Desc",
      icon: Target,
      color: "from-[#17BEBB] to-[#14A3A0]",
    },
    {
      titleKey: "onboarding.feature3Title",
      descKey: "onboarding.feature3Desc",
      icon: Zap,
      color: "from-[#455DD3] to-[#7DD3CF]",
    },
  ];

  const welcomeTitle = t("onboarding.welcomeTitle", locale);
  const titleWords = welcomeTitle.split(" ");
  const titleStart = titleWords.slice(0, -1).join(" ");
  const titleEnd = titleWords.pop()?.replace(".", "") || "";

  const personalGreeting = firstName ? `Hey ${firstName}` : null;

  // Typewriter reveal
  React.useEffect(() => {
    if (shouldReduceMotion) {
      setTitleRevealed(true);
      return;
    }
    const timer = setTimeout(() => setTitleRevealed(true), 600);
    return () => clearTimeout(timer);
  }, [shouldReduceMotion]);

  return (
    <div role="region" aria-labelledby="welcome-step-title">
      <div className="text-center py-4">
        {/* Animated Icon with sparkle background */}
        <div className="mx-auto mb-6 relative font-display">
          {/* Sparkle particles */}
          {!shouldReduceMotion && (
            <>
              {[...new Array(6)].map((_, index) => (
                                <motion.div
                                    key={index}
                                    className="absolute w-1.5 h-1.5 rounded-full bg-[#455DD3]/60"
                                    style={{
                                        left: `${30 + Math.cos((index * 60 * Math.PI) / 180) * 40}%`,
                                        top: `${30 + Math.sin((index * 60 * Math.PI) / 180) * 40}%`,
                                    }}
                                    animate={{
                                        scale: [0, 1, 0],
                                        opacity: [0, 0.8, 0],
                                    }}
                                    transition={{
                                        duration: 2,
                                        delay: index * 0.3,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
              ))}
            </>
          )}
          <motion.div
            animate={shouldReduceMotion ? undefined : { rotate: 360 }}
            transition={
              shouldReduceMotion
                ? undefined
                : { duration: 20, repeat: Infinity, ease: "linear" }
            }
            className="absolute inset-0 rounded-2xl border-2 border-dashed border-[#455DD3]/20"
          />
          <motion.div
            initial={
              shouldReduceMotion ? undefined : { scale: 0, rotate: -180 }
            }
            animate={{ scale: 1, rotate: 0 }}
            transition={
              shouldReduceMotion
                ? undefined
                : { type: "spring", stiffness: 200, damping: 15, delay: 0.2 }
            }
            className={cn(
              "relative mx-auto flex h-20 w-20 items-center justify-center",
              "rounded-[2rem] bg-gradient-to-br from-[#455DD3] to-[#17BEBB] shadow-2xl shadow-[#455DD3]/30",
              !shouldReduceMotion && "animate-pulse-glow",
            )}
          >
            <Rocket className="h-10 w-10 text-white" />
          </motion.div>
        </div>

        {/* Time badge */}
        <motion.div
          initial={shouldReduceMotion ? undefined : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#17BEBB]/10 border border-[#17BEBB]/20 mb-4"
        >
          <Clock className="w-3 h-3 text-[#17BEBB]" />
          <span className="text-[10px] font-bold text-[#17BEBB] uppercase tracking-wider">
            {t("onboarding.setupTime", locale) || "2–3 min"}
          </span>
        </motion.div>

        {/* Personal Greeting */}
        {personalGreeting && (
          <motion.p
            initial={shouldReduceMotion ? undefined : { opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-1 text-sm font-black text-[#455DD3] uppercase tracking-widest"
          >
            {personalGreeting}
          </motion.p>
        )}

        {/* Title with typewriter effect */}
        <h1
          id="welcome-step-title"
          className="mb-3 font-display text-4xl md:text-5xl font-black text-[#2D2A26] tracking-tight leading-tight"
        >
          <motion.span
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
            animate={{ opacity: titleRevealed ? 1 : 0 }}
            transition={{ duration: 0.4 }}
          >
            {titleStart}{" "}
          </motion.span>
          <motion.span
            initial={
              shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 10 }
            }
            animate={{
              opacity: titleRevealed ? 1 : 0,
              y: titleRevealed ? 0 : 10,
            }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="text-[#455DD3] italic"
          >
            {titleEnd}.
          </motion.span>
          {!titleRevealed && !shouldReduceMotion && (
            <span className="inline-block w-0.5 h-8 ml-1 bg-[#455DD3] align-middle animate-typewriter-cursor" />
          )}
        </h1>

        {/* Subtitle */}
        <motion.p
          initial={shouldReduceMotion ? undefined : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className={cn(
            "mb-8 text-[#787774] font-bold leading-relaxed max-w-sm mx-auto",
            "text-base md:text-lg",
          )}
        >
          {t("onboarding.welcomeSubtitle", locale)}
        </motion.p>

        {/* Feature Cards with enhanced animations */}
        <div className="grid gap-3 mb-10 text-left">
          {features.map((item, index) => (
                        <motion.div
                            key={index}
                            initial={shouldReduceMotion ? undefined : { opacity: 0, x: -20, scale: 0.95 }}
                            animate={{ opacity: 1, x: 0, scale: 1 }}
                            transition={shouldReduceMotion ? undefined : { delay: 0.5 + index * 0.15, type: "spring", stiffness: 300, damping: 20 }}
              whileHover={
                shouldReduceMotion ? undefined : { scale: 1.02, y: -2 }
              }
              className={cn(
                "flex items-center gap-4 p-5 rounded-2xl",
                "bg-white border border-[#E9E9E7]",
                "hover:border-[#455DD3]/20 hover:shadow-xl hover:shadow-[#455DD3]/5",
                "transition-all group cursor-default",
              )}
            >
              <motion.div
                whileHover={
                  shouldReduceMotion ? undefined : { rotate: [0, -10, 10, 0] }
                }
                transition={{ duration: 0.4 }}
                className={cn(
                  "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl",
                  "bg-gradient-to-br",
                  item.color,
                  "text-white shadow-lg",
                  "group-hover:shadow-xl",
                  "transition-all",
                )}
              >
                <item.icon className="h-6 w-6" />
              </motion.div>
              <div className="text-left min-w-0">
                <p className="text-sm font-black text-[#2D2A26] uppercase tracking-wider">
                  {t(item.titleKey, locale)}
                </p>
                <p className="text-xs text-[#787774] font-bold leading-snug mt-0.5">
                  {t(item.descKey, locale)}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Start Button with shimmer */}
      <Button
        type="button"
        onClick={onNext}
        className={cn(
          "w-full h-16 rounded-[2rem] font-black text-xl",
          "shadow-xl shadow-[#455DD3]/20",
          "bg-gradient-to-r from-[#455DD3] to-[#17BEBB] hover:from-[#3A4FB8] hover:to-[#14A3A0]",
          "group overflow-hidden relative",
        )}
        aria-label={t("onboarding.startSetup", locale)}
        data-onboarding-next
      >
        <span className="relative z-10 flex items-center gap-2">
          {t("onboarding.startSetup", locale)}
          <ArrowRight className="ml-2 h-6 w-6 group-hover:translate-x-2 transition-transform" />
        </span>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
      </Button>
    </div>
  );
}
