import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CalendarClock, CheckCircle2, FileText, FolderKanban, ListTodo, Mail, Plus, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi } from '../api/teams';
import { tasksApi } from '../api/tasks';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatCard } from '../components/ui/StatCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { PageHeader, primaryButton, secondaryButton, SectionCard } from '../components/ui/Workspace';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { TaskStatus } from '../types/task';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

export function DashboardPage() {
  const { profile, user } = useAuth();
  const { activeTeam, activeRole, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const meetings = useQuery({ queryKey: ['meetings', activeTeam?.id, 'dashboard'], queryFn: () => meetingsApi.listMeetings({ team_id: activeTeam!.id, page_size: 100 }), enabled: Boolean(activeTeam) });
  const tasks = useQuery({ queryKey: ['tasks', activeTeam?.id, 'dashboard'], queryFn: () => tasksApi.listTasks({ team_id: activeTeam!.id, page_size: 100 }), enabled: Boolean(activeTeam) });
  const projects = useQuery({ queryKey: ['projects', activeTeam?.id], queryFn: () => projectsApi.listProjects(activeTeam!.id), enabled: Boolean(activeTeam) });
  const recent = (meetings.data ?? []).slice(0, 5);
  const meetingDetails = useQueries({ queries: canManageActiveTeam ? [] : recent.map(meeting => ({ queryKey: ['meeting', meeting.id], queryFn: () => meetingsApi.getMeeting(meeting.id) })) });
  const updateTask = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.updateTask(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }),
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (!activeTeam) return <EmptyState title="No team workspace" description="Create or join a team to open your dashboard." />;
  if (meetings.isError || tasks.isError || projects.isError) return <ErrorState message={formatErrorMessage(meetings.error ?? tasks.error ?? projects.error)} onRetry={() => { void meetings.refetch(); void tasks.refetch(); void projects.refetch(); }} />;
  if (meetings.isLoading || tasks.isLoading || projects.isLoading) return <LoadingState label="Preparing your workspace..." />;

  const allTasks = tasks.data?.tasks ?? [];
  const myTasks = allTasks.filter(task => task.assigned_user_id === user?.id);
  const openTasks = allTasks.filter(task => task.status !== 'done');
  const overdue = openTasks.filter(task => task.due_date && new Date(task.due_date) < new Date());
  const review = (meetings.data ?? []).filter(meeting => meeting.status === 'awaiting_review');
  const emailReview = (meetings.data ?? []).filter(meeting => meeting.status === 'awaiting_email_review');

  if (canManageActiveTeam) return <div className="space-y-6">
    <PageHeader eyebrow={`${activeRole} workspace`} title={activeTeam.name} description="Monitor reviews, follow-up work, and the projects your team is moving forward." actions={<>
      <Link to="/members" className={secondaryButton}><UserPlus className="h-4 w-4" />Add member</Link>
      <Link to="/projects" className={secondaryButton}><FolderKanban className="h-4 w-4" />New project</Link>
      <Link to="/meetings/new" className={primaryButton}><Plus className="h-4 w-4" />New meeting</Link>
    </>} />

    <section aria-labelledby="attention-heading">
      <div className="mb-3"><h2 id="attention-heading" className="text-sm font-semibold text-foreground">Needs attention</h2><p className="mt-0.5 text-xs text-muted-foreground">Live workflow items across this team.</p></div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Link to="/meetings"><StatCard title="Awaiting review" value={review.length} subtitle="Meeting outputs" icon={AlertTriangle} iconColor="text-violet-600" iconBg="bg-violet-50 border-violet-100 dark:bg-violet-950/50 dark:border-violet-900" /></Link>
        <Link to="/meetings"><StatCard title="Email approvals" value={emailReview.length} subtitle="Drafts ready to send" icon={Mail} iconColor="text-indigo-600" iconBg="bg-indigo-50 border-indigo-100 dark:bg-indigo-950/50 dark:border-indigo-900" /></Link>
        <Link to="/tasks"><StatCard title="Open tasks" value={openTasks.length} subtitle="Across team projects" icon={ListTodo} /></Link>
        <Link to="/tasks"><StatCard title="Overdue" value={overdue.length} subtitle="Past their due date" icon={CalendarClock} iconColor={overdue.length ? 'text-rose-600' : 'text-muted-foreground'} iconBg={overdue.length ? 'bg-rose-50 border-rose-100 dark:bg-rose-950/50 dark:border-rose-900' : 'bg-muted border-border'} /></Link>
      </div>
    </section>

    <div className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
      <MeetingList title="Recent meetings" description="Latest activity in this workspace" meetings={recent} />
      <ProjectList title="Projects" description={`${projects.data?.length ?? 0} visible in this team`} projects={projects.data ?? []} />
    </div>
    <SectionCard title="Open work" description="The next tasks your team can move forward" icon={ListTodo} action={<Link to="/tasks" className="text-xs font-semibold text-primary hover:underline">View all tasks</Link>} contentClassName="p-0">
      {openTasks.length ? <div className="divide-y divide-border/70">{openTasks.slice(0, 6).map(task => <div key={task.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-5"><div className="min-w-0"><p className="truncate text-sm font-medium">{task.title}</p><p className="mt-0.5 text-xs text-muted-foreground">{task.meeting_title}{task.due_date ? ` · Due ${formatDate(task.due_date)}` : ''}</p></div><StatusBadge status={task.status} size="sm" /></div>)}</div> : <CompactEmpty text="No open tasks in this team." />}
    </SectionCard>
  </div>;

  const decisions = meetingDetails.flatMap(query => query.data?.redacted_decisions?.length ? query.data.redacted_decisions : query.data?.decisions ?? []).slice(0, 5);
  const summaries = meetingDetails.flatMap((query, index) => {
    const summary = query.data?.redacted_summary || query.data?.summary;
    return summary && recent[index] ? [{ meeting: recent[index], summary }] : [];
  }).slice(0, 4);
  const dueSoon = myTasks.filter(task => task.status !== 'done' && task.due_date).length;
  return <div className="space-y-6">
    <PageHeader eyebrow={`Member · ${activeTeam.name}`} title={`Welcome back, ${profile?.full_name.split(' ')[0] ?? 'there'}`} description="Your assigned work, recent meetings, and project context in one place." />
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Link to="/tasks"><StatCard title="My open tasks" value={myTasks.filter(task => task.status !== 'done').length} subtitle="Assigned to you" icon={ListTodo} /></Link>
      <Link to="/tasks"><StatCard title="With due dates" value={dueSoon} subtitle="Plan your next steps" icon={CalendarClock} iconColor="text-sky-600" iconBg="bg-sky-50 border-sky-100 dark:bg-sky-950/50 dark:border-sky-900" /></Link>
      <Link to="/projects"><StatCard title="My projects" value={projects.data?.length ?? 0} subtitle="Authorized workspaces" icon={FolderKanban} iconColor="text-violet-600" iconBg="bg-violet-50 border-violet-100 dark:bg-violet-950/50 dark:border-violet-900" /></Link>
      <Link to="/meetings"><StatCard title="Recent meetings" value={recent.length} subtitle="Available to review" icon={CheckCircle2} iconColor="text-emerald-600" iconBg="bg-emerald-50 border-emerald-100 dark:bg-emerald-950/50 dark:border-emerald-900" /></Link>
    </div>
    <SectionCard title="My tasks" description="Update progress as your work moves forward" icon={ListTodo} action={<Link to="/tasks" className="text-xs font-semibold text-primary hover:underline">View all</Link>} contentClassName="p-0">
      {myTasks.length ? <div className="divide-y divide-border/70">{myTasks.slice(0, 6).map(task => <div key={task.id} className="flex flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-5"><div className="min-w-0"><p className="truncate text-sm font-medium">{task.title}</p><p className="mt-0.5 text-xs text-muted-foreground">{task.due_date ? `Due ${formatDate(task.due_date)}` : task.meeting_title}</p></div><select aria-label={`Update ${task.title} status`} className="rounded-lg border border-input bg-background px-2.5 py-1.5 text-xs font-semibold" value={task.status} onChange={event => updateTask.mutate({ id: task.id, status: event.target.value as TaskStatus })}>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(status => <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>)}</select></div>)}</div> : <CompactEmpty text="No tasks are assigned to you." />}
    </SectionCard>
    <div className="grid gap-5 xl:grid-cols-2">
      <MeetingList title="Recent meetings" description="Meetings from your assigned projects" meetings={recent} />
      <ProjectList title="My projects" description="Projects you can access" projects={projects.data ?? []} />
    </div>
    <div className="grid gap-5 xl:grid-cols-2">
      <SectionCard title="Recent summaries" description="What came out of meetings you participated in" icon={FileText} contentClassName="p-0">
        {summaries.length ? <div className="divide-y divide-border/70">{summaries.map(item => <Link key={item.meeting.id} to={`/meetings/${item.meeting.id}`} className="block px-4 py-3.5 transition-colors hover:bg-muted/40 sm:px-5"><p className="text-sm font-medium">{item.meeting.title}</p><p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">{item.summary}</p></Link>)}</div> : <CompactEmpty text="No recent summaries are available." />}
      </SectionCard>
      <SectionCard title="Recent decisions" description="Key outcomes from meetings you can access" icon={CheckCircle2}>
        {decisions.length ? <ul className="space-y-3">{decisions.map((decision, index) => <li key={`${decision}-${index}`} className="flex gap-3 text-sm leading-6"><span className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />{decision}</li>)}</ul> : <p className="text-sm text-muted-foreground">No recent decisions are available.</p>}
      </SectionCard>
    </div>
  </div>;
}

function MeetingList({ title, description, meetings }: { title: string; description: string; meetings: Array<{ id: string; title: string; meeting_date: string; project_name?: string | null; status: string }> }) {
  return <SectionCard title={title} description={description} action={<Link to="/meetings" className="text-xs font-semibold text-primary hover:underline">View all</Link>} contentClassName="p-0">
    {meetings.length ? <div className="divide-y divide-border/70">{meetings.map(meeting => <Link to={`/meetings/${meeting.id}`} key={meeting.id} className="flex items-center justify-between gap-4 px-4 py-3.5 transition-colors hover:bg-muted/40 sm:px-5"><div className="min-w-0"><p className="truncate text-sm font-medium">{meeting.title}</p><p className="mt-0.5 truncate text-xs text-muted-foreground">{meeting.project_name || 'Team meeting'} · {formatDate(meeting.meeting_date)}</p></div><StatusBadge status={meeting.status} size="sm" /></Link>)}</div> : <CompactEmpty text="No recent meetings." />}
  </SectionCard>;
}

function ProjectList({ title, description, projects }: { title: string; description: string; projects: Array<{ id: string; name: string; description?: string | null }> }) {
  return <SectionCard title={title} description={description} icon={FolderKanban} action={<Link to="/projects" className="text-xs font-semibold text-primary hover:underline">View all</Link>} contentClassName="p-0">
    {projects.length ? <div className="divide-y divide-border/70">{projects.slice(0, 5).map(project => <Link key={project.id} to={`/projects/${project.id}`} className="flex items-center gap-3 px-4 py-3.5 transition-colors hover:bg-muted/40 sm:px-5"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><FolderKanban className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-medium">{project.name}</span><span className="block truncate text-xs text-muted-foreground">{project.description || 'No description added'}</span></span></Link>)}</div> : <CompactEmpty text="No projects are available." />}
  </SectionCard>;
}

function CompactEmpty({ text }: { text: string }) {
  return <p className="px-5 py-8 text-center text-sm text-muted-foreground">{text}</p>;
}
