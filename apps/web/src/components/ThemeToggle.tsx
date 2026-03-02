import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';

const THEME_KEY = 'jobhuntin-theme';

type ThemeMode = 'light' | 'dark' | 'system';

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    if (typeof globalThis.window === 'undefined') return 'system';
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === 'dark' || stored === 'light' || stored === 'system') return stored as ThemeMode;
    return 'system';
  });

  const resolvedDark = theme === 'dark' || (theme === 'system' && typeof globalThis.window !== 'undefined' && globalThis.window.matchMedia('(prefers-color-scheme: dark)').matches);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', resolvedDark);
    if (theme !== 'system') {
      localStorage.setItem(THEME_KEY, theme);
    } else {
      localStorage.removeItem(THEME_KEY);
    }
  }, [theme, resolvedDark]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mq = globalThis.window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      root.classList.toggle('dark', mq.matches);
    };
    const root = document.documentElement;
    mq.addEventListener('change', handleChange);
    return () => mq.removeEventListener('change', handleChange);
  }, [theme]);

  const cycleTheme = () => {
    setTheme((t) => (t === 'light' ? 'dark' : t === 'dark' ? 'system' : 'light'));
  };

  const ariaLabel = theme === 'dark' ? 'Switch to light mode' : theme === 'light' ? 'Switch to dark mode' : 'Switch to system theme';

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycleTheme}
      aria-label={ariaLabel}
      title={`Theme: ${theme} (click to cycle)`}
      className={cn('relative shrink-0', className)}
    >
      <span className="relative flex h-4 w-4">
        <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" aria-hidden />
        <Moon className="absolute inset-0 h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" aria-hidden />
      </span>
    </Button>
  );
}
