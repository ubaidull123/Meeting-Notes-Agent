import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { LandingPage } from './LandingPage';
import { useAuth } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('renders landing page content when unauthenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
      isAdmin: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    // Hero headline and copy
    expect(screen.getByRole('heading', { name: /Turn meetings into actionable work\./i })).toBeInTheDocument();
    expect(screen.getByText(/Meeting Notes Agent uses AI to transform meeting transcripts/i)).toBeInTheDocument();

    // CTAs and links
    const getStartedLinks = screen.getAllByRole('link', { name: /Get Started/i });
    expect(getStartedLinks.length).toBeGreaterThan(0);
    expect(getStartedLinks[0]).toHaveAttribute('href', '/register');

    const loginLinks = screen.getAllByRole('link', { name: /Login/i });
    expect(loginLinks.length).toBeGreaterThan(0);
    expect(loginLinks[0]).toHaveAttribute('href', '/login');

    // Sections
    expect(screen.getAllByText(/How It Works/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Core Capabilities/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Meeting Summaries/i)).toBeInTheDocument();
    expect(screen.getByText(/Action Item Extraction/i)).toBeInTheDocument();
    expect(screen.getByText(/Multiple AI Providers \/ BYOK/i)).toBeInTheDocument();
    expect(screen.getByText(/Architecture & Portfolio/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'FastAPI' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'PostgreSQL' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'LangGraph' })).toBeInTheDocument();
  });

  it('redirects to /dashboard when user is authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        email: 'user@example.com',
        full_name: 'Test User',
        role: 'USER',
        platform_role: 'user',
        is_active: true,
      },
      profile: null,
      isAuthenticated: true,
      isLoading: false,
      isAdmin: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<div>Dashboard Mock</div>} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByText('Dashboard Mock')).toBeInTheDocument();
  });

  it('allows switching tabs in the product preview', async () => {
    const user = userEvent.setup();
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
      isAdmin: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );

    // Click on Action Items tab
    const tasksTab = screen.getByRole('tab', { name: /Action Items/i });
    await user.click(tasksTab);
    expect(screen.getByText(/Implement state schema for LangGraph agent pipeline/i)).toBeInTheDocument();

    // Click on Decisions tab
    const decisionsTab = screen.getByRole('tab', { name: /Decisions/i });
    await user.click(decisionsTab);
    expect(screen.getByText(/Decision: Adopt LangGraph for Multi-Stage Processing/i)).toBeInTheDocument();
  });
});
