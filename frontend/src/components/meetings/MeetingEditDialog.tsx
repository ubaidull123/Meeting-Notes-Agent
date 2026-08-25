import { FormEvent, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, X } from 'lucide-react';
import { projectsApi, teamsApi } from '../../api/teams';
import { Meeting, MeetingUpdateRequest } from '../../types/meeting';
import { MemberOption } from '../../types/team';
import { Avatar, fieldClass, primaryButton, secondaryButton } from '../ui/Workspace';

interface MeetingEditDialogProps {
  isOpen: boolean;
  meeting: Meeting;
  initialFocus?: 'title' | 'notes';
  isSaving: boolean;
  onClose: () => void;
  onSave: (data: MeetingUpdateRequest) => Promise<void>;
}

export function MeetingEditDialog({ isOpen, meeting, initialFocus = 'title', isSaving, onClose, onSave }: MeetingEditDialogProps) {
  const [title, setTitle] = useState(meeting.title);
  const [meetingDate, setMeetingDate] = useState(meeting.meeting_date);
  const [meetingTime, setMeetingTime] = useState(meeting.meeting_time ?? '');
  const [notes, setNotes] = useState(meeting.notes ?? '');
  const [agenda, setAgenda] = useState(meeting.agenda.join('\n'));
  const [participantIds, setParticipantIds] = useState<number[]>(meeting.attendees.flatMap(participant => participant.user_id ? [participant.user_id] : []));
  const [error, setError] = useState('');
  const participantOptions = useQuery<MemberOption[]>({ queryKey: ['meeting-participant-options', meeting.team_id, meeting.project_id || 'team'], queryFn: async () => meeting.project_id ? await projectsApi.listMembers(meeting.project_id) : await teamsApi.listMembers(meeting.team_id), enabled: isOpen });

  useEffect(() => {
    if (!isOpen) return;
    setTitle(meeting.title);
    setMeetingDate(meeting.meeting_date);
    setMeetingTime(meeting.meeting_time ?? '');
    setNotes(meeting.notes ?? '');
    setAgenda(meeting.agenda.join('\n'));
    setParticipantIds(meeting.attendees.flatMap(participant => participant.user_id ? [participant.user_id] : []));
    setError('');
  }, [isOpen, meeting]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen && !isSaving) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSaving, onClose]);

  if (!isOpen) return null;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim()) return setError('Meeting title is required.');
    if (!meetingDate) return setError('Meeting date is required.');
    if (meeting.restrict_to_participants && !participantIds.length) return setError('Select at least one meeting participant.');
    setError('');
    try {
      await onSave({
        title: title.trim(),
        meeting_date: meetingDate,
        meeting_time: meetingTime || null,
        notes: notes.trim() || null,
        agenda: agenda.split('\n').map(item => item.trim()).filter(Boolean),
        ...(participantIds.length ? { participant_user_ids: participantIds } : {}),
      });
    } catch {
      // The mutation surfaces the backend error in the shared toast UI.
    }
  };

  return <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5" role="dialog" aria-modal="true" aria-labelledby="edit-meeting-title">
    <button className="fixed inset-0 cursor-default bg-slate-950/50 backdrop-blur-[2px]" onClick={() => !isSaving && onClose()} aria-label="Close edit meeting dialog" />
    <form onSubmit={submit} className="relative z-10 max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-xl border border-border bg-card shadow-2xl">
      <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border bg-card px-4 py-4 sm:px-5">
        <div><h2 id="edit-meeting-title" className="text-lg font-semibold">Edit meeting</h2><p className="mt-1 text-sm text-muted-foreground">Update the meeting details used throughout this workspace.</p></div>
        <button type="button" onClick={onClose} disabled={isSaving} className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground" aria-label="Close"><X className="h-4 w-4" /></button>
      </div>
      <div className="grid gap-4 p-4 sm:grid-cols-2 sm:p-5">
        <label className="text-sm font-medium sm:col-span-2">Meeting title<input autoFocus={initialFocus === 'title'} className={`mt-1.5 ${fieldClass}`} value={title} onChange={event => setTitle(event.target.value)} maxLength={500} required /></label>
        <label className="text-sm font-medium">Date<input className={`mt-1.5 ${fieldClass}`} type="date" value={meetingDate} onChange={event => setMeetingDate(event.target.value)} required /></label>
        <label className="text-sm font-medium">Time<input className={`mt-1.5 ${fieldClass}`} type="time" value={meetingTime} onChange={event => setMeetingTime(event.target.value)} /></label>
        <div className="sm:col-span-2"><span className="text-sm font-medium">Project</span><p className="mt-1.5 rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm">{meeting.project_name || 'Team-level meeting'}</p></div>
        <label className="text-sm font-medium sm:col-span-2">Agenda <span className="font-normal text-muted-foreground">(one item per line)</span><textarea className={`mt-1.5 ${fieldClass}`} rows={3} value={agenda} onChange={event => setAgenda(event.target.value)} /></label>
        <label className="text-sm font-medium sm:col-span-2">Notes<textarea autoFocus={initialFocus === 'notes'} className={`mt-1.5 ${fieldClass}`} rows={4} value={notes} onChange={event => setNotes(event.target.value)} placeholder="Add context or notes for this meeting" /></label>
      </div>
      <div className="mx-4 rounded-lg border border-border p-4 sm:mx-5"><div><h3 className="text-sm font-semibold">Meeting participants</h3><p className="mt-1 text-xs text-muted-foreground">Only eligible {meeting.project_id ? 'Project' : 'Team'} members can be selected.</p></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{participantOptions.data?.filter(member => member.status === 'active' && member.user_id).map(member => { const userId = member.user_id!; const selected = participantIds.includes(userId); return <label key={member.id} className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${selected ? 'border-primary/30 bg-primary/5' : 'border-border'}`}><input type="checkbox" checked={selected} onChange={() => setParticipantIds(current => selected ? current.filter(id => id !== userId) : [...current, userId])} /><Avatar name={member.full_name} /><span className="min-w-0"><span className="block truncate text-sm font-medium">{member.full_name}</span><span className="block truncate text-xs text-muted-foreground">{member.title || member.department || member.email}</span></span></label>; })}</div></div>
      {error && <p className="mx-4 mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 sm:mx-5">{error}</p>}
      <div className="sticky bottom-0 mt-5 flex flex-col-reverse gap-2 border-t border-border bg-card px-4 py-3 sm:flex-row sm:justify-end sm:px-5">
        <button type="button" onClick={onClose} disabled={isSaving} className={secondaryButton}>Cancel</button>
        <button type="submit" disabled={isSaving} className={primaryButton}>{isSaving && <Loader2 className="h-4 w-4 animate-spin" />}Save changes</button>
      </div>
    </form>
  </div>;
}
