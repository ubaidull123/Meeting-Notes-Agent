import { FormEvent, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Loader2, Plus, Upload } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi } from '../api/teams';
import { AttendeeEditor, AttendeeItem } from '../components/ui/AttendeeEditor';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useTeam } from '../context/TeamContext';
import { MeetingStatus } from '../types/meeting';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const field = 'w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/30';
const button = 'inline-flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60';
const card = 'rounded-xl border border-border bg-card p-5 shadow-sm';

export function MeetingsWorkspacePage() {
  const { activeTeam, canManageActiveTeam } = useTeam();
  const [status, setStatus] = useState('');
  const meetings = useQuery({
    queryKey: ['meetings', activeTeam?.id, status],
    queryFn: () => meetingsApi.listMeetings({ team_id: activeTeam!.id, status: (status || undefined) as MeetingStatus | undefined, page_size: 100 }),
    enabled: Boolean(activeTeam),
  });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to view meetings." />;
  return <div className="space-y-6"><header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-bold">Meetings</h1><p className="mt-1 text-sm text-muted-foreground">Authorized meetings in {activeTeam.name}.</p></div>{canManageActiveTeam && <Link className={button} to="/meetings/new"><Plus className="h-4 w-4" />Create meeting</Link>}</header><select aria-label="Filter meetings by status" className={field + ' max-w-xs'} value={status} onChange={event => setStatus(event.target.value)}><option value="">All statuses</option>{['draft', 'uploaded', 'queued', 'processing', 'awaiting_review', 'revision_requested', 'awaiting_email_review', 'completed', 'rejected', 'failed', 'cancelled'].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}</select>{meetings.isLoading ? <LoadingState /> : meetings.isError ? <ErrorState message={formatErrorMessage(meetings.error)} onRetry={() => meetings.refetch()} /> : meetings.data?.length ? <section className={card + ' divide-y divide-border'}>{meetings.data.map(meeting => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="flex items-center justify-between gap-3 py-3 hover:bg-muted/30"><span><span className="block text-sm font-medium">{meeting.title}</span><span className="text-xs text-muted-foreground">{meeting.project_name || 'Team meeting'} · {formatDate(meeting.meeting_date)}</span></span><StatusBadge status={meeting.status} /></Link>)}</section> : <EmptyState title="No meetings found" description={canManageActiveTeam ? 'Create a meeting or try another status filter.' : 'No meetings are available in your assigned projects.'} />}</div>;
}

