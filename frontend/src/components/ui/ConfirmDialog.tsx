import React, { useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isDestructive = false,
  isLoading = false,
}) => {
  // Close on ESC
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={() => !isLoading && onClose()}
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-md rounded-xl border bg-card p-6 shadow-xl z-10 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                'p-2.5 rounded-full',
                isDestructive
                  ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400'
                  : 'bg-teal-100 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400'
              )}
            >
              <AlertCircle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-muted-foreground hover:text-foreground p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="mt-3 text-sm text-muted-foreground leading-relaxed">{description}</p>

        <div className="mt-6 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-3.5 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={cn(
              'px-4 py-2 text-sm font-medium text-white rounded-lg shadow-sm transition-all focus:outline-none focus:ring-2 disabled:opacity-50',
              isDestructive
                ? 'bg-rose-600 hover:bg-rose-700 focus:ring-rose-500/20'
                : 'bg-teal-600 hover:bg-teal-700 focus:ring-teal-500/20'
            )}
          >
            {isLoading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
