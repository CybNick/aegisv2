import { useState, createContext, useContext } from 'react';

export type UserMode = 'simple' | 'professional' | 'executive';

interface ModeContextProps {
  mode: UserMode;
  setMode: (mode: UserMode) => void;
  isSimple: boolean;
  isProfessional: boolean;
  isExecutive: boolean;
}

const ModeContext = createContext<ModeContextProps | undefined>(undefined);

export function ModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<UserMode>(() => {
    const saved = localStorage.getItem('aegis_user_mode');
    return (saved as UserMode) || 'simple';
  });

  const setMode = (newMode: UserMode) => {
    setModeState(newMode);
    localStorage.setItem('aegis_user_mode', newMode);
  };

  return (
    <ModeContext.Provider value={{
      mode,
      setMode,
      isSimple: mode === 'simple',
      isProfessional: mode === 'professional',
      isExecutive: mode === 'executive'
    }}>
      {children}
    </ModeContext.Provider>
  );
}

export function useMode() {
  const context = useContext(ModeContext);
  if (!context) {
    throw new Error('useMode must be used within a ModeProvider');
  }
  return context;
}
