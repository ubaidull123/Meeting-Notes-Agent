import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CreditCard, FileAudio, FileText, ListTodo, Mail, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { meetingsApi } from '../api/meetings';
import { tasksApi } from '../api/tasks';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const actionClass = 'inline-flex items-center justify-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm font-semibold hover:bg-muted';

export function DashboardPage() {
  const { profile } = useAuth();
  const meetings = useQuery({ queryKey: ['meetings', 'dashboard'], queryFn: () => meetingsApi.listMeetings({ page_size: 100 }) });
  const tasks = useQuery({ queryKey: ['tasks', 'dashboard'], queryFn: () => tasksApi.listTasks({ page_size: 100 }) });
  if (meetings.isError || tasks.isError) return <ErrorState message={formatErrorMessage(meetings.error ?? tasks.error)} onRetry={() => { void meetings.refetch(); void tasks.refetch(); }} />;
  if (meetings.isLoading || tasks.isLoading) return <LoadingState />;

  const items = meetings.data ?? [];
  const openTasks = (tasks.data?.tasks ?? []).filter((task) => task.status !== 'done').length;
  const review = items.filter((meeting) => meeting.status === 'awaiting_review');
  const emailReview = items.filter((meeting) => meeting.status === 'awaiting_email_review');
  const recent = items.slice(0, 5);

  return <div className="space-y-7">
    <header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-bold">Welcome back, {profile?.full_name.split(' ')[0]}</h1><p className="mt-1 text-sm text-muted-foreground">Meetings and follow-up that need your attention.</p></div><Link to="/meetings/new" className="inline-flex items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"><Plus className="h-4 w-4"/>New meeting</Link></header>
    <section className="flex flex-wrap gap-2" aria-label="Create meeting"><Link to="/meetings/new" className={actionClass}><FileAudio className="h-4 w-4"/>Upload recording</Link><Link to="/meetings/new" className={actionClass}><FileText className="h-4 w-4"/>Paste transcript</Link></section>
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
      { label: 'Meetings awaiting review', value: review.length, icon: AlertTriangle, path: '/meetings' },
      { label: 'Emails awaiting approval', value: emailReview.length, icon: Mail, path: '/meetings' },
      { label: 'Open tasks', value: openTasks, icon: ListTodo, path: '/tasks' },
      { label: 'Credit balance', value: profile?.credits?.balance ?? '-', icon: CreditCard, path: '/settings/usage' },
    ].map(({ label, value, icon: Icon, path }) => <Link to={path} key={label} className="rounded-md border border-border p-4 hover:border-teal-500/50"><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-teal-600"/></div><p className="mt-3 text-2xl font-semibold">{value}</p></Link>)}</section>
    {(review.length > 0 || emailReview.length > 0) && <section><h2 className="text-sm font-semibold">Needs attention</h2><div className="mt-3 divide-y divide-border rounded-md border border-border">{[...review, ...emailReview].slice(0, 5).map((meeting) => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="flex items-center justify-between gap-3 p-3 hover:bg-muted/40"><span><span className="block text-sm font-medium">{meeting.title}</span><span className="text-xs text-muted-foreground">{formatDate(meeting.meeting_date)}</span></span><StatusBadge status={meeting.status}/></Link>)}</div></section>}
    <section><div className="flex items-center justify-between"><h2 className="text-sm font-semibold">Recent meetings</h2><Link to="/meetings" className="text-sm font-semibold text-teal-700">View all</Link></div>{recent.length ? <div className="mt-3 divide-y divide-border rounded-md border border-border">{recent.map((meeting) => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="flex items-center justify-between gap-3 p-3 hover:bg-muted/40"><span><span className="block text-sm font-medium">{meeting.title}</span><span className="text-xs text-muted-foreground">{meeting.project_name || 'No project'} / {formatDate(meeting.meeting_date)}</span></span><StatusBadge status={meeting.status}/></Link>)}</div> : <EmptyState title="No meetings yet" description="Create a meeting from a recording or transcript." />}</section>
  </div>;
}
