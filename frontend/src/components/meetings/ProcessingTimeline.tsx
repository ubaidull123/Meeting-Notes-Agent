import React from 'react';
import { AlertCircle, Check, Circle, Loader2 } from 'lucide-react';
import { MeetingStatus } from '../../types/meeting';
import { cn } from '../../utils/cn';

export type PipelineStepState = 'pending' | 'active' | 'completed' | 'failed';
export type MeetingSourceType = 'audio' | 'supplied_transcript' | 'none';

interface PipelineStep {
  key: 'input' | 'transcription' | 'analysis' | 'review' | 'email' | 'complete';
  title: string;
  state: PipelineStepState;
  detail: string;
}

interface ProcessingTimelineProps {
  status: MeetingStatus;
  currentStage?: string | null;
  progressPercentage?: number | null;
  errorMessage?: string | null;
  errorCode?: string | null;
  sourceType?: MeetingSourceType;
  hasTranscription?: boolean;
}

const terminalStatuses: MeetingStatus[] = ['completed', 'failed', 'cancelled', 'rejected'];

function failedStageIndex(currentStage?: string | null, errorCode?: string | null, sourceType: MeetingSourceType = 'none', hasTranscription = false) {
  const hint = `${currentStage ?? ''} ${errorCode ?? ''}`.toLowerCase();
  if (hint.includes('email')) return 4;
  if (hint.includes('review')) return 3;
  if (hint.includes('transcrib') || (sourceType === 'audio' && !hasTranscription)) return 1;
  if (hint.includes('input') || hint.includes('upload')) return 0;
  return 2;
}

export function buildPipelineSteps({ status, currentStage, errorCode, sourceType = 'none', hasTranscription = false }: Pick<ProcessingTimelineProps, 'status' | 'currentStage' | 'errorCode' | 'sourceType' | 'hasTranscription'>): PipelineStep[] {
  const titles: PipelineStep['title'][] = ['Input', 'Transcription', 'AI Analysis', 'Human Review', 'Email', 'Complete'];
  const details = [
    sourceType === 'audio' ? 'Audio uploaded' : sourceType === 'supplied_transcript' ? 'Transcript supplied' : 'Add a meeting source',
    sourceType === 'supplied_transcript' ? 'Transcript supplied' : hasTranscription ? 'Audio transcribed' : 'Waiting to transcribe',
    'Summary, decisions and actions', 'Approval checkpoint', 'Draft and delivery approval', 'Workflow finished',
  ];
  const keys: PipelineStep['key'][] = ['input', 'transcription', 'analysis', 'review', 'email', 'complete'];
  const steps = titles.map((title, index) => ({ key: keys[index], title, detail: details[index], state: 'pending' as PipelineStepState }));
  const completeThrough = (index: number) => { for (let i = 0; i <= index; i += 1) steps[i].state = 'completed'; };
  const activate = (index: number) => { if (index > 0) completeThrough(index - 1); steps[index].state = 'active'; };

  if (status === 'completed') { completeThrough(5); steps[5].detail = 'Completed'; return steps; }
  if (status === 'failed') { const failedIndex = failedStageIndex(currentStage, errorCode, sourceType, hasTranscription); if (failedIndex > 0) completeThrough(failedIndex - 1); steps[failedIndex].state = 'failed'; steps[failedIndex].detail = 'Processing failed'; return steps; }
  if (status === 'rejected') { completeThrough(2); const rejectedIndex = (currentStage ?? '').toLowerCase().includes('email') ? 4 : 3; if (rejectedIndex === 4) completeThrough(3); steps[rejectedIndex].state = 'failed'; steps[rejectedIndex].detail = 'Review rejected'; return steps; }
  if (status === 'cancelled') return steps;
  if (status === 'awaiting_email_review') { activate(4); steps[4].detail = 'Approval required'; return steps; }
  if (status === 'awaiting_review' || status === 'revision_requested') { activate(3); steps[3].detail = status === 'revision_requested' ? 'Revision requested' : 'Approval required'; return steps; }
  if (status === 'queued' || status === 'processing') {
    const stageHint = (currentStage ?? '').toLowerCase();
    const transcriptionIsActive = sourceType === 'audio' && !hasTranscription && !stageHint.includes('analysis');
    activate(transcriptionIsActive ? 1 : 2);
    if (status === 'queued') steps[transcriptionIsActive ? 1 : 2].detail = 'Queued to begin';
    else if (transcriptionIsActive) steps[1].detail = 'Transcribing audio';
    else steps[2].detail = 'Generating meeting artifacts';
    return steps;
  }
  if (sourceType !== 'none') { completeThrough(0); if (sourceType === 'supplied_transcript') completeThrough(1); }
  else if (status === 'draft') activate(0);
  return steps;
}

