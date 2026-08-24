import { FormEvent, useEffect, useState } from 'react';
import { Loader2, X } from 'lucide-react';
import { Meeting, MeetingUpdateRequest } from '../../types/meeting';
import { AttendeeEditor, AttendeeItem } from '../ui/AttendeeEditor';

interface MeetingEditDialogProps {
  isOpen: boolean;
  meeting: Meeting;
  initialFocus?: 'title' | 'notes';
  isSaving: boolean;
  onClose: () => void;
  onSave: (data: MeetingUpdateRequest) => Promise<void>;
}

const field = 'mt-1 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20';

export function MeetingEditDialog({ isOpen, meeting, initialFocus = 'title', isSaving, onClose, onSave }: MeetingEditDialogProps) {
  const [title, setTitle] = useState(meeting.title);
  const [meetingDate, setMeetingDate] = useState(meeting.meeting_date);
  const [meetingTime, setMeetingTime] = useState(meeting.meeting_time ?? '');
  const [projectName, setProjectName] = useState(meeting.project_name ?? '');
  const [notes, setNotes] = useState(meeting.notes ?? '');
  const [agenda, setAgenda] = useState(meeting.agenda.join('\n'));
  const [attendees, setAttendees] = useState<AttendeeItem[]>(meeting.attendees.map(({ name, email }) => ({ name, email })));
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    setTitle(meeting.title);
    setMeetingDate(meeting.meeting_date);
    setMeetingTime(meeting.meeting_time ?? '');
    setProjectName(meeting.project_name ?? '');
    setNotes(meeting.notes ?? '');
    setAgenda(meeting.agenda.join('\n'));
    setAttendees(meeting.attendees.map(({ name, email }) => ({ name, email })));
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
    if (!attendees.length || !attendees.every(attendee => attendee.name.trim() && /^\S+@\S+\.\S+$/.test(attendee.email))) {
      return setError('Add a name and valid email for every attendee.');
    }
    setError('');
    try {
      await onSave({
        title: title.trim(),
        meeting_date: meetingDate,
        meeting_time: meetingTime || null,
        project_name: projectName.trim() || null,
        notes: notes.trim() || null,
        agenda: agenda.split('\n').map(item => item.trim()).filter(Boolean),
        attendees: attendees.map(attendee => ({ name: attendee.name.trim(), email: attendee.email.trim() })),
      });
    } catch {
      // The mutation surfaces the backend error in the shared toast UI.
    }
  };

  return <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="edit-meeting-title">
    <button className="fixed inset-0 cursor-default bg-black/60 backdrop-blur-xs" onClick={() => !isSaving && onClose()} aria-label="Close edit meeting dialog" />
    <form onSubmit={submit} className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-card p-5 shadow-2xl sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <div><h2 id="edit-meeting-title" className="text-lg font-semibold">Edit meeting</h2><p className="mt-1 text-sm text-muted-foreground">Update the meeting details used throughout this workspace.</p></div>
        <button type="button" onClick={onClose} disabled={isSaving} className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground" aria-label="Close"><X className="h-4 w-4" /></button>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium sm:col-span-2">Meeting title<input autoFocus={initialFocus === 'title'} className={field} value={title} onChange={event => setTitle(event.target.value)} maxLength={500} required /></label>
        <label className="text-sm font-medium">Date<input className={field} type="date" value={meetingDate} onChange={event => setMeetingDate(event.target.value)} required /></label>
        <label className="text-sm font-medium">Time<input className={field} type="time" value={meetingTime} onChange={event => setMeetingTime(event.target.value)} /></label>
        <label className="text-sm font-medium sm:col-span-2">Project<input className={field} value={projectName} onChange={event => setProjectName(event.target.value)} maxLength={255} /></label>
        <label className="text-sm font-medium sm:col-span-2">Agenda <span className="font-normal text-muted-foreground">(one item per line)</span><textarea className={field} rows={3} value={agenda} onChange={event => setAgenda(event.target.value)} /></label>
        <label className="text-sm font-medium sm:col-span-2">Notes<textarea autoFocus={initialFocus === 'notes'} className={field} rows={4} value={notes} onChange={event => setNotes(event.target.value)} placeholder="Add context or notes for this meeting" /></label>
      </div>
      <div className="mt-5 rounded-lg border border-border p-4"><AttendeeEditor attendees={attendees} onChange={setAttendees} /></div>
      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" onClick={onClose} disabled={isSaving} className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground">Cancel</button>
        <button type="submit" disabled={isSaving} className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60">{isSaving && <Loader2 className="h-4 w-4 animate-spin" />}Save changes</button>
      </div>
    </form>
  </div>;
}
