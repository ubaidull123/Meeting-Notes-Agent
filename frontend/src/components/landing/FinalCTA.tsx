import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';

export const FinalCTA: React.FC = () => {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24 border-t border-border">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl border border-teal-600/20 bg-gradient-to-b from-teal-500/10 via-background to-card p-8 sm:p-12 md:p-16 text-center shadow-lg">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-600 text-white shadow-sm mb-6">
            <Sparkles className="h-6 w-6" />
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground max-w-2xl mx-auto">
            Ready to turn meetings into structured work?
          </h2>

          <p className="mt-4 text-base sm:text-lg text-muted-foreground max-w-xl mx-auto">
            Start processing meetings with AI summaries, automated task tracking, and human-reviewed follow-up communications.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-6 py-3.5 text-base font-semibold text-white shadow-sm hover:bg-teal-700 active:bg-teal-800 transition-all focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
            >
              Get Started
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-6 py-3.5 text-base font-semibold text-foreground shadow-xs hover:bg-muted transition-all focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-teal-500"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
};
