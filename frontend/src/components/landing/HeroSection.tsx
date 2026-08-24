import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Github, Sparkles, CheckCircle2, Shield } from 'lucide-react';

const GITHUB_REPO_URL = 'https://github.com/ubaidull123/Meeting-Notes-Agent';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
      {/* Background decorative gradients */}
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -z-10 -translate-x-1/2 transform-gpu blur-3xl sm:-top-80"
        aria-hidden="true"
      >
        <div
          className="aspect-1155/678 w-[68rem] bg-gradient-to-tr from-teal-500/20 to-emerald-500/20 opacity-40 dark:opacity-20"
          style={{
            clipPath:
              'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
          }}
        />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
        {/* Pill Badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-teal-600/20 bg-teal-50 dark:bg-teal-950/40 px-3.5 py-1 text-xs font-semibold text-teal-800 dark:text-teal-300 shadow-xs mb-8">
          <Sparkles className="h-3.5 w-3.5 text-teal-600 dark:text-teal-400" />
          <span>AI-Powered Meeting Intelligence & Execution</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl max-w-4xl mx-auto leading-[1.15]">
          Turn meetings into{' '}
          <span className="bg-gradient-to-r from-teal-600 via-teal-500 to-emerald-600 bg-clip-text text-transparent">
            actionable work.
          </span>
        </h1>

        {/* Supporting text */}
        <p className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
          Meeting Notes Agent uses AI to transform meeting transcripts and recordings into structured
          summaries, decisions, action items, insights, and reviewable follow-up emails — organized
          around your teams and projects.
        </p>

        {/* CTA buttons */}
        <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-6 py-3.5 text-base font-semibold text-white shadow-sm hover:bg-teal-700 active:bg-teal-800 transition-all duration-150 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
          >
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3.5 text-base font-semibold text-foreground shadow-xs hover:bg-muted transition-all duration-150 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500"
          >
            Login
          </Link>
          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl px-5 py-3.5 text-base font-medium text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500"
          >
            <Github className="h-4 w-4" />
            <span>View on GitHub</span>
          </a>
        </div>

        {/* Trust/Feature Pills */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs sm:text-sm text-muted-foreground">
          <div className="inline-flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-teal-600" />
            <span>Bring Your Own Key (BYOK) or App Credits</span>
          </div>
          <div className="inline-flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-teal-600" />
            <span>Human-in-the-loop email review</span>
          </div>
          <div className="inline-flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-teal-600" />
            <span>Project-scoped data isolation</span>
          </div>
        </div>
      </div>
    </section>
  );
};
