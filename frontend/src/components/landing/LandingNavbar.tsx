import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Github, ArrowRight, Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { BrandMark } from '../ui/BrandMark';

const GITHUB_REPO_URL = 'https://github.com/ubaidull123/Meeting-Notes-Agent';

export const LandingNavbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { setTheme, isDark } = useTheme();

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/80 bg-background/80 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 font-semibold text-foreground hover:opacity-90 transition-opacity focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded-lg p-1"
          aria-label="Meeting Notes Agent Home"
        >
          <BrandMark size="lg" />
          <span className="text-lg font-bold tracking-tight text-foreground">
            Meeting Notes Agent
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-muted-foreground" aria-label="Main Navigation">
          <a
            href="#features"
            onClick={(e) => handleScroll(e, 'features')}
            className="hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded px-1.5 py-1"
          >
            Features
          </a>
          <a
            href="#how-it-works"
            onClick={(e) => handleScroll(e, 'how-it-works')}
            className="hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded px-1.5 py-1"
          >
            How It Works
          </a>
          <a
            href="#tech-stack"
            onClick={(e) => handleScroll(e, 'tech-stack')}
            className="hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded px-1.5 py-1"
          >
            Tech Stack
          </a>
          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded px-1.5 py-1"
            aria-label="GitHub repository (opens in new tab)"
          >
            <Github className="h-4 w-4" />
            <span>GitHub</span>
          </a>
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-3">
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500"
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <Link
            to="/login"
            className="px-3.5 py-2 text-sm font-semibold text-foreground hover:text-teal-600 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 rounded-lg"
          >
            Login
          </Link>
          <Link
            to="/register"
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-teal-700 active:bg-teal-800 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-foreground hover:bg-muted transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-border bg-card px-4 pt-2 pb-6 shadow-lg animate-in slide-in-from-top-2">
          <div className="flex flex-col space-y-3 pt-2">
            <a
              href="#features"
              onClick={(e) => handleScroll(e, 'features')}
              className="rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              onClick={(e) => handleScroll(e, 'how-it-works')}
              className="rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              How It Works
            </a>
            <a
              href="#tech-stack"
              onClick={(e) => handleScroll(e, 'tech-stack')}
              className="rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              Tech Stack
            </a>
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-md px-3 py-2 text-base font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <Github className="h-4 w-4" />
              <span>GitHub</span>
            </a>
            <div className="pt-4 border-t border-border flex flex-col gap-2.5">
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center rounded-lg border border-border bg-background py-2.5 text-sm font-semibold text-foreground hover:bg-muted"
              >
                Login
              </Link>
              <Link
                to="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center inline-flex items-center justify-center gap-1.5 rounded-lg bg-teal-600 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-teal-700"
              >
                Get Started
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
