import { createContext, useContext, useState, type ReactNode } from 'react';

interface TimelineState {
  context: string;
  asOf: string; // 'now' or ISO timestamp
  setContext: (ctx: string) => void;
  setAsOf: (time: string) => void;
}

const TimelineContext = createContext<TimelineState | undefined>(undefined);

export function TimelineProvider({ children }: { children: ReactNode }) {
  const [context, setContext] = useState<string>('default');
  const [asOf, setAsOf] = useState<string>('now');

  return (
    <TimelineContext.Provider value={{ context, asOf, setContext, setAsOf }}>
      {children}
    </TimelineContext.Provider>
  );
}

export function useTimeline() {
  const ctx = useContext(TimelineContext);
  if (!ctx) throw new Error('useTimeline must be used within TimelineProvider');
  return ctx;
}