export function CreateMeetingWorkspacePage() {
  const navigate = useNavigate();
  const { activeTeam } = useTeam();
  const [inputType, setInputType] = useState<'text' | 'transcript' | 'audio'>('text');
  const [file, setFile] = useState<File | null>(null);
  const [attendees, setAttendees] = useState<AttendeeItem[]>([{ name: '', email: '' }]);
  const [form, setForm] = useState({ title: '', meeting_date: new Date().toISOString().slice(0, 10), meeting_time: '', project_id: '', agenda: '', notes: '', transcript_text: '' });
  const [error, setError] = useState('');
  const projects = useQuery({ queryKey: ['projects', activeTeam?.id], queryFn: () => projectsApi.listProjects(activeTeam!.id), enabled: Boolean(activeTeam) });
  const create = useMutation({
    mutationFn: async () => {
      const meeting = await meetingsApi.createMeeting({
        title: form.title,
        meeting_date: form.meeting_date,
        meeting_time: form.meeting_time || null,
        team_id: activeTeam!.id,
        project_id: form.project_id || null,
        project_name: projects.data?.find(project => project.id === form.project_id)?.name ?? null,
        agenda: form.agenda.split('\n').map(value => value.trim()).filter(Boolean),
        notes: form.notes || null,
        attendees,
        transcript_text: inputType === 'text' ? form.transcript_text : null,
      });
      if (file) {
        if (inputType === 'audio') await meetingsApi.uploadAudio(meeting.id, file);
        else await meetingsApi.uploadTranscript(meeting.id, file);
      }
      return meeting;
    },
    onSuccess: meeting => { toast.success('Meeting created'); navigate(`/meetings/${meeting.id}`); },
    onError: mutationError => setError(formatErrorMessage(mutationError)),
  });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team before creating a meeting." />;
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!attendees.every(attendee => attendee.name.trim() && /^\S+@\S+\.\S+$/.test(attendee.email))) { setError('Add a name and valid email for every attendee.'); return; }
    if (inputType === 'text' && !form.transcript_text.trim()) { setError('Paste the transcript to continue.'); return; }
    if (inputType !== 'text' && !file) { setError('Choose a file to continue.'); return; }
    setError(''); create.mutate();
  };
  return <div className="max-w-3xl"><header className="mb-6"><h1 className="text-2xl font-bold">Create meeting</h1><p className="mt-1 text-sm text-muted-foreground">Create a meeting in {activeTeam.name} and optionally assign it to a project.</p></header><form onSubmit={submit} className="space-y-5"><section className={card}><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium sm:col-span-2">Meeting title<input className={'mt-1 ' + field} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} required /></label><label className="text-sm font-medium">Date<input className={'mt-1 ' + field} type="date" value={form.meeting_date} onChange={event => setForm({ ...form, meeting_date: event.target.value })} required /></label><label className="text-sm font-medium">Time<input className={'mt-1 ' + field} type="time" value={form.meeting_time} onChange={event => setForm({ ...form, meeting_time: event.target.value })} /></label><label className="text-sm font-medium sm:col-span-2">Project<select className={'mt-1 ' + field} value={form.project_id} onChange={event => setForm({ ...form, project_id: event.target.value })}><option value="">Team-level meeting</option>{projects.data?.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><label className="text-sm font-medium sm:col-span-2">Agenda <span className="font-normal text-muted-foreground">(one item per line)</span><textarea className={'mt-1 ' + field} rows={3} value={form.agenda} onChange={event => setForm({ ...form, agenda: event.target.value })} /></label><label className="text-sm font-medium sm:col-span-2">Notes<textarea className={'mt-1 ' + field} rows={3} value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} /></label></div></section><section className={card}><AttendeeEditor attendees={attendees} onChange={setAttendees} /></section><section className={card}><h2 className="font-semibold">Meeting input</h2><p className="mt-1 text-sm text-muted-foreground">Choose one source. Processing remains asynchronous.</p><div className="mt-4 grid grid-cols-3 gap-2">{([['text', 'Paste transcript'], ['transcript', 'Transcript file'], ['audio', 'Audio file']] as const).map(([value, label]) => <button key={value} type="button" onClick={() => { setInputType(value); setFile(null); }} className={'rounded-lg border px-3 py-2 text-sm font-medium ' + (inputType === value ? 'border-teal-600 bg-teal-50 text-teal-800 dark:bg-teal-950/40' : 'border-border hover:bg-muted')}>{label}</button>)}</div>{inputType === 'text' ? <textarea className={'mt-4 ' + field} rows={9} placeholder="Paste the meeting transcript here..." value={form.transcript_text} onChange={event => setForm({ ...form, transcript_text: event.target.value })} /> : <label className="mt-4 flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-input p-8 text-sm text-muted-foreground hover:bg-muted"><Upload className="h-4 w-4" />{file ? file.name : `Choose a ${inputType === 'audio' ? 'MP3, WAV, or M4A' : 'TXT or MD'} file`}<input className="sr-only" type="file" accept={inputType === 'audio' ? '.mp3,.wav,.m4a' : '.txt,.md'} onChange={event => setFile(event.target.files?.[0] ?? null)} /></label>}</section>{error && <p className="text-sm text-rose-600">{error}</p>}<div className="flex justify-end gap-3"><Link to="/meetings" className="rounded-lg px-4 py-2 text-sm font-medium hover:bg-muted">Cancel</Link><button className={button} disabled={create.isPending}>{create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Create meeting</button></div></form></div>;
}
