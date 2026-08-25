import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { TeamProvider } from './context/TeamContext';
import { App } from './App';
import './index.css';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={queryClient}><ThemeProvider><AuthProvider><BrowserRouter><TeamProvider><App /><Toaster richColors position="top-right" /></TeamProvider></BrowserRouter></AuthProvider></ThemeProvider></QueryClientProvider></React.StrictMode>,
);
