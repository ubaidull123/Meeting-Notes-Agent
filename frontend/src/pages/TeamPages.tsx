import { FormEvent, useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FolderKanban, Loader2, Plus, Trash2, UserPlus, Users } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi, teamsApi } from '../api/teams';
import { tasksApi } from '../api/tasks';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { StatusBadge } from '../components/ui/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { Project, TeamRole } from '../types/team';
import { TaskStatus } from '../types/task';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const card = 'rounded-xl border border-border bg-card p-5 shadow-sm';
const field = 'w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/30';
const primary = 'inline-flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60';
const secondary = 'inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold hover:bg-muted disabled:opacity-60';

export function ProjectsPage() {
  const { activeTeam, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', context: '' });
  const projects = useQuery({
    queryKey: ['projects', activeTeam?.id],
    queryFn: () => projectsApi.listProjects(activeTeam!.id),
    enabled: Boolean(activeTeam),
  });
  const create = useMutation({
    mutationFn: () => projectsApi.createProject(activeTeam!.id, {
      name: form.name,
      description: form.description || null,
      context: form.context || null,
    }),
    onSuccess: () => {
      setForm({ name: '', description: '', context: '' });
      setIsCreating(false);
      queryClient.invalidateQueries({ queryKey: ['projects', activeTeam?.id] });
      toast.success('Project created');
    },
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (!activeTeam) return <EmptyState title="No team available" description="Create or join a team to access projects." />;
  if (projects.isLoading) return <LoadingState label="Loading projects..." />;
  if (projects.isError) return <ErrorState message={formatErrorMessage(projects.error)} onRetry={() => projects.refetch()} />;

  return <div className="space-y-6">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-bold">Projects</h1><p className="mt-1 text-sm text-muted-foreground">Projects you can access in {activeTeam.name}.</p></div>{canManageActiveTeam && <button className={primary} onClick={() => setIsCreating(value => !value)}><Plus className="h-4 w-4" />New project</button>}</header>
    {isCreating && <form className={card + ' space-y-4'} onSubmit={(event: FormEvent) => { event.preventDefault(); create.mutate(); }}>
      <h2 className="font-semibold">Create project</h2>
      <label className="block text-sm font-medium">Name<input className={'mt-1 ' + field} value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} required /></label>
      <label className="block text-sm font-medium">Description<textarea className={'mt-1 ' + field} rows={2} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></label>
      <label className="block text-sm font-medium">Project context<textarea className={'mt-1 ' + field} rows={4} value={form.context} onChange={event => setForm({ ...form, context: event.target.value })} placeholder="Context used by authorized meeting processing" /></label>
      <div className="flex justify-end gap-2"><button type="button" className={secondary} onClick={() => setIsCreating(false)}>Cancel</button><button className={primary} disabled={create.isPending}>{create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Create project</button></div>
    </form>}
    {projects.data?.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.data.map(project => <Link key={project.id} to={`/projects/${project.id}`} className={card + ' transition-colors hover:border-teal-500/60'}><FolderKanban className="h-5 w-5 text-teal-600" /><h2 className="mt-4 font-semibold">{project.name}</h2><p className="mt-2 line-clamp-3 text-sm text-muted-foreground">{project.description || 'No description provided.'}</p><p className="mt-4 text-xs text-muted-foreground">Updated {formatDate(project.updated_at)}</p></Link>)}</div> : <EmptyState title="No projects" description={canManageActiveTeam ? 'Create a project and assign members to it.' : 'You have not been assigned to a project in this team.'} />}
  </div>;
}

type ProjectTab = 'overview' | 'members' | 'meetings' | 'tasks' | 'context';

export function ProjectPage() {
  const { projectId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { canManageTeam } = useTeam();
  const [tab, setTab] = useState<ProjectTab>('overview');
  const [memberId, setMemberId] = useState('');
  const [context, setContext] = useState('');
  const project = useQuery({ queryKey: ['project', projectId], queryFn: () => projectsApi.getProject(projectId) });
  const canManage = canManageTeam(project.data?.team_id);
  const members = useQuery({ queryKey: ['project-members', projectId], queryFn: () => projectsApi.listMembers(projectId), enabled: tab === 'members' });
  const meetings = useQuery({ queryKey: ['meetings', project.data?.team_id, projectId], queryFn: () => meetingsApi.listMeetings({ team_id: project.data!.team_id, project_id: projectId, page_size: 100 }), enabled: Boolean(project.data) && tab === 'meetings' });
  const tasks = useQuery({ queryKey: ['tasks', project.data?.team_id, projectId], queryFn: () => tasksApi.listTasks({ team_id: project.data!.team_id, project_id: projectId, page_size: 100 }), enabled: Boolean(project.data) && tab === 'tasks' });

  useEffect(() => { if (project.data) setContext(project.data.context ?? ''); }, [project.data]);

  const update = useMutation({
    mutationFn: (data: Partial<Project>) => projectsApi.updateProject(projectId, data),
    onSuccess: updated => { queryClient.setQueryData(['project', projectId], updated); queryClient.invalidateQueries({ queryKey: ['projects', updated.team_id] }); toast.success('Project updated'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const addMember = useMutation({
    mutationFn: () => projectsApi.addMember(projectId, Number(memberId)),
    onSuccess: () => { setMemberId(''); queryClient.invalidateQueries({ queryKey: ['project-members', projectId] }); toast.success('Project member added'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const removeMember = useMutation({
    mutationFn: (userId: number) => projectsApi.removeMember(projectId, userId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['project-members', projectId] }); toast.success('Project member removed'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const updateTask = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.updateTask(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', project.data?.team_id, projectId] }),
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const removeProject = useMutation({
    mutationFn: () => projectsApi.deleteProject(projectId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['projects'] }); navigate('/projects'); toast.success('Project deleted'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (project.isLoading) return <LoadingState label="Loading project..." />;
  if (!project.data) return <ErrorState message={formatErrorMessage(project.error, 'Project not found.')} onRetry={() => project.refetch()} />;
  const data = project.data;
  const tabs: Array<{ id: ProjectTab; label: string }> = [
    { id: 'overview', label: 'Overview' }, { id: 'members', label: 'Members' }, { id: 'meetings', label: 'Meetings' }, { id: 'tasks', label: 'Tasks' }, { id: 'context', label: 'Project Context' },
  ];

  return <div className="space-y-6">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><Link to="/projects" className="text-sm font-semibold text-teal-700">Projects</Link><h1 className="mt-2 text-3xl font-bold">{data.name}</h1><p className="mt-1 text-sm text-muted-foreground">{data.description || 'No project description.'}</p></div>{canManage && <button className="inline-flex items-center gap-2 rounded-lg border border-rose-300 px-3 py-2 text-sm font-semibold text-rose-700" onClick={() => { if (window.confirm(`Delete ${data.name}? Meetings and tasks will be retained without this project.`)) removeProject.mutate(); }}><Trash2 className="h-4 w-4" />Delete project</button>}</header>
    <nav className="flex flex-wrap border-b border-border">{tabs.map(item => <button key={item.id} className={'border-b-2 px-4 py-2.5 text-sm font-medium ' + (tab === item.id ? 'border-teal-600 text-teal-700' : 'border-transparent text-muted-foreground')} onClick={() => setTab(item.id)}>{item.label}</button>)}</nav>
    {tab === 'overview' && <section className={card}><h2 className="font-semibold">Overview</h2><dl className="mt-4 grid gap-4 sm:grid-cols-3"><div><dt className="text-xs uppercase text-muted-foreground">Created</dt><dd className="mt-1 text-sm">{formatDate(data.created_at)}</dd></div><div><dt className="text-xs uppercase text-muted-foreground">Updated</dt><dd className="mt-1 text-sm">{formatDate(data.updated_at)}</dd></div><div><dt className="text-xs uppercase text-muted-foreground">Access</dt><dd className="mt-1 text-sm">{canManage ? 'Team management' : 'Project member'}</dd></div></dl></section>}
    {tab === 'members' && <div className="space-y-4">{canManage && <form className={card + ' flex flex-wrap items-end gap-3'} onSubmit={(event: FormEvent) => { event.preventDefault(); addMember.mutate(); }}><label className="min-w-64 flex-1 text-sm font-medium">Existing team member user ID<input className={'mt-1 ' + field} type="number" min="1" value={memberId} onChange={event => setMemberId(event.target.value)} required /></label><button className={primary} disabled={addMember.isPending}><UserPlus className="h-4 w-4" />Add member</button></form>}{members.isLoading ? <LoadingState /> : <section className={card}>{members.data?.map(member => <div key={member.id} className="flex items-center justify-between gap-3 border-b border-border py-3 last:border-0"><div><p className="text-sm font-medium">{member.full_name}</p><p className="text-xs text-muted-foreground">{member.email}</p></div>{canManage && member.user_id !== data.created_by && <button className="text-sm font-semibold text-rose-600" onClick={() => removeMember.mutate(member.user_id)}>Remove</button>}</div>)}</section>}</div>}
    {tab === 'meetings' && (meetings.isLoading ? <LoadingState /> : meetings.data?.length ? <section className={card}>{meetings.data.map(meeting => <Link key={meeting.id} to={`/meetings/${meeting.id}`} className="flex items-center justify-between gap-3 border-b border-border py-3 last:border-0"><span><span className="block text-sm font-medium">{meeting.title}</span><span className="text-xs text-muted-foreground">{formatDate(meeting.meeting_date)}</span></span><StatusBadge status={meeting.status} /></Link>)}</section> : <EmptyState title="No project meetings" description="Meetings assigned to this project will appear here." />)}
    {tab === 'tasks' && (tasks.isLoading ? <LoadingState /> : tasks.data?.tasks.length ? <section className={card}>{tasks.data.tasks.map(task => { const canUpdate = canManage || task.assigned_user_id === user?.id; return <div key={task.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-3 last:border-0"><div><p className="text-sm font-medium">{task.title}</p><p className="text-xs text-muted-foreground">{task.meeting_title}</p></div><select className="rounded-lg border border-input bg-background px-2 py-1 text-sm" value={task.status} disabled={!canUpdate} onChange={event => updateTask.mutate({ id: task.id, status: event.target.value as TaskStatus })}>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(status => <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>)}</select></div>; })}</section> : <EmptyState title="No project tasks" description="Tasks generated from project meetings will appear here." />)}
    {tab === 'context' && <section className={card}><h2 className="font-semibold">Project context</h2><p className="mt-1 text-sm text-muted-foreground">Used only for authorized meeting processing in this project.</p>{canManage ? <><textarea className={'mt-4 ' + field} rows={10} value={context} onChange={event => setContext(event.target.value)} /><button className={primary + ' mt-3'} onClick={() => update.mutate({ context })} disabled={update.isPending}>Save context</button></> : <p className="mt-4 whitespace-pre-wrap text-sm leading-7">{context || 'No project context has been added.'}</p>}</section>}
  </div>;
}

export function MembersPage() {
  const { activeTeam, activeRole } = useTeam();
  const queryClient = useQueryClient();
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState<TeamRole>('member');
  const members = useQuery({ queryKey: ['team-members', activeTeam?.id], queryFn: () => teamsApi.listMembers(activeTeam!.id), enabled: Boolean(activeTeam) });
  const add = useMutation({ mutationFn: () => teamsApi.addMember(activeTeam!.id, Number(userId), role), onSuccess: () => { setUserId(''); setRole('member'); queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }); toast.success('Team member added'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const updateRole = useMutation({ mutationFn: ({ id, nextRole }: { id: number; nextRole: TeamRole }) => teamsApi.updateMemberRole(activeTeam!.id, id, nextRole), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }), onError: error => toast.error(formatErrorMessage(error)) });
  const remove = useMutation({ mutationFn: (id: number) => teamsApi.removeMember(activeTeam!.id, id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }); queryClient.invalidateQueries({ queryKey: ['projects', activeTeam?.id] }); toast.success('Team member removed'); }, onError: error => toast.error(formatErrorMessage(error)) });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to manage members." />;
  if (members.isLoading) return <LoadingState label="Loading team members..." />;
  if (members.isError) return <ErrorState message={formatErrorMessage(members.error)} onRetry={() => members.refetch()} />;
  return <div className="space-y-6"><header><h1 className="text-2xl font-bold">Team members</h1><p className="mt-1 text-sm text-muted-foreground">Manage access to {activeTeam.name}. Project access is assigned separately.</p></header><form className={card + ' flex flex-wrap items-end gap-3'} onSubmit={(event: FormEvent) => { event.preventDefault(); add.mutate(); }}><label className="min-w-56 flex-1 text-sm font-medium">Existing user ID<input className={'mt-1 ' + field} type="number" min="1" value={userId} onChange={event => setUserId(event.target.value)} required /></label><label className="text-sm font-medium">Team role<select className={'mt-1 ' + field} value={role} onChange={event => setRole(event.target.value as TeamRole)}><option value="member">Member</option>{activeRole === 'owner' && <option value="admin">Admin</option>}</select></label><button className={primary} disabled={add.isPending}><UserPlus className="h-4 w-4" />Add member</button></form><section className={card}>{members.data?.map(member => <div key={member.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-3 last:border-0"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-teal-100 font-semibold text-teal-800"><Users className="h-4 w-4" /></span><span><span className="block text-sm font-medium">{member.full_name}</span><span className="text-xs text-muted-foreground">{member.email}</span></span></div><div className="flex items-center gap-3">{activeRole === 'owner' && member.role !== 'owner' ? <select className="rounded-lg border border-input bg-background px-2 py-1 text-sm" value={member.role} onChange={event => updateRole.mutate({ id: member.user_id, nextRole: event.target.value as TeamRole })}><option value="member">Member</option><option value="admin">Admin</option></select> : <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-semibold capitalize">{member.role}</span>}{member.role !== 'owner' && <button className="text-sm font-semibold text-rose-600" onClick={() => remove.mutate(member.user_id)}>Remove</button>}</div></div>)}</section></div>;
}

export function TeamSettingsPage() {
  const { activeTeam, refreshTeams } = useTeam();
  const [form, setForm] = useState({ name: '', description: '' });
  useEffect(() => { if (activeTeam) setForm({ name: activeTeam.name, description: activeTeam.description ?? '' }); }, [activeTeam]);
  const save = useMutation({ mutationFn: () => teamsApi.updateTeam(activeTeam!.id, { name: form.name, description: form.description || null }), onSuccess: async () => { await refreshTeams(); toast.success('Team settings saved'); }, onError: error => toast.error(formatErrorMessage(error)) });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to open its settings." />;
  return <div className="space-y-6"><header><h1 className="text-2xl font-bold">Team settings</h1><p className="mt-1 text-sm text-muted-foreground">Workspace settings are separate from your personal account.</p></header><form className={card + ' max-w-2xl space-y-4'} onSubmit={(event: FormEvent) => { event.preventDefault(); save.mutate(); }}><label className="block text-sm font-medium">Team name<input className={'mt-1 ' + field} value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} required /></label><label className="block text-sm font-medium">Description<textarea className={'mt-1 ' + field} rows={4} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /></label><button className={primary} disabled={save.isPending}>{save.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Save settings</button></form></div>;
}
