import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../utils/cn';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className, label }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={cn('flex min-h-40 flex-col items-center justify-center gap-3 rounded-xl border border-border/70 bg-card/60', className)} role="status" aria-live="polite">
      <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
        <Loader2 className={cn('animate-spin text-primary', sizeClasses[size])} />
      </span>
      {label && <span className="text-sm font-medium text-muted-foreground">{label}</span>}
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({ rows = 5, cols = 5 }) => {
  return (
    <div className="w-full space-y-3 animate-pulse">
      <div className="h-10 bg-muted/60 rounded-lg w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 items-center p-3 border-b border-border/50">
          {Array.from({ length: cols }).map((_, j) => (
            <div
              key={j}
              className="h-4 bg-muted rounded"
              style={{ width: `${Math.max(30, 100 / cols - 5)}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

export const CardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="p-5 border rounded-xl bg-card space-y-3">
          <div className="flex justify-between items-center">
            <div className="h-3 bg-muted rounded w-24" />
            <div className="h-8 w-8 bg-muted rounded-lg" />
          </div>
          <div className="h-7 bg-muted rounded w-16" />
          <div className="h-3 bg-muted/60 rounded w-32" />
        </div>
      ))}
    </div>
  );
};

export const LoadingState = LoadingSpinner;
