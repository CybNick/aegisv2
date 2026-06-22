import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import './index.css';

import { TimelineProvider } from './hooks/useTimeline';
import { ModeProvider } from './hooks/useMode';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ModeProvider>
      <QueryClientProvider client={queryClient}>
        <TimelineProvider>
          <RouterProvider router={router} />
        </TimelineProvider>
      </QueryClientProvider>
    </ModeProvider>
  </React.StrictMode>,
);
