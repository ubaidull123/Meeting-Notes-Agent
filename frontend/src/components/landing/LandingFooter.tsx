import React from 'react';
import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';
import { BrandMark } from '../ui/BrandMark';

const GITHUB_REPO_URL = 'https://github.com/ubaidull123/Meeting-Notes-Agent';

export const LandingFooter: React.FC = () => {
  return (
    <footer className="border-t border-border bg-card/60 transition-colors">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          {/* Brand */}
          <div className="space-y-2">
            <Link
              to="/"
              className="inline-flex items-center gap-2 font-semibold text-foreground hover:opacity-90 transition-opacity"
            >
              <BrandMark size="sm" />
              <span className="text-base font-bold text-foreground">Meeting Notes Agent</span>
            </Link>
            <p className="text-xs text-muted-foreground">
              Built with FastAPI + React + PostgreSQL
            </p>
          </div>

          {/* Links */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
            <a
              href="#features"
              className="hover:text-foreground transition-colors"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="hover:text-foreground transition-colors"
            >
              How It Works
            </a>
            <a
              href={GITHUB_REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 hover:text-foreground transition-colors"
              aria-label="GitHub repository (opens in new tab)"
            >
              <Github className="h-4 w-4" />
              <span>GitHub</span>
            </a>
            <Link
              to="/login"
              className="hover:text-foreground transition-colors"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="hover:text-foreground transition-colors"
            >
              Register
            </Link>
          </div>
        </div>

        <div className="mt-8 border-t border-border/80 pt-6 text-center text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} Meeting Notes Agent. All rights reserved.
        </div>
      </div>
    </footer>
  );
};
