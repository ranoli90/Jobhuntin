import { useEffect, useState, useRef } from "react";
import { Globe, ChevronDown } from "lucide-react";
import { cn } from "../lib/utils";
import { setDocumentDirection } from "../lib/i18n";

const LANGUAGE_KEY = "jobhuntin-language";

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
}

const languages: Language[] = [
  { code: "en", name: "English", nativeName: "English", flag: "🇺🇸" },
  { code: "fr", name: "French", nativeName: "Français", flag: "🇫🇷" },
];

export function LanguageSelector({ className }: { className?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState<Language>(() => {
    if (globalThis.window === undefined) return languages[0];
    const stored = localStorage.getItem(LANGUAGE_KEY);
    if (stored) {
      const found = languages.find((l) => l.code === stored);
      if (found) return found;
    }
    // Try to match browser language
    const browserLang = navigator.language.split("-")[0];
    const matched = languages.find((l) => l.code === browserLang);
    return matched || languages[0];
  });
  const dropdownReference = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(LANGUAGE_KEY, currentLang.code);
    setDocumentDirection(currentLang.code);
    window.dispatchEvent(
      new CustomEvent("localechange", { detail: currentLang.code }),
    );
  }, [currentLang]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownReference.current &&
        !dropdownReference.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close on escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  return (
    <div className={cn("relative", className)} ref={dropdownReference}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg",
          "text-sm font-medium text-slate-600 dark:text-slate-300",
          "hover:bg-slate-100 dark:hover:bg-slate-800",
          "focus:outline-none focus:ring-2 focus:ring-brand-primary/30",
          "transition-colors",
        )}
        aria-label={`Current language: ${currentLang.name}. Click to change language.`}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <Globe className="w-4 h-4" />
        <span className="hidden sm:inline">
          {currentLang.flag} {currentLang.nativeName}
        </span>
        <span className="sm:hidden">{currentLang.flag}</span>
        <ChevronDown
          className={cn("w-3 h-3 transition-transform", isOpen && "rotate-180")}
        />
      </button>

      {isOpen && (
        <div
          className={cn(
            "absolute right-0 top-full mt-2",
            "w-56 py-2",
            "bg-white dark:bg-slate-900",
            "rounded-xl shadow-xl border border-slate-200 dark:border-slate-700",
            "z-50 overflow-hidden",
          )}
          role="listbox"
          aria-label="Select language"
        >
          <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Select Language
          </div>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setCurrentLang(lang);
                setIsOpen(false);
              }}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5",
                "text-left text-sm",
                "hover:bg-slate-100 dark:hover:bg-slate-800",
                "focus:outline-none focus:bg-slate-100 dark:focus:bg-slate-800",
                "transition-colors",
                lang.code === currentLang.code
                  ? "bg-brand-primary/10 dark:bg-brand-primary/20 text-brand-primary dark:text-brand-primary"
                  : "text-slate-700 dark:text-slate-300",
              )}
              role="option"
              aria-selected={lang.code === currentLang.code}
            >
              <span className="text-lg">{lang.flag}</span>
              <div className="flex-1">
                <div className="font-medium">{lang.nativeName}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {lang.name}
                </div>
              </div>
              {lang.code === currentLang.code && (
                <svg
                  className="w-4 h-4 text-brand-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default LanguageSelector;
