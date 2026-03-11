import { motion, useReducedMotion } from "framer-motion";
import { ReactNode } from "react";

interface PageTransitionProperties {
  children: ReactNode;
  className?: string;
}

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  enter: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.61, 1, 0.88, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.3,
      ease: [0.61, 1, 0.88, 1],
    },
  },
};

const reducedMotionVariants = {
  initial: { opacity: 1, y: 0 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 1, y: 0 },
};

export function PageTransition({
  children,
  className,
}: PageTransitionProperties) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial="initial"
      animate="enter"
      exit="exit"
      variants={shouldReduceMotion ? reducedMotionVariants : pageVariants}
      className={className}
    >
      {children}
    </motion.div>
  );
}
