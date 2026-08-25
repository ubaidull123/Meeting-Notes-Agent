import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load content',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex min-h-48 flex-col items-center justify-center rounded-xl border border-rose-200 bg-rose-50/60 p-6 text-center dark:border-rose-900/50 dark:bg-rose-950/20',
        className
      )}
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-rose-100 text-rose-600 dark:bg-rose-900/50 dark:text-rose-400">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <h4 className="text-sm font-semibold text-rose-950 dark:text-rose-200">{title}</h4>
      <p className="mt-1.5 max-w-md text-sm leading-6 text-rose-700 dark:text-rose-400">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-rose-300 bg-white px-3 py-2 text-sm font-semibold text-rose-700 transition-colors hover:bg-rose-100/50 dark:border-rose-700 dark:bg-rose-900/40 dark:text-rose-300"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
};
