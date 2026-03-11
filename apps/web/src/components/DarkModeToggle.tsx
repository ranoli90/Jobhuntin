import * as React from "react";
import { motion } from "framer-motion";
import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "../lib/utils";

type Theme = "light" | "dark" | "system";

interface DarkModeToggleProperties {
  className?: string;
  showLabel?: boolean;
}

export function DarkModeToggle({
  className,
  showLabel,
}: DarkModeToggleProperties) {
  const [theme, setTheme] = React.useState<Theme>("system");
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    // Check for saved preference or system preference
    const saved = localStorage.getItem("theme") as Theme;
    if (saved) {
      setTheme(saved);
    }
  }, []);

  React.useEffect(() => {
    if (!mounted) return;

    const root = window.document.documentElement;
    root.classList.remove("light", "dark");

    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }

    localStorage.setItem("theme", theme);
  }, [theme, mounted]);

  // Listen for system changes
  React.useEffect(() => {
    if (!mounted || theme !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      const root = window.document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(e.matches ? "dark" : "light");
    };

    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [theme, mounted]);

  if (!mounted) {
    return (
      <div
        className={cn(
          "w-10 h-10 rounded-xl bg-slate-100 animate-pulse",
          className,
        )}
      />
    );
  }

  const options: { value: Theme; icon: React.ReactNode; label: string }[] = [
    { value: "light", icon: <Sun className="w-4 h-4" />, label: "Light" },
    { value: "dark", icon: <Moon className="w-4 h-4" />, label: "Dark" },
    { value: "system", icon: <Monitor className="w-4 h-4" />, label: "System" },
  ];

  return (
    <div
      className={cn(
        "flex items-center gap-1 bg-slate-100 dark:bg-slate-800 rounded-xl p-1",
        className,
      )}
    >
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => setTheme(option.value)}
          className={cn(
            "relative flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
            theme === option.value
              ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
              : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300",
          )}
          aria-label={`Switch to ${option.label} mode`}
          aria-pressed={theme === option.value}
        >
          {option.icon}
          {showLabel && <span>{option.label}</span>}
        </button>
      ))}
    </div>
  );
}

// Simple toggle switch version
interface ThemeToggleSwitchProperties {
  className?: string;
}

export function ThemeToggleSwitch({ className }: ThemeToggleSwitchProperties) {
  const [isDark, setIsDark] = React.useState(false);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("theme");
    const isDarkMode =
      saved === "dark" ||
      (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches);
    setIsDark(isDarkMode);
  }, []);

  React.useEffect(() => {
    if (!mounted) return;

    const root = window.document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [isDark, mounted]);

  if (!mounted) {
    return (
      <div
        className={cn(
          "w-14 h-8 rounded-full bg-slate-200 animate-pulse",
          className,
        )}
      />
    );
  }

  return (
    <button
      onClick={() => setIsDark(!isDark)}
      className={cn(
        "relative w-14 h-8 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2",
        isDark ? "bg-slate-700" : "bg-slate-200",
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <motion.div
        animate={{ x: isDark ? 24 : 4 }}
        transition={{ type: "spring", damping: 20, stiffness: 300 }}
        className={cn(
          "absolute top-1 w-6 h-6 rounded-full flex items-center justify-center shadow-sm",
          isDark ? "bg-slate-900" : "bg-white",
        )}
      >
        {isDark ? (
          <Moon className="w-3 h-3 text-slate-100" />
        ) : (
          <Sun className="w-3 h-3 text-amber-500" />
        )}
      </motion.div>
    </button>
  );
}

export default DarkModeToggle;
