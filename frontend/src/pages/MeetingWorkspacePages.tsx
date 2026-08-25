import { FormEvent, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CalendarDays, FileAudio, FileText, Loader2, Plus, Upload, Users } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi, teamsApi } from '../api/teams';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Avatar, fieldClass, PageHeader, primaryButton, secondaryButton, SectionCard } from '../components/ui/Workspace';
import { useTeam } from '../context/TeamContext';
import { MeetingStatus } from '../types/meeting';
import { MemberOption } from '../types/team';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const meetingStatuses: MeetingStatus[] = ['draft', 'uploaded', 'queued', 'processing', 'awaiting_review', 'revision_requested', 'awaiting_email_review', 'completed', 'rejected', 'failed', 'cancelled'];

export function MeetingsWorkspacePage() {
  const { activeTeam, canManageActiveTeam } = useTeam();
  const [status, setStatus] = useState('');
  const meetings = useQuery({ queryKey: ['meetings', activeTeam?.id, status], queryFn: () => meetingsApi.listMeetings({ team_id: activeTeam!.id, status: (status || undefined) as MeetingStatus | undefined, page_size: 100 }), enabled: Boolean(activeTeam) });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to view meetings." />;

  return <div className="space-y-6">
    <PageHeader title="Meetings" description={`Authorized meeting history and workflow state in ${activeTeam.name}.`} icon={CalendarDays} actions={canManageActiveTeam && <Link className={primaryButton} to="/meetings/new"><Plus className="h-4 w-4" />Create meeting</Link>} />
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><label className="text-xs font-semibold text-muted-foreground">Workflow status<select aria-label="Filter meetings by status" className={`mt-1.5 block w-full sm:w-64 ${fieldClass}`} value={status} onChange={event => setStatus(event.target.value)}><option value="">All statuses</option>{meetingStatuses.map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}</select></label>{meetings.data && <p className="text-xs text-muted-foreground">{meetings.data.length} meeting{meetings.data.length === 1 ? '' : 's'} shown</p>}</div>
    {meetings.isLoading ? <LoadingState label="Loading meetings..." /> : meetings.isError ? <ErrorState message={formatErrorMessage(meetings.error)} onRetry={() => meetings.refetch()} /> : meetings.data?.length ? <SectionCard contentClassName="p-0"><div className="divide-y divide-border/70">{meetings.data.map(meeting => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="group flex flex-col gap-3 px-4 py-4 transition-colors hover:bg-muted/35 sm:flex-row sm:items-center sm:justify-between sm:px-5"><div className="flex min-w-0 items-start gap-3"><span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><FileText className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-semibold group-hover:text-primary">{meeting.title}</span><span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground"><span>{meeting.project_name || 'Team meeting'}</span><span aria-hidden="true">·</span><span>{formatDate(meeting.meeting_date)}</span></span></span></div><StatusBadge status={meeting.status} size="sm" /></Link>)}</div></SectionCard> : <EmptyState icon={CalendarDays} title="No meetings found" description={canManageActiveTeam ? status ? 'No meetings match this workflow status.' : 'Create a meeting to begin capturing decisions and follow-up work.' : 'No meetings are available in your assigned projects.'} action={canManageActiveTeam && !status ? { label: 'Create meeting', icon: Plus, onClick: () => { window.location.href = '/meetings/new'; } } : undefined} />}
  </div>;
}