export const ProcessingTimeline: React.FC<ProcessingTimelineProps> = props => {
  const { status, progressPercentage, errorMessage, sourceType = 'none' } = props;
  const steps = buildPipelineSteps(props);
  const activeStep = steps.find(step => step.state === 'active');
  const isTerminal = terminalStatuses.includes(status);
  const description = status === 'completed' ? 'The workflow completed successfully.' : status === 'failed' ? 'The workflow stopped because an error occurred.' : status === 'cancelled' ? 'Processing was stopped.' : status === 'rejected' ? 'The workflow ended at a review checkpoint.' : 'Follow the meeting from input through delivery.';

  return <section className="rounded-xl border border-border/80 bg-card p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5" aria-labelledby="processing-heading">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 id="processing-heading" className="font-semibold text-foreground">Processing workflow</h3><p className="mt-1 text-sm text-muted-foreground">{description}</p></div>{progressPercentage != null && !isTerminal && <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-semibold tabular-nums text-primary">{progressPercentage}%</span>}</div>
    {progressPercentage != null && !isTerminal && <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted"><span className="block h-full rounded-full bg-primary transition-all" style={{ width: `${Math.max(0, Math.min(100, progressPercentage))}%` }} /></div>}
    <ol className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-6 md:gap-2" aria-label="Meeting processing stages">{steps.map((step, index) => <li key={step.key} className="relative flex min-w-0 items-start gap-3 pb-1 md:block md:text-center">
      {index < steps.length - 1 && <span className={cn('absolute left-4 top-8 h-[calc(100%+0.75rem)] w-px bg-border md:left-[calc(50%+1rem)] md:top-4 md:h-px md:w-[calc(100%-2rem)]', step.state === 'completed' && 'bg-emerald-400 dark:bg-emerald-700')} aria-hidden="true" />}
      <span className={cn('relative z-10 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-card md:mx-auto', step.state === 'completed' && 'border-emerald-500 bg-emerald-500 text-white', step.state === 'active' && 'border-primary text-primary ring-4 ring-primary/10', step.state === 'failed' && 'border-rose-500 bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300', step.state === 'pending' && 'text-muted-foreground')}>{step.state === 'completed' ? <Check className="h-4 w-4" /> : step.state === 'active' ? <Loader2 className="h-4 w-4 animate-spin" /> : step.state === 'failed' ? <AlertCircle className="h-4 w-4" /> : <Circle className="h-3.5 w-3.5" />}</span>
      <div className="min-w-0 md:mt-2"><p className={cn('text-sm font-medium', step.state === 'pending' && 'text-muted-foreground')}>{step.title}</p><p className="mt-0.5 text-xs text-muted-foreground">{step.detail}</p></div>
    </li>)}</ol>
    {activeStep && <div className="mt-6 rounded-lg border border-primary/20 bg-primary/5 p-4"><p className="text-sm font-semibold text-foreground">{activeStep.title}</p>{activeStep.key === 'analysis' ? <div className="mt-2 text-sm text-muted-foreground"><p>{status === 'queued' ? 'Waiting for processing capacity.' : 'Generating:'}</p>{status !== 'queued' && <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">{['Summary and decisions', 'Action items', 'Sensitive-information redaction', 'Follow-up content'].map(item => <li key={item} className="flex gap-2"><span className="text-primary">•</span>{item}</li>)}</ul>}</div> : <p className="mt-1 text-sm text-muted-foreground">{activeStep.key === 'transcription' && sourceType === 'audio' ? 'Converting the uploaded audio into a transcript.' : activeStep.detail}</p>}</div>}
    {status === 'failed' && <div className="mt-5 flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /><div><p className="font-semibold">Processing failed</p><p className="mt-1 break-words leading-6">{errorMessage || 'The backend did not provide an error message.'}</p></div></div>}
  </section>;
};
