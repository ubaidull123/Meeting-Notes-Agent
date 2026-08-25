import React, { useState } from 'react';
import { ReviewContentResponse, ReviewRequest } from '../../types/meeting';
import { UserCheck, Check, RefreshCw, X, AlertTriangle } from 'lucide-react';
import { cn } from '../../utils/cn';

interface HumanReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviewContent?: ReviewContentResponse | null;
  onSubmitReview: (data: ReviewRequest) => Promise<void>;
  isLoading?: boolean;
}

export const HumanReviewModal: React.FC<HumanReviewModalProps> = ({
  isOpen,
  onClose,
  reviewContent,
  onSubmitReview,
  isLoading = false,
}) => {
  const [decision, setDecision] = useState<'approve' | 'revise' | 'reject'>('approve');
  const [instructions, setInstructions] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen || !reviewContent) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (decision === 'revise' && (!instructions || instructions.trim().length === 0)) {
      setValidationError('Please provide specific revision instructions for the AI workflow.');
      return;
    }

    await onSubmitReview({
      decision,
      instructions: decision === 'revise' ? instructions.trim() : null,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5" role="dialog" aria-modal="true" aria-labelledby="human-review-title">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-slate-950/50 backdrop-blur-[2px]" onClick={() => !isLoading && onClose()} />

      {/* Modal */}
      <div className="relative z-10 flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-4 sm:px-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 id="human-review-title" className="text-base font-semibold text-foreground">Review meeting output</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Approve, request a targeted revision, or reject this output.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close review"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4 text-sm sm:p-5">
          {/* Summary Preview */}
          <div className="space-y-2 rounded-lg border border-border bg-muted/25 p-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Generated Summary
            </h4>
            <p className="whitespace-pre-wrap text-sm leading-6 text-foreground/90">
              {reviewContent.redacted_summary || 'No summary generated yet.'}
            </p>
          </div>

          {/* Key Decisions */}
          {reviewContent.redacted_decisions && reviewContent.redacted_decisions.length > 0 && (
            <div className="space-y-2 rounded-lg border border-border bg-muted/25 p-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Decisions ({reviewContent.redacted_decisions.length})
              </h4>
              <ul className="list-inside list-disc space-y-1.5 text-sm leading-6 text-foreground/90">
                {reviewContent.redacted_decisions.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {reviewContent.redacted_action_items && reviewContent.redacted_action_items.length > 0 && (
            <div className="space-y-2 rounded-lg border border-border bg-muted/25 p-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Extracted Action Items ({reviewContent.redacted_action_items.length})
              </h4>
              <ul className="list-inside list-disc space-y-1.5 text-sm leading-6 text-foreground/90">
                {reviewContent.redacted_action_items.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Decision Form */}
          <form onSubmit={handleSubmit} className="space-y-4 border-t border-border pt-4">
            <label className="block text-sm font-semibold text-foreground">Review decision</label>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
              <button
                type="button"
                onClick={() => setDecision('approve')}
                className={cn(
                  'flex min-h-20 flex-row items-center justify-start gap-2 rounded-lg border p-3 text-left transition-all sm:flex-col sm:justify-center sm:text-center',
                  decision === 'approve'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-200 font-semibold ring-2 ring-emerald-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <Check className="h-4 w-4 text-emerald-600" />
                <span className="text-xs">Approve</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('revise')}
                className={cn(
                  'flex min-h-20 flex-row items-center justify-start gap-2 rounded-lg border p-3 text-left transition-all sm:flex-col sm:justify-center sm:text-center',
                  decision === 'revise'
                    ? 'border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-200 font-semibold ring-2 ring-amber-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <RefreshCw className="h-4 w-4 text-amber-600" />
                <span className="text-xs">Request Revision</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('reject')}
                className={cn(
                  'flex min-h-20 flex-row items-center justify-start gap-2 rounded-lg border p-3 text-left transition-all sm:flex-col sm:justify-center sm:text-center',
                  decision === 'reject'
                    ? 'border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-200 font-semibold ring-2 ring-rose-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <X className="h-4 w-4 text-rose-600" />
                <span className="text-xs">Reject</span>
              </button>
            </div>

            {decision === 'revise' && (
              <div className="space-y-1.5 animate-in fade-in">
                <label className="text-xs font-medium text-foreground">Revision Instructions for AI</label>
                <textarea
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Make summary more concise and re-word action item 2..."
                  className="w-full rounded-lg border border-input bg-background p-3 text-sm outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 placeholder:text-muted-foreground"
                />
              </div>
            )}

            {validationError && (
              <div className="flex items-center gap-1.5 text-xs text-rose-600">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span>{validationError}</span>
              </div>
            )}

            <div className="flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-end">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="rounded-lg px-3.5 py-2 text-sm font-semibold text-muted-foreground hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className={cn(
                  'rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all',
                  decision === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : decision === 'revise'
                    ? 'bg-amber-600 hover:bg-amber-700'
                    : 'bg-rose-600 hover:bg-rose-700'
                )}
              >
                {isLoading ? 'Submitting...' : `Submit ${decision.charAt(0).toUpperCase() + decision.slice(1)}`}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
