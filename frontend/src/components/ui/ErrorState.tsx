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
        'flex flex-col items-center justify-center p-8 text-center rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20',
        className
      )}
    >
      <div className="p-3 rounded-full bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h4 className="text-sm font-semibold text-rose-900 dark:text-rose-200">{title}</h4>
      <p className="mt-1 text-xs text-rose-700 dark:text-rose-400 max-w-md">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-rose-700 dark:text-rose-300 bg-white dark:bg-rose-900/40 border border-rose-300 dark:border-rose-700 hover:bg-rose-100/50 rounded-md transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try Again</span>
        </button>
      )}
    </div>
  );
};
