import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  notifications: boolean;
  soundEffects: boolean;
  autoSave: boolean;
}

interface AppContextType {
  // Audio/Video
  muted: boolean;
  toggleMute: () => void;
  
  // User Preferences
  preferences: UserPreferences;
  updatePreferences: (updates: Partial<UserPreferences>) => void;
  
  // Global UI State
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // Error handling
  globalError: string | null;
  setGlobalError: (error: string | null) => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'system',
  notifications: true,
  soundEffects: true,
  autoSave: true,
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  // Audio/Video state
  const [muted, setMuted] = useState(false);

  // User preferences with localStorage persistence
  const [preferences, setPreferences] = useState<UserPreferences>(() => {
    try {
      const stored = localStorage.getItem('user_preferences');
      return stored ? { ...defaultPreferences, ...JSON.parse(stored) } : defaultPreferences;
    } catch {
      return defaultPreferences;
    }
  });

  // Global UI state
  const [isLoading, setIsLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Audio/Video functions
  const toggleMute = useCallback(() => {
    setMuted(prev => !prev);
  }, []);

  // Preferences functions
  const updatePreferences = useCallback((updates: Partial<UserPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates };
      try {
        localStorage.setItem('user_preferences', JSON.stringify(newPrefs));
      } catch (error) {
        if (import.meta.env.DEV) console.warn('Failed to save user preferences:', error);
      }
      return newPrefs;
    });
  }, []);

  // Apply theme
  useEffect(() => {
    const root = document.documentElement;
    const { theme } = preferences;
    
    if (theme === 'dark') {
      root.classList.add('dark');
    } else if (theme === 'light') {
      root.classList.remove('dark');
    } else {
      // system
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      if (systemTheme === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [preferences.theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (preferences.theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => {
        const root = document.documentElement;
        if (mediaQuery.matches) {
          root.classList.add('dark');
        } else {
          root.classList.remove('dark');
        }
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [preferences.theme]);

  return (
    <AppContext.Provider value={{ 
      muted, 
      toggleMute,
      preferences,
      updatePreferences,
      isLoading,
      setIsLoading,
      globalError,
      setGlobalError,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
