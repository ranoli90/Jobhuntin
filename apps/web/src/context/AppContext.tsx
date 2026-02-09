import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

interface AppContextType {
  muted: boolean;
  toggleMute: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [muted, setMuted] = useState(false);

  const toggleMute = useCallback(() => {
    setMuted(prev => !prev);
  }, []);

  return (
    <AppContext.Provider value={{ muted, toggleMute }}>
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
