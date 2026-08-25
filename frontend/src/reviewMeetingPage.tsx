import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CalendarDays, Check, Clock3, Download, Edit3, FileText, Mail, MoreHorizontal, Play, Square, Trash2, UserCheck, Users } from 'lucide-react';
import { toast } from 'sonner';
import { meetingsApi } from './api/meetings';
import { tasksApi } from './api/tasks';
import { formatErrorMessage } from './utils/errors';
import { formatDate } from './utils/date';
import { StatusBadge } from './components/ui/StatusBadge';
import { LoadingState } from './components/ui/LoadingState';
import { ErrorState } from './components/ui/ErrorState';
import { EmptyState } from './components/ui/EmptyState';
import { ProcessingTimeline, MeetingSourceType } from './components/meetings/ProcessingTimeline';
import { HumanReviewModal } from './components/meetings/HumanReviewModal';
import { EmailReviewModal } from './components/meetings/EmailReviewModal';
import { MeetingEditDialog } from './components/meetings/MeetingEditDialog';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { EmailReviewRequest, Meeting, MeetingStatus, MeetingUpdateRequest, ReviewRequest } from './types/meeting';
import { MeetingOverridePanel } from './components/settings/MeetingOverridePanel';
import { TaskTable } from './components/tasks/TaskTable';
import { TaskStatus } from './types/task';
import { useTeam } from './context/TeamContext';
import { useAuth } from './context/AuthContext';
import { primaryButton, secondaryButton, SectionCard, WorkspaceTabs } from './components/ui/Workspace';

const card = 'rounded-xl border border-border/80 bg-card p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] sm:p-5';
type MeetingTab = 'overview' | 'transcript' | 'summary' | 'tasks' | 'email' | 'activity';

export function shouldPollMeetingStatus(status?: MeetingStatus | null) {
  return status === 'queued' || status === 'processing';
}

function getSourceType(meeting: Meeting): MeetingSourceType {
  if (meeting.audio_file_path) return 'audio';
  if (meeting.transcript_file_path || meeting.transcript_text) return 'supplied_transcript';
  return 'none';
}

function getSourceLabel(meeting: Meeting) {
  if (meeting.audio_file_path) return 'Audio upload';
  if (meeting.transcript_file_path) return 'Transcript upload';
  if (meeting.transcript_text) return 'Pasted transcript';
  return 'No source';
}

function AttendeeList({ meeting }: { meeting: Meeting }) {
  return <div className="space-y-3">
    {meeting.attendees.map(attendee => <div key={attendee.id ?? attendee.email} className="flex min-w-0 items-center gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-100 text-sm font-semibold text-teal-800 dark:bg-teal-950/70 dark:text-teal-200">{attendee.name.charAt(0).toUpperCase()}</span>
      <div className="min-w-0"><p className="truncate text-sm font-medium">{attendee.name}</p><p className="truncate text-xs text-muted-foreground">{attendee.email}</p></div>
    </div>)}
  </div>;
}

function TasksList({ meetingId, teamId, canManage }: { meetingId: string; teamId: string; canManage: boolean }) {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const query = useQuery({ queryKey: ['tasks', teamId, meetingId], queryFn: () => tasksApi.listTasks({ team_id: teamId, meeting_id: meetingId, page_size: 100 }) });
  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.updateTask(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
    onError: error => toast.error(formatErrorMessage(error)),
  });
  if (query.isLoading) return <LoadingState label="Loading tasks..." />;
  if (query.isError) return <ErrorState message={formatErrorMessage(query.error, 'Tasks could not be loaded.')} onRetry={() => query.refetch()} />;
  return query.data?.tasks.length ? <TaskTable tasks={query.data.tasks} onSelectTask={() => undefined} onDeleteTask={() => undefined} onStatusChange={(id, status) => update.mutate({ id, status })} canManageActions={false} canChangeStatus={task => canManage || task.assigned_user_id === user?.id} /> : <EmptyState title="No meeting tasks" description="Action items extracted from this meeting will appear here." />;
}

