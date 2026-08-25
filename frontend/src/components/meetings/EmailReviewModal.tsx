import React, { useEffect, useState } from 'react';
import { EmailDraftResponse, EmailReviewRequest } from '../../types/meeting';
import { Mail, RefreshCw, X, AlertTriangle, Send } from 'lucide-react';
import { cn } from '../../utils/cn';

interface EmailReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  emailDraft?: EmailDraftResponse | null;
  onSubmitReview: (data: EmailReviewRequest) => Promise<void>;
  isLoading?: boolean;
}

export const EmailReviewModal: React.FC<EmailReviewModalProps> = ({
  isOpen,
  onClose,
  emailDraft,
  onSubmitReview,
  isLoading = false,
}) => {
  const [decision, setDecision] = useState<'approve' | 'revise' | 'reject'>('approve');
  const [instructions, setInstructions] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [recipientUserIds, setRecipientUserIds] = useState<number[]>([]);
  const availableParticipants = emailDraft?.participants ?? [];

  useEffect(() => {
    if (!isOpen || !emailDraft) return;
    setRecipientUserIds((emailDraft.participants ?? []).filter(participant => participant.selected).map(participant => participant.user_id));
  }, [emailDraft, isOpen]);

  if (!isOpen || !emailDraft) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (decision === 'revise' && (!instructions || instructions.trim().length === 0)) {
      setValidationError('Please provide specific revision instructions for the email draft.');
      return;
    }
    if (decision === 'approve' && availableParticipants.length > 0 && recipientUserIds.length === 0) {
      setValidationError('Select at least one meeting participant to receive the follow-up.');
      return;
    }

    const review: EmailReviewRequest = {
      decision,
      instructions: decision === 'revise' ? instructions.trim() : null,
    };
    if (availableParticipants.length) review.recipient_user_ids = recipientUserIds;
    await onSubmitReview(review);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5" role="dialog" aria-modal="true" aria-labelledby="email-review-title">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-slate-950/50 backdrop-blur-[2px]" onClick={() => !isLoading && onClose()} />

      {/* Modal */}
      <div className="relative z-10 flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-4 sm:px-5">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h2 id="email-review-title" className="text-base font-semibold text-foreground">Email draft review</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Confirm the final message before it is sent to attendees.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close email review"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4 text-sm sm:p-5">
          {emailDraft.delivery_error && (
            <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-semibold">Email was not sent</p>
                <p className="mt-1">{emailDraft.delivery_error}</p>
              </div>
            </div>
          )}

          {/* Email Draft Preview */}
          <div className="space-y-2 rounded-lg border border-border bg-muted/25 p-4 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-border text-muted-foreground">
              <span>Subject: Meeting Summary & Action Items</span>
              <span className="text-[10px]">Formatted Email</span>
            </div>
            <div className="p-3 bg-background rounded-lg border text-foreground whitespace-pre-wrap leading-relaxed">
              {emailDraft.email_draft || 'No email draft generated.'}
            </div>
          </div>

          {availableParticipants.length > 0 && <section className="rounded-lg border border-border p-4"><div><h3 className="text-sm font-semibold">Send meeting follow-up to</h3><p className="mt-1 text-xs text-muted-foreground">Recipients are selected from this meeting's participants and saved for this meeting only.</p></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{availableParticipants.map(participant => { const selected = recipientUserIds.includes(participant.user_id); return <label key={participant.user_id} className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${selected ? 'border-primary/30 bg-primary/5' : 'border-border hover:bg-muted/30'}`}><input type="checkbox" checked={selected} disabled={participant.delivery_status === 'sent'} onChange={() => setRecipientUserIds(current => selected ? current.filter(id => id !== participant.user_id) : [...current, participant.user_id])} /><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">{participant.name.split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase()}</span><span className="min-w-0"><span className="block truncate text-sm font-medium">{participant.name}</span><span className="block truncate text-xs text-muted-foreground">{participant.title || participant.email}</span>{participant.delivery_status && <span className="mt-1 block text-[10px] font-semibold uppercase text-muted-foreground">{participant.delivery_status}</span>}</span></label>; })}</div></section>}

          {/* Decision Form */}
          <form onSubmit={handleSubmit} className="space-y-4 border-t border-border pt-4">
            <label className="block text-sm font-semibold text-foreground">Email action</label>
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
                <Send className="h-4 w-4 text-emerald-600" />
                <span className="text-xs">Approve & Send</span>
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
                <span className="text-xs">Skip Email</span>
              </button>
            </div>

            {decision === 'revise' && (
              <div className="space-y-1.5 animate-in fade-in">
                <label className="text-xs font-medium text-foreground">Email Revision Instructions</label>
                <textarea
                  rows={3}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Tone down the wording and add a reminder about next week's sync..."
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
                    : 'bg-slate-700 hover:bg-slate-800'
                )}
              >
                {isLoading ? 'Processing...' : decision === 'approve' ? 'Send Email' : 'Submit'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
