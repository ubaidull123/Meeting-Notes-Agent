import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CalendarClock, FolderKanban, ListTodo, Mail, Plus, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi } from '../api/teams';
import { tasksApi } from '../api/tasks';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { TaskStatus } from '../types/task';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const actionClass = 'inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold hover:bg-muted';
const card = 'rounded-xl border border-border bg-card p-5 shadow-sm';

export function DashboardPage() {
  const { profile, user } = useAuth();
  const { activeTeam, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const meetings = useQuery({
    queryKey: ['meetings', activeTeam?.id, 'dashboard'],
    queryFn: () => meetingsApi.listMeetings({ team_id: activeTeam!.id, page_size: 100 }),
    enabled: Boolean(activeTeam),
  });
  const tasks = useQuery({
    queryKey: ['tasks', activeTeam?.id, 'dashboard'],
    queryFn: () => tasksApi.listTasks({ team_id: activeTeam!.id, page_size: 100 }),
    enabled: Boolean(activeTeam),
  });
  const projects = useQuery({
    queryKey: ['projects', activeTeam?.id],
    queryFn: () => projectsApi.listProjects(activeTeam!.id),
    enabled: Boolean(activeTeam),
  });
  const recent = (meetings.data ?? []).slice(0, 5);
  const meetingDetails = useQueries({
    queries: canManageActiveTeam ? [] : recent.map(meeting => ({
      queryKey: ['meeting', meeting.id],
      queryFn: () => meetingsApi.getMeeting(meeting.id),
    })),
  });
  const updateTask = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.updateTask(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }),
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (!activeTeam) return <EmptyState title="No team workspace" description="Create or join a team to open your dashboard." />;
  if (meetings.isError || tasks.isError || projects.isError) return <ErrorState message={formatErrorMessage(meetings.error ?? tasks.error ?? projects.error)} onRetry={() => { void meetings.refetch(); void tasks.refetch(); void projects.refetch(); }} />;
  if (meetings.isLoading || tasks.isLoading || projects.isLoading) return <LoadingState />;

  const allTasks = tasks.data?.tasks ?? [];
  const myTasks = allTasks.filter(task => task.assigned_user_id === user?.id);
  const openTasks = allTasks.filter(task => task.status !== 'done');
  const overdue = openTasks.filter(task => task.due_date && new Date(task.due_date) < new Date());
  const review = (meetings.data ?? []).filter(meeting => meeting.status === 'awaiting_review');
  const emailReview = (meetings.data ?? []).filter(meeting => meeting.status === 'awaiting_email_review');

  if (canManageActiveTeam) return <div className="space-y-7">
    <header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-bold">{activeTeam.name}</h1><p className="mt-1 text-sm text-muted-foreground">Team operations and workflow items that need attention.</p></div><div className="flex flex-wrap gap-2"><Link to="/meetings/new" className={actionClass}><Plus className="h-4 w-4" />New meeting</Link><Link to="/projects" className={actionClass}><FolderKanban className="h-4 w-4" />New project</Link><Link to="/members" className={actionClass}><UserPlus className="h-4 w-4" />Add member</Link></div></header>
    <section><h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Needs attention</h2><div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
      { label: 'Meetings awaiting review', value: review.length, icon: AlertTriangle, path: '/meetings' },
      { label: 'Emails awaiting approval', value: emailReview.length, icon: Mail, path: '/meetings' },
      { label: 'Open tasks', value: openTasks.length, icon: ListTodo, path: '/tasks' },
      { label: 'Overdue tasks', value: overdue.length, icon: CalendarClock, path: '/tasks' },
    ].map(({ label, value, icon: Icon, path }) => <Link to={path} key={label} className={card + ' hover:border-teal-500/50'}><div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">{label}</p><Icon className="h-4 w-4 text-teal-600" /></div><p className="mt-3 text-2xl font-semibold">{value}</p></Link>)}</div></section>
    <div className="grid gap-5 xl:grid-cols-2"><MeetingList title="Recent meetings" meetings={recent} /><section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">Projects</h2><Link to="/projects" className="text-sm font-semibold text-teal-700">View all</Link></div><div className="mt-3 space-y-2">{projects.data?.slice(0, 5).map(project => <Link key={project.id} to={`/projects/${project.id}`} className="flex items-center gap-3 rounded-lg border border-border p-3 hover:bg-muted/40"><FolderKanban className="h-4 w-4 text-teal-600" /><span className="text-sm font-medium">{project.name}</span></Link>)}</div></section></div>
  </div>;

  const decisions = meetingDetails.flatMap(query => query.data?.redacted_decisions?.length ? query.data.redacted_decisions : query.data?.decisions ?? []).slice(0, 5);
  return <div className="space-y-7">
    <header><h1 className="text-2xl font-bold">Welcome back, {profile?.full_name.split(' ')[0]}</h1><p className="mt-1 text-sm text-muted-foreground">Your assigned work in {activeTeam.name}.</p></header>
    <section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">My tasks</h2><Link to="/tasks" className="text-sm font-semibold text-teal-700">View all</Link></div>{myTasks.length ? <div className="mt-3 divide-y divide-border">{myTasks.slice(0, 6).map(task => <div key={task.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><span><span className="block text-sm font-medium">{task.title}</span><span className="text-xs text-muted-foreground">{task.due_date ? `Due ${formatDate(task.due_date)}` : task.meeting_title}</span></span><select className="rounded-lg border border-input bg-background px-2 py-1 text-sm" value={task.status} onChange={event => updateTask.mutate({ id: task.id, status: event.target.value as TaskStatus })}>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(status => <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>)}</select></div>)}</div> : <p className="mt-3 text-sm text-muted-foreground">No tasks are assigned to you.</p>}</section>
    <div className="grid gap-5 xl:grid-cols-2"><MeetingList title="Recent meetings" meetings={recent} /><section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">My projects</h2><Link to="/projects" className="text-sm font-semibold text-teal-700">View all</Link></div><div className="mt-3 space-y-2">{projects.data?.map(project => <Link key={project.id} to={`/projects/${project.id}`} className="flex items-center gap-3 rounded-lg border border-border p-3 hover:bg-muted/40"><FolderKanban className="h-4 w-4 text-teal-600" /><span className="text-sm font-medium">{project.name}</span></Link>)}</div></section></div>
    <section className={card}><h2 className="font-semibold">Recent decisions</h2>{decisions.length ? <ul className="mt-3 space-y-2">{decisions.map((decision, index) => <li key={`${decision}-${index}`} className="flex gap-2 text-sm"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />{decision}</li>)}</ul> : <p className="mt-3 text-sm text-muted-foreground">No recent decisions are available.</p>}</section>
  </div>;
}

function MeetingList({ title, meetings }: { title: string; meetings: Array<{ id: string; title: string; meeting_date: string; project_name?: string | null; status: string }> }) {
  return <section className={card}><div className="flex items-center justify-between"><h2 className="font-semibold">{title}</h2><Link to="/meetings" className="text-sm font-semibold text-teal-700">View all</Link></div>{meetings.length ? <div className="mt-3 divide-y divide-border">{meetings.map(meeting => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="flex items-center justify-between gap-3 py-3"><span><span className="block text-sm font-medium">{meeting.title}</span><span className="text-xs text-muted-foreground">{meeting.project_name || 'Team meeting'} · {formatDate(meeting.meeting_date)}</span></span><StatusBadge status={meeting.status} /></Link>)}</div> : <p className="mt-3 text-sm text-muted-foreground">No recent meetings.</p>}</section>;
}
