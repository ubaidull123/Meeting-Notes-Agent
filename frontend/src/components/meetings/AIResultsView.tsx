import React, { useState } from 'react';
import { MeetingResultResponse } from '../../types/meeting';
import { TaskCard } from '../tasks/TaskCard';
import { StatusBadge } from '../ui/StatusBadge';
import {
  Sparkles,
  CheckCircle2,
  ListTodo,
  Mail,
  Eye,
  EyeOff,
  Cpu,
  Copy,
  Check,
} from 'lucide-react';
import { formatNumber } from '../../utils/formatters';

interface AIResultsViewProps {
  results: MeetingResultResponse;
  onTaskStatusChange?: (taskId: string, status: string) => void;
}

export const AIResultsView: React.FC<AIResultsViewProps> = ({ results, onTaskStatusChange }) => {
  const [showRedacted, setShowRedacted] = useState(true);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  const handleCopy = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const currentSummary = showRedacted
    ? results.redacted_summary || results.summary
    : results.summary;

  const currentDecisions = showRedacted
    ? results.redacted_decisions?.length
      ? results.redacted_decisions
      : results.decisions
    : results.decisions;

  const currentActionItems = showRedacted
    ? results.redacted_action_items?.length
      ? results.redacted_action_items
      : results.action_items
    : results.action_items;

  return (
    <div className="space-y-6">
      {/* Top Header & Privacy Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border bg-card">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">AI Generated Artifacts</h3>
            <p className="text-xs text-muted-foreground">
              Processed and verified through the Meeting Notes AI Pipeline
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {results.tokens_used > 0 && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground font-mono bg-muted px-2.5 py-1 rounded-md">
              <Cpu className="w-3.5 h-3.5" />
              <span>{formatNumber(results.tokens_used)} tokens</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowRedacted(!showRedacted)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          >
            {showRedacted ? (
              <>
                <EyeOff className="w-3.5 h-3.5 text-teal-600" />
                <span>Viewing Redacted (Safe)</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5 text-amber-600" />
                <span>Viewing Raw Output</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Summary Card */}
      <div className="p-5 rounded-xl border bg-card space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600" />
            <h4 className="text-sm font-semibold text-foreground">Executive Summary</h4>
          </div>
          {currentSummary && (
            <button
              type="button"
              onClick={() => handleCopy(currentSummary, 'summary')}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {copiedSection === 'summary' ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
        <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">
          {currentSummary || 'No summary available.'}
        </p>
      </div>

      {/* Decisions Card */}
      {currentDecisions && currentDecisions.length > 0 && (
        <div className="p-5 rounded-xl border bg-card space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <h4 className="text-sm font-semibold text-foreground">
                Key Decisions ({currentDecisions.length})
              </h4>
            </div>
            <button
              type="button"
              onClick={() => handleCopy(currentDecisions.join('\n• '), 'decisions')}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {copiedSection === 'decisions' ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <ul className="space-y-2">
            {currentDecisions.map((decision, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-foreground/90">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0" />
                <span className="leading-relaxed">{decision}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Items & Generated Tasks */}
      <div className="p-5 rounded-xl border bg-card space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ListTodo className="w-4 h-4 text-teal-600" />
            <h4 className="text-sm font-semibold text-foreground">
              Extracted Action Items & Tasks
            </h4>
          </div>
        </div>

        {results.tasks && results.tasks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {results.tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onStatusChange={onTaskStatusChange}
              />
            ))}
          </div>
        ) : currentActionItems && currentActionItems.length > 0 ? (
          <ul className="space-y-2">
            {currentActionItems.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-foreground/90">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-2 shrink-0" />
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">No action items were identified.</p>
        )}
      </div>

      {/* Email Draft Card */}
      {results.email_draft && (
        <div className="p-5 rounded-xl border bg-card space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-indigo-600" />
              <h4 className="text-sm font-semibold text-foreground">
                Attendee Email Draft
              </h4>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={results.email_sent ? 'completed' : 'draft'} size="sm" />
              <button
                type="button"
                onClick={() => handleCopy(results.email_draft || '', 'email')}
                className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {copiedSection === 'email' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>
          <div className="p-3.5 rounded-lg border bg-muted/30 font-mono text-xs text-foreground/90 whitespace-pre-wrap leading-relaxed">
            {results.email_draft}
          </div>
        </div>
      )}
    </div>
  );
};