function SummaryPanel({ meeting, canManage }: { meeting: Meeting; canManage: boolean }) {
  const [showRedacted, setShowRedacted] = useState(true);
  const summary = showRedacted ? meeting.redacted_summary || meeting.summary : meeting.summary;
  const decisions = showRedacted && meeting.redacted_decisions.length ? meeting.redacted_decisions : meeting.decisions;
  const actionItems = showRedacted && meeting.redacted_action_items.length ? meeting.redacted_action_items : meeting.action_items;
  return <div className="space-y-4">
    {canManage && <div className="flex justify-end"><button type="button" className={secondaryButton} onClick={() => setShowRedacted(value => !value)}>{showRedacted ? 'Viewing redacted output' : 'Viewing raw output'}</button></div>}
    <SectionCard title="Executive summary" description="A concise overview of the discussion" icon={FileText}><p className="whitespace-pre-wrap text-sm leading-7 text-foreground/90">{summary || 'No summary is available yet.'}</p></SectionCard>
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title={`Decisions${decisions.length ? ` · ${decisions.length}` : ''}`} description="Outcomes agreed during the meeting"><>{decisions.length ? <ul className="space-y-3 text-sm leading-6">{decisions.map((item, index) => <li key={index} className="flex gap-2.5"><Check className="mt-1 h-4 w-4 shrink-0 text-emerald-600" /><span>{item}</span></li>)}</ul> : <p className="text-sm text-muted-foreground">No decisions were identified.</p>}</></SectionCard>
      <SectionCard title={`Action items${actionItems.length ? ` · ${actionItems.length}` : ''}`} description="Follow-up captured from the conversation"><>{actionItems.length ? <ul className="space-y-3 text-sm leading-6">{actionItems.map((item, index) => <li key={index} className="flex gap-2.5"><span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" /><span>{item}</span></li>)}</ul> : <p className="text-sm text-muted-foreground">No action items were identified.</p>}</></SectionCard>
    </div>
  </div>;
}

export function MeetingReviewPage() {
  const { meetingId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { activeTeam, canManageTeam } = useTeam();
  const menuRef = useRef<HTMLDivElement>(null);
  const lastSyncedStatus = useRef<MeetingStatus | undefined>(undefined);
  const [tab, setTab] = useState<MeetingTab>('overview');
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [isEmailReviewOpen, setIsEmailReviewOpen] = useState(false);
  const [isStopOpen, setIsStopOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editFocus, setEditFocus] = useState<'title' | 'notes'>('title');
  const [isActionsOpen, setIsActionsOpen] = useState(false);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const meetingKey = useMemo(() => ['meeting', activeTeam?.id, meetingId] as const, [activeTeam?.id, meetingId]);
  const meeting = useQuery({ queryKey: meetingKey, queryFn: () => meetingsApi.getMeeting(meetingId) });
  const canManage = canManageTeam(meeting.data?.team_id);
  const status = useQuery({
    queryKey: ['status', activeTeam?.id, meetingId],
    queryFn: () => meetingsApi.getStatus(meetingId),
    refetchInterval: query => shouldPollMeetingStatus(query.state.data?.status) ? 3000 : false,
  });
  const review = useQuery({ queryKey: ['review', activeTeam?.id, meetingId], queryFn: () => meetingsApi.getReviewContent(meetingId), enabled: canManage && isReviewOpen });
  const emailDraft = useQuery({ queryKey: ['email-review', activeTeam?.id, meetingId], queryFn: () => meetingsApi.getEmailDraft(meetingId), enabled: canManage && isEmailReviewOpen });

  useEffect(() => {
    const closeMenu = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setIsActionsOpen(false);
    };
    document.addEventListener('mousedown', closeMenu);
    return () => document.removeEventListener('mousedown', closeMenu);
  }, []);

  useEffect(() => {
    const nextStatus = status.data?.status;
    if (!nextStatus || lastSyncedStatus.current === nextStatus) return;
    lastSyncedStatus.current = nextStatus;
    queryClient.invalidateQueries({ queryKey: meetingKey });
    queryClient.invalidateQueries({ queryKey: ['meetings'] });
  }, [meetingKey, queryClient, status.data?.status]);

  const start = useMutation({
    mutationFn: () => meetingsApi.startProcessing(meetingId),
    onSuccess: () => { toast.success('Processing started'); queryClient.invalidateQueries({ queryKey: ['status', activeTeam?.id, meetingId] }); queryClient.invalidateQueries({ queryKey: meetingKey }); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const stop = useMutation({
    mutationFn: () => meetingsApi.cancelProcessing(meetingId),
    onSuccess: response => {
      toast.success('Processing stopped'); setIsStopOpen(false); setIsReviewOpen(false); setIsEmailReviewOpen(false);
      queryClient.setQueryData(['status', activeTeam?.id, meetingId], response); queryClient.invalidateQueries({ queryKey: meetingKey }); queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const updateMeeting = useMutation({
    mutationFn: (data: MeetingUpdateRequest) => meetingsApi.updateMeeting(meetingId, data),
    onSuccess: updated => { queryClient.setQueryData(meetingKey, updated); queryClient.invalidateQueries({ queryKey: ['meetings'] }); setIsEditOpen(false); toast.success('Meeting updated'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const deleteMeeting = useMutation({
    mutationFn: () => meetingsApi.deleteMeeting(meetingId),
    onSuccess: () => { toast.success('Meeting deleted'); queryClient.removeQueries({ queryKey: meetingKey }); queryClient.invalidateQueries({ queryKey: ['meetings'] }); navigate('/meetings'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const submitReview = useMutation({
    mutationFn: (data: ReviewRequest) => meetingsApi.submitReview(meetingId, data),
    onSuccess: response => { toast.success(response.message); setIsReviewOpen(false); queryClient.invalidateQueries({ queryKey: ['status', activeTeam?.id, meetingId] }); queryClient.invalidateQueries({ queryKey: meetingKey }); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const submitEmailReview = useMutation({
    mutationFn: (data: EmailReviewRequest) => meetingsApi.submitEmailReview(meetingId, data),
    onSuccess: response => {
      if (response.sent) { toast.success(response.message); setIsEmailReviewOpen(false); } else { toast.error(response.message); queryClient.invalidateQueries({ queryKey: ['email-review', activeTeam?.id, meetingId] }); }
      queryClient.invalidateQueries({ queryKey: ['status', activeTeam?.id, meetingId] }); queryClient.invalidateQueries({ queryKey: meetingKey });
    },
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (meeting.isLoading) return <LoadingState label="Loading meeting..." />;
  if (!meeting.data) return <ErrorState message={formatErrorMessage(meeting.error, 'Meeting not found.')} onRetry={() => meeting.refetch()} />;

  const data = meeting.data;
  const currentStatus = status.data?.status ?? data.status;
  const transcript = data.cleaned_transcription || data.raw_transcription || data.transcript_text || '';
  const sourceType = getSourceType(data);
  const hasSummary = Boolean(data.summary || data.redacted_summary || data.decisions.length || data.action_items.length);
  const hasEmail = Boolean(data.email_draft || data.email_sent || currentStatus === 'awaiting_email_review');
  const canStart = canManage && ['draft', 'uploaded', 'failed', 'cancelled'].includes(currentStatus);
  const canReview = canManage && (currentStatus === 'awaiting_review' || currentStatus === 'revision_requested');
  const canReviewEmail = canManage && currentStatus === 'awaiting_email_review';
  const canStop = canManage && ['queued', 'processing', 'awaiting_review', 'revision_requested', 'awaiting_email_review'].includes(currentStatus);
  const tabs: Array<{ id: MeetingTab; label: string }> = [
    { id: 'overview', label: 'Overview' },
    ...(canManage && (sourceType !== 'none' || transcript) ? [{ id: 'transcript' as const, label: 'Transcript' }] : []),
    ...(hasSummary ? [{ id: 'summary' as const, label: 'Summary' }] : []),
    { id: 'tasks', label: 'Tasks' },
    ...(canManage && hasEmail ? [{ id: 'email' as const, label: 'Email' }] : []),
    ...(canManage ? [{ id: 'activity' as const, label: 'Activity' }] : []),
  ];

  const openEdit = (focus: 'title' | 'notes' = 'title') => { setEditFocus(focus); setIsEditOpen(true); setIsActionsOpen(false); };
  const downloadTranscript = () => {
    if (!transcript) return;
    const url = URL.createObjectURL(new Blob([transcript], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `${data.title.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase() || 'meeting'}-transcript.txt`; link.click(); URL.revokeObjectURL(url); setIsActionsOpen(false);
  };

  return <div className="space-y-6">
    <header className="flex flex-col gap-4 border-b border-border/80 pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <Link to="/meetings" className="mb-2 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"><ArrowLeft className="h-3.5 w-3.5" />All meetings</Link>
        <div className="flex flex-wrap items-center gap-3"><h1 className="break-words text-2xl font-semibold tracking-tight sm:text-[1.75rem]">{data.title}</h1><StatusBadge status={currentStatus} /></div>
        <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground"><span>{formatDate(data.meeting_date)}</span>{data.meeting_time && <><span aria-hidden="true">·</span><span>{data.meeting_time}</span></>}<span aria-hidden="true">·</span><span>{data.attendees.length} {data.attendees.length === 1 ? 'attendee' : 'attendees'}</span>{data.project_name && <><span aria-hidden="true">·</span><span>{data.project_name}</span></>}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:justify-end">
        {canStart && <button className={primaryButton} onClick={() => start.mutate()} disabled={start.isPending}><Play className="h-4 w-4" />{start.isPending ? 'Starting...' : currentStatus === 'failed' ? 'Reprocess' : 'Start processing'}</button>}
        {canReview && <button className={primaryButton} onClick={() => setIsReviewOpen(true)}><UserCheck className="h-4 w-4" />Review results</button>}
        {canReviewEmail && <button className={primaryButton} onClick={() => setIsEmailReviewOpen(true)}><Mail className="h-4 w-4" />Review email</button>}
        {canStop && <button className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-300 bg-card px-3.5 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/30" onClick={() => setIsStopOpen(true)} disabled={stop.isPending}><Square className="h-3.5 w-3.5" />Stop processing</button>}
        {canManage && <button className={secondaryButton} onClick={() => openEdit()}><Edit3 className="h-4 w-4" />Edit meeting</button>}
        {canManage && <div className="relative" ref={menuRef}>
          <button type="button" onClick={() => setIsActionsOpen(value => !value)} className="rounded-lg border border-border bg-card p-2.5 shadow-sm hover:bg-muted" aria-label="Meeting actions" aria-expanded={isActionsOpen}><MoreHorizontal className="h-4 w-4" /></button>
          {isActionsOpen && <div className="absolute right-0 z-20 mt-2 w-52 rounded-xl border border-border bg-card p-1.5 shadow-xl">
            <button type="button" onClick={() => openEdit()} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-muted"><Edit3 className="h-4 w-4 text-muted-foreground" />Edit meeting</button>
            {transcript && <button type="button" onClick={downloadTranscript} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-muted"><Download className="h-4 w-4 text-muted-foreground" />Download transcript</button>}
            {!canStop && <div className="mt-1 border-t border-border pt-1"><button type="button" onClick={() => { setIsActionsOpen(false); setIsDeleteOpen(true); }} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-300 dark:hover:bg-rose-950/30"><Trash2 className="h-4 w-4" />Delete meeting</button></div>}
          </div>}
        </div>}
      </div>
    </header>

    <WorkspaceTabs items={tabs} active={tab} onChange={setTab} label="Meeting workspace" />

    {tab === 'overview' && <div className="space-y-5">
      <section className={card}>
        <div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">Meeting overview</h2><p className="mt-1 text-sm text-muted-foreground">Essential context at a glance.</p></div></div>
        <dl className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[[CalendarDays, 'Date', formatDate(data.meeting_date)], [Users, 'Attendees', String(data.attendees.length)], [FileText, 'Source', getSourceLabel(data)], [Clock3, 'Duration', '—']].map(([Icon, label, value]) => { const MetaIcon = Icon as typeof CalendarDays; return <div key={label as string} className="flex gap-3"><MetaIcon className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" /><div><dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label as string}</dt><dd className="mt-1 text-sm font-medium">{value as string}</dd></div></div>; })}
        </dl>
      </section>
      <div className="grid gap-5 lg:grid-cols-2">
        <section className={card}><div className="flex items-center justify-between"><div><h2 className="font-semibold">Meeting participants</h2><p className="mt-1 text-sm text-muted-foreground">{data.attendees.length} participant{data.attendees.length === 1 ? '' : 's'}</p></div>{canManage && <button className="text-sm font-semibold text-teal-700 dark:text-teal-300" onClick={() => openEdit()}>Edit participants</button>}</div><div className="mt-4"><AttendeeList meeting={data} /></div></section>
        <section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">Notes</h2>{canManage && <button className="text-sm font-semibold text-teal-700 dark:text-teal-300" onClick={() => openEdit('notes')}>{data.notes ? 'Edit notes' : 'Add notes'}</button>}</div>{data.notes ? <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-foreground/85">{data.notes}</p> : <p className="mt-4 text-sm text-muted-foreground">No notes added.</p>}</section>
      </div>
      {(canReview || canReviewEmail) && <section className="rounded-xl border border-purple-200 bg-purple-50 p-4 text-sm text-purple-950 dark:border-purple-900 dark:bg-purple-950/30 dark:text-purple-100"><strong>{canReviewEmail ? 'Email approval required.' : 'Review required.'}</strong> {canReviewEmail ? 'Review the attendee email before it is sent.' : 'Check the generated summary and action items before the workflow continues.'}</section>}
      {canManage && <ProcessingTimeline status={currentStatus} currentStage={status.data?.current_stage} progressPercentage={status.data?.progress_percentage} errorMessage={status.data?.error ?? data.error_message} errorCode={data.error_code} sourceType={sourceType} hasTranscription={Boolean(data.raw_transcription || data.cleaned_transcription || sourceType === 'supplied_transcript')} />}
      {canManage && <section className={card}><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">AI & transcription configuration</h2><p className="mt-1 text-sm text-muted-foreground">This meeting uses workspace defaults unless a meeting override is saved.</p></div>{canStart && <button className={secondaryButton} onClick={() => setIsConfigOpen(value => !value)}>{isConfigOpen ? 'Hide configuration' : 'Configure meeting'}</button>}</div></section>}
      {canStart && isConfigOpen && <MeetingOverridePanel meetingId={meetingId} />}
      <section className="rounded-xl border border-border bg-card px-5 py-4 text-sm text-muted-foreground"><span className="font-medium text-foreground">Recent activity:</span> Updated {new Date(data.updated_at).toLocaleString()} &middot; {data.tokens_used.toLocaleString()} AI tokens used</section>
    </div>}

    {tab === 'transcript' && <section className={card}><div className="flex items-center justify-between gap-3"><div><h2 className="font-semibold">Transcript</h2><p className="mt-1 text-sm text-muted-foreground">{getSourceLabel(data)}</p></div>{transcript && <button className={secondaryButton} onClick={downloadTranscript}><Download className="h-4 w-4" />Download</button>}</div><p className="mt-5 whitespace-pre-wrap text-sm leading-7 text-foreground/85">{transcript || 'The transcript will appear here when it is available.'}</p></section>}
    {tab === 'summary' && <SummaryPanel meeting={data} canManage={canManage} />}
    {tab === 'tasks' && <TasksList meetingId={meetingId} teamId={data.team_id} canManage={canManage} />}
    {tab === 'email' && <section className={card}><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-semibold">Attendee email</h2><p className="mt-1 text-sm text-muted-foreground">{data.email_sent ? 'Sent to attendees' : currentStatus === 'awaiting_email_review' ? 'Waiting for your approval' : 'Draft generated by the workflow'}</p></div>{canReviewEmail && <button className={primaryButton} onClick={() => setIsEmailReviewOpen(true)}>Review email</button>}</div><div className="mt-5 whitespace-pre-wrap rounded-lg border border-border bg-muted/30 p-4 text-sm leading-7">{data.email_draft || 'No email draft is available.'}</div></section>}
    {tab === 'activity' && <section className={card}><h2 className="font-semibold">Activity</h2><ol className="mt-5 space-y-5 border-l border-border pl-5"><li><p className="text-sm font-medium">Meeting updated</p><p className="mt-1 text-xs text-muted-foreground">{new Date(data.updated_at).toLocaleString()}</p></li><li><p className="text-sm font-medium">Current status: <span className="capitalize">{currentStatus.replace(/_/g, ' ')}</span></p><p className="mt-1 text-xs text-muted-foreground">Based on the latest backend workflow state</p></li><li><p className="text-sm font-medium">Meeting created</p><p className="mt-1 text-xs text-muted-foreground">{new Date(data.created_at).toLocaleString()}</p></li></ol></section>}

    {canManage && <MeetingEditDialog isOpen={isEditOpen} meeting={data} initialFocus={editFocus} isSaving={updateMeeting.isPending} onClose={() => setIsEditOpen(false)} onSave={data => updateMeeting.mutateAsync(data).then(() => undefined)} />}
    {canManage && <HumanReviewModal isOpen={isReviewOpen} onClose={() => setIsReviewOpen(false)} reviewContent={review.data} onSubmitReview={async request => { await submitReview.mutateAsync(request); }} isLoading={review.isLoading || submitReview.isPending} />}
    {canManage && <EmailReviewModal isOpen={isEmailReviewOpen} onClose={() => setIsEmailReviewOpen(false)} emailDraft={emailDraft.data} onSubmitReview={async request => { await submitEmailReview.mutateAsync(request); }} isLoading={emailDraft.isLoading || submitEmailReview.isPending} />}
    {canManage && <ConfirmDialog isOpen={isStopOpen} onClose={() => setIsStopOpen(false)} onConfirm={() => stop.mutate()} title="Stop processing?" description="The current workflow will stop safely. You can start a fresh run later." confirmLabel="Yes, stop processing" isDestructive isLoading={stop.isPending} />}
    {canManage && <ConfirmDialog isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} onConfirm={() => deleteMeeting.mutate()} title="Delete meeting?" description={`Delete "${data.title}" and its generated artifacts? This cannot be undone.`} confirmLabel="Delete meeting" isDestructive isLoading={deleteMeeting.isPending} />}
  </div>;
}
