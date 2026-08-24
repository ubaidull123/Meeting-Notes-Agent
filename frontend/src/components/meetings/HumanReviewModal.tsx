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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-xs" onClick={() => !isLoading && onClose()} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl border bg-card shadow-2xl z-10 animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Human-in-the-Loop Review</h2>
              <p className="text-xs text-muted-foreground">
                Review generated summary & action items before finalization
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="text-muted-foreground hover:text-foreground p-1 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-sm">
          {/* Summary Preview */}
          <div className="p-4 rounded-xl border bg-muted/30 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Generated Summary
            </h4>
            <p className="text-foreground text-xs leading-relaxed whitespace-pre-wrap">
              {reviewContent.redacted_summary || 'No summary generated yet.'}
            </p>
          </div>

          {/* Key Decisions */}
          {reviewContent.redacted_decisions && reviewContent.redacted_decisions.length > 0 && (
            <div className="p-4 rounded-xl border bg-muted/30 space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Decisions ({reviewContent.redacted_decisions.length})
              </h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-foreground">
                {reviewContent.redacted_decisions.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {reviewContent.redacted_action_items && reviewContent.redacted_action_items.length > 0 && (
            <div className="p-4 rounded-xl border bg-muted/30 space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Extracted Action Items ({reviewContent.redacted_action_items.length})
              </h4>
              <ul className="list-disc list-inside space-y-1 text-xs text-foreground">
                {reviewContent.redacted_action_items.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Decision Form */}
          <form onSubmit={handleSubmit} className="pt-3 border-t border-border space-y-3">
            <label className="text-xs font-semibold text-foreground block">Select Review Decision</label>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setDecision('approve')}
                className={cn(
                  'flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all',
                  decision === 'approve'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-200 font-semibold ring-2 ring-emerald-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <Check className="w-4 h-4 mb-1 text-emerald-600" />
                <span className="text-xs">Approve</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('revise')}
                className={cn(
                  'flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all',
                  decision === 'revise'
                    ? 'border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-200 font-semibold ring-2 ring-amber-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <RefreshCw className="w-4 h-4 mb-1 text-amber-600" />
                <span className="text-xs">Request Revision</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('reject')}
                className={cn(
                  'flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all',
                  decision === 'reject'
                    ? 'border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-200 font-semibold ring-2 ring-rose-500/20'
                    : 'border-border hover:bg-muted text-muted-foreground'
                )}
              >
                <X className="w-4 h-4 mb-1 text-rose-600" />
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
                  className="w-full p-2.5 text-xs bg-background border border-input rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500 placeholder:text-muted-foreground"
                />
              </div>
            )}

            {validationError && (
              <div className="flex items-center gap-1.5 text-xs text-rose-600">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span>{validationError}</span>
              </div>
            )}

            <div className="pt-3 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="px-3.5 py-2 text-xs font-medium text-muted-foreground hover:bg-muted rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className={cn(
                  'px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-sm transition-all',
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