export function CreateMeetingWorkspacePage() {
  const navigate = useNavigate();
  const { activeTeam } = useTeam();
  const [inputType, setInputType] = useState<'text' | 'transcript' | 'audio'>('text');
  const [file, setFile] = useState<File | null>(null);
  const [participantIds, setParticipantIds] = useState<number[]>([]);
  const [form, setForm] = useState({ title: '', meeting_date: new Date().toISOString().slice(0, 10), meeting_time: '', project_id: '', agenda: '', notes: '', transcript_text: '' });
  const [error, setError] = useState('');
  const projects = useQuery({ queryKey: ['projects', activeTeam?.id], queryFn: () => projectsApi.listProjects(activeTeam!.id), enabled: Boolean(activeTeam) });
  const participants = useQuery<MemberOption[]>({ queryKey: ['meeting-participant-options', activeTeam?.id, form.project_id || 'team'], queryFn: async () => form.project_id ? await projectsApi.listMembers(form.project_id) : await teamsApi.listMembers(activeTeam!.id), enabled: Boolean(activeTeam) });
  const create = useMutation({
    mutationFn: async () => {
      const meeting = await meetingsApi.createMeeting({ title: form.title, meeting_date: form.meeting_date, meeting_time: form.meeting_time || null, team_id: activeTeam!.id, project_id: form.project_id || null, project_name: projects.data?.find(project => project.id === form.project_id)?.name ?? null, agenda: form.agenda.split('\n').map(value => value.trim()).filter(Boolean), notes: form.notes || null, participant_user_ids: participantIds, transcript_text: inputType === 'text' ? form.transcript_text : null });
      if (file) { if (inputType === 'audio') await meetingsApi.uploadAudio(meeting.id, file); else await meetingsApi.uploadTranscript(meeting.id, file); }
      return meeting;
    },
    onSuccess: meeting => { toast.success('Meeting created'); navigate(`/meetings/${meeting.id}`); },
    onError: mutationError => setError(formatErrorMessage(mutationError)),
  });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team before creating a meeting." />;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!participantIds.length) { setError('Select at least one meeting participant.'); return; }
    if (inputType === 'text' && !form.transcript_text.trim()) { setError('Paste the transcript to continue.'); return; }
    if (inputType !== 'text' && !file) { setError('Choose a file to continue.'); return; }
    setError(''); create.mutate();
  };

  return <div className="mx-auto max-w-4xl space-y-6">
    <PageHeader eyebrow={<Link to="/meetings" className="normal-case tracking-normal text-primary hover:underline">Back to meetings</Link>} title="Create meeting" description={`Add a transcript or recording to ${activeTeam.name}. Processing starts only when you choose to run it.`} icon={CalendarDays} />
    <form onSubmit={submit} className="space-y-5">
      <SectionCard title="Meeting details" description="Give the meeting enough context to make its output useful." icon={FileText}>
        <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium sm:col-span-2">Meeting title<input className={`mt-1.5 ${fieldClass}`} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} placeholder="Weekly product review" required /></label><label className="text-sm font-medium">Date<input className={`mt-1.5 ${fieldClass}`} type="date" value={form.meeting_date} onChange={event => setForm({ ...form, meeting_date: event.target.value })} required /></label><label className="text-sm font-medium">Time <span className="font-normal text-muted-foreground">(optional)</span><input className={`mt-1.5 ${fieldClass}`} type="time" value={form.meeting_time} onChange={event => setForm({ ...form, meeting_time: event.target.value })} /></label><label className="text-sm font-medium sm:col-span-2">Project<select className={`mt-1.5 ${fieldClass}`} value={form.project_id} onChange={event => { setForm({ ...form, project_id: event.target.value }); setParticipantIds([]); }}><option value="">Team-level meeting</option>{projects.data?.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}</select><span className="mt-1.5 block text-xs font-normal text-muted-foreground">Participants are selected from this Project. Team-level meetings use joined Team members.</span></label><label className="text-sm font-medium sm:col-span-2">Agenda <span className="font-normal text-muted-foreground">(one item per line)</span><textarea className={`mt-1.5 ${fieldClass}`} rows={3} value={form.agenda} onChange={event => setForm({ ...form, agenda: event.target.value })} /></label><label className="text-sm font-medium sm:col-span-2">Internal notes <span className="font-normal text-muted-foreground">(optional)</span><textarea className={`mt-1.5 ${fieldClass}`} rows={3} value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} /></label></div>
      </SectionCard>
      <SectionCard title="Meeting participants" description="Choose the Project members involved in this meeting. Email recipients are selected separately during review." icon={Users}>{participants.isLoading ? <LoadingState label="Loading eligible participants..." /> : <div className="grid gap-2 sm:grid-cols-2">{participants.data?.filter(member => member.status === 'active' && member.user_id).map(member => { const userId = member.user_id!; const selected = participantIds.includes(userId); return <label key={member.id} className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${selected ? 'border-primary/30 bg-primary/5' : 'border-border hover:bg-muted/40'}`}><input type="checkbox" checked={selected} onChange={() => setParticipantIds(current => selected ? current.filter(id => id !== userId) : [...current, userId])} /><Avatar name={member.full_name} /><span className="min-w-0"><span className="block truncate text-sm font-medium">{member.full_name}</span><span className="block truncate text-xs text-muted-foreground">{member.title || member.department || member.email}</span></span></label>; })}{!participants.data?.some(member => member.status === 'active' && member.user_id) && <p className="text-sm text-muted-foreground sm:col-span-2">Add joined members to this {form.project_id ? 'Project' : 'Team'} before creating the meeting.</p>}</div>}</SectionCard>
      <SectionCard title="Meeting source" description="Choose exactly one source for this meeting." icon={FileAudio}>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">{([['text', 'Paste transcript', FileText], ['transcript', 'Transcript file', Upload], ['audio', 'Audio file', FileAudio]] as const).map(([value, label, Icon]) => <button key={value} type="button" onClick={() => { setInputType(value); setFile(null); }} className={`flex items-center gap-3 rounded-lg border px-3 py-3 text-left text-sm font-semibold transition-colors ${inputType === value ? 'border-primary/30 bg-primary/10 text-primary' : 'border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Icon className="h-4 w-4 shrink-0" />{label}</button>)}</div>
        {inputType === 'text' ? <textarea aria-label="Meeting transcript" className={`mt-4 ${fieldClass}`} rows={10} placeholder="Paste the meeting transcript here..." value={form.transcript_text} onChange={event => setForm({ ...form, transcript_text: event.target.value })} /> : <label className="mt-4 flex min-h-40 cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-input bg-muted/20 p-6 text-center text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-background shadow-sm"><Upload className="h-5 w-5 text-primary" /></span><strong className="text-foreground">{file ? file.name : `Choose a ${inputType === 'audio' ? 'recording' : 'transcript'}`}</strong><span className="text-xs">{inputType === 'audio' ? 'MP3, WAV, or M4A' : 'TXT or MD'}</span><input className="sr-only" type="file" accept={inputType === 'audio' ? '.mp3,.wav,.m4a' : '.txt,.md'} onChange={event => setFile(event.target.files?.[0] ?? null)} /></label>}
      </SectionCard>
      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700" role="alert">{error}</div>}
      <div className="flex flex-col-reverse gap-2 border-t border-border pt-5 sm:flex-row sm:justify-end"><Link to="/meetings" className={secondaryButton}>Cancel</Link><button className={primaryButton} disabled={create.isPending}>{create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}{create.isPending ? 'Creating meeting...' : 'Create meeting'}</button></div>
    </form>
  </div>;
}
