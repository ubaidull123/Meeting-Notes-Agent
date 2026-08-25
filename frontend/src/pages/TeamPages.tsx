import { FormEvent, useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CalendarDays, FileText, FolderKanban, Loader2, Plus, ShieldCheck, Trash2, UserPlus, Users } from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { meetingsApi } from '../api/meetings';
import { projectsApi, teamsApi } from '../api/teams';
import { tasksApi } from '../api/tasks';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { PriorityBadge } from '../components/ui/PriorityBadge';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Avatar, dangerButton, fieldClass, PageHeader, primaryButton, secondaryButton, SectionCard, WorkspaceTabs } from '../components/ui/Workspace';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { Project, TeamRole } from '../types/team';
import { TaskStatus } from '../types/task';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

export function ProjectsPage() {
  const { activeTeam, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', context: '' });
  const projects = useQuery({ queryKey: ['projects', activeTeam?.id], queryFn: () => projectsApi.listProjects(activeTeam!.id), enabled: Boolean(activeTeam) });
  const create = useMutation({
    mutationFn: () => projectsApi.createProject(activeTeam!.id, { name: form.name, description: form.description || null, context: form.context || null }),
    onSuccess: () => { setForm({ name: '', description: '', context: '' }); setIsCreating(false); queryClient.invalidateQueries({ queryKey: ['projects', activeTeam?.id] }); toast.success('Project created'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (!activeTeam) return <EmptyState title="No team available" description="Create or join a team to access projects." />;
  if (projects.isLoading) return <LoadingState label="Loading projects..." />;
  if (projects.isError) return <ErrorState message={formatErrorMessage(projects.error)} onRetry={() => projects.refetch()} />;

  return <div className="space-y-6">
    <PageHeader title="Projects" description={`Focused workspaces you can access in ${activeTeam.name}.`} icon={FolderKanban} actions={canManageActiveTeam && <button className={primaryButton} onClick={() => setIsCreating(value => !value)}><Plus className="h-4 w-4" />New project</button>} />
    {isCreating && <SectionCard title="Create a project" description="Organize meetings, members, tasks, and AI context around one initiative." icon={Plus}>
      <form className="space-y-5" onSubmit={(event: FormEvent) => { event.preventDefault(); create.mutate(); }}>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium sm:col-span-2">Project name<input className={`mt-1.5 ${fieldClass}`} value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} placeholder="e.g. Customer onboarding" required /></label>
          <label className="text-sm font-medium sm:col-span-2">Description <span className="font-normal text-muted-foreground">(optional)</span><textarea className={`mt-1.5 ${fieldClass}`} rows={2} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} placeholder="A concise description visible to project members" /></label>
          <label className="text-sm font-medium sm:col-span-2">AI project context <span className="font-normal text-muted-foreground">(optional)</span><textarea className={`mt-1.5 ${fieldClass}`} rows={4} value={form.context} onChange={event => setForm({ ...form, context: event.target.value })} placeholder="Goals, terminology, customer background, or constraints used during authorized meeting processing" /><span className="mt-1.5 block text-xs font-normal leading-5 text-muted-foreground">Only authorized meetings in this project use this context.</span></label>
        </div>
        <div className="flex justify-end gap-2 border-t border-border pt-4"><button type="button" className={secondaryButton} onClick={() => setIsCreating(false)}>Cancel</button><button className={primaryButton} disabled={create.isPending}>{create.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Create project</button></div>
      </form>
    </SectionCard>}
    {projects.data?.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.data.map(project => <Link key={project.id} to={`/projects/${project.id}`} className="group flex min-h-48 flex-col rounded-xl border border-border/80 bg-card p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md">
      <div className="flex items-start justify-between gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary"><FolderKanban className="h-[18px] w-[18px]" /></span><span className="rounded-md bg-muted px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Project</span></div>
      <h2 className="mt-4 text-base font-semibold tracking-tight group-hover:text-primary">{project.name}</h2>
      <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-muted-foreground">{project.description || 'No description has been added yet.'}</p>
      <div className="mt-auto flex items-center gap-1.5 border-t border-border/70 pt-4 text-xs text-muted-foreground"><CalendarDays className="h-3.5 w-3.5" />Updated {formatDate(project.updated_at)}</div>
    </Link>)}</div> : <EmptyState icon={FolderKanban} title="No projects yet" description={canManageActiveTeam ? 'Create the first project, then assign the members who should have access.' : 'You have not been assigned to a project in this team.'} action={canManageActiveTeam ? { label: 'Create project', icon: Plus, onClick: () => setIsCreating(true) } : undefined} />}
  </div>;
}

type ProjectTab = 'overview' | 'members' | 'meetings' | 'tasks' | 'context';

export function ProjectPage() {
  const { projectId = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { activeTeam, canManageTeam } = useTeam();
  const [tab, setTab] = useState<ProjectTab>('overview');
  const [memberId, setMemberId] = useState('');
  const [context, setContext] = useState('');
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const project = useQuery({ queryKey: ['project', activeTeam?.id, projectId], queryFn: () => projectsApi.getProject(projectId), enabled: Boolean(activeTeam) });
  const canManage = canManageTeam(project.data?.team_id);
  const members = useQuery({ queryKey: ['project-members', activeTeam?.id, projectId], queryFn: () => projectsApi.listMembers(projectId), enabled: Boolean(activeTeam) && tab === 'members' });
  const teamMembers = useQuery({ queryKey: ['team-members', project.data?.team_id], queryFn: () => teamsApi.listMembers(project.data!.team_id), enabled: Boolean(project.data && canManage && tab === 'members') });
  const meetings = useQuery({ queryKey: ['meetings', project.data?.team_id, projectId], queryFn: () => meetingsApi.listMeetings({ team_id: project.data!.team_id, project_id: projectId, page_size: 100 }), enabled: Boolean(project.data) && tab === 'meetings' });
  const tasks = useQuery({ queryKey: ['tasks', project.data?.team_id, projectId], queryFn: () => tasksApi.listTasks({ team_id: project.data!.team_id, project_id: projectId, page_size: 100 }), enabled: Boolean(project.data) && tab === 'tasks' });

  useEffect(() => { if (project.data) setContext(project.data.context ?? ''); }, [project.data]);
  const update = useMutation({ mutationFn: (data: Partial<Project>) => projectsApi.updateProject(projectId, data), onSuccess: updated => { queryClient.setQueryData(['project', activeTeam?.id, projectId], updated); queryClient.invalidateQueries({ queryKey: ['projects', updated.team_id] }); toast.success('Project updated'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const addMember = useMutation({ mutationFn: () => projectsApi.addMember(projectId, Number(memberId)), onSuccess: () => { setMemberId(''); queryClient.invalidateQueries({ queryKey: ['project-members', activeTeam?.id, projectId] }); toast.success('Project member added'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const removeMember = useMutation({ mutationFn: (userId: number) => projectsApi.removeMember(projectId, userId), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['project-members', activeTeam?.id, projectId] }); toast.success('Project member removed'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const updateTask = useMutation({ mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => tasksApi.updateTask(id, { status }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', project.data?.team_id, projectId] }), onError: error => toast.error(formatErrorMessage(error)) });
  const removeProject = useMutation({ mutationFn: () => projectsApi.deleteProject(projectId), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['projects'] }); navigate('/projects'); toast.success('Project deleted'); }, onError: error => toast.error(formatErrorMessage(error)) });

  if (project.isLoading) return <LoadingState label="Loading project..." />;
  if (!project.data) return <ErrorState message={formatErrorMessage(project.error, 'Project not found.')} onRetry={() => project.refetch()} />;
  const data = project.data;
  const tabs: Array<{ id: ProjectTab; label: string; count?: number }> = [
    { id: 'overview', label: 'Overview' }, { id: 'members', label: 'Members', count: members.data?.length }, { id: 'meetings', label: 'Meetings', count: meetings.data?.length }, { id: 'tasks', label: 'Tasks', count: tasks.data?.tasks.length }, { id: 'context', label: 'Project context' },
  ];
  const projectMemberIds = new Set(members.data?.map(member => member.user_id) ?? []);
  const availableTeamMembers = teamMembers.data?.filter(member => member.status === 'active' && member.user_id && !projectMemberIds.has(member.user_id)) ?? [];

  return <div className="space-y-6">
    <PageHeader eyebrow={<Link to="/projects" className="inline-flex items-center gap-1.5 normal-case tracking-normal text-primary hover:underline"><ArrowLeft className="h-3.5 w-3.5" />All projects</Link>} title={data.name} description={data.description || 'No project description has been added.'} icon={FolderKanban} actions={canManage && <button className={dangerButton} onClick={() => setIsDeleteOpen(true)}><Trash2 className="h-4 w-4" />Delete project</button>} />
    <WorkspaceTabs items={tabs} active={tab} onChange={setTab} label="Project workspace" />

    {tab === 'overview' && <div className="grid gap-5 lg:grid-cols-[1.35fr_.65fr]">
      <SectionCard title="Project overview" description="Workspace metadata and access" icon={FileText}>
        <dl className="grid gap-5 sm:grid-cols-3"><Meta label="Created" value={formatDate(data.created_at)} /><Meta label="Last updated" value={formatDate(data.updated_at)} /><Meta label="Your access" value={canManage ? 'Team management' : 'Project member'} /></dl>
      </SectionCard>
      <SectionCard title="AI context" description="Used during meeting processing" icon={ShieldCheck}><p className="line-clamp-5 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{data.context || 'No project context has been added.'}</p>{data.context && <button className="mt-3 text-xs font-semibold text-primary hover:underline" onClick={() => setTab('context')}>View full context</button>}</SectionCard>
    </div>}

    {tab === 'members' && <div className="space-y-4">
      {canManage && <SectionCard title="Add project access" description="Choose a joined Team member. Internal user IDs are never required." icon={UserPlus}><form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={(event: FormEvent) => { event.preventDefault(); addMember.mutate(); }}><label className="flex-1 text-sm font-medium">Team member<select className={`mt-1.5 ${fieldClass}`} value={memberId} onChange={event => setMemberId(event.target.value)} required><option value="">Select a person</option>{availableTeamMembers.map(member => <option key={member.id} value={member.user_id ?? ''}>{member.full_name} — {member.email}</option>)}</select></label><button className={primaryButton} disabled={addMember.isPending || !memberId}><UserPlus className="h-4 w-4" />Add member</button></form>{!teamMembers.isLoading && availableTeamMembers.length === 0 && <p className="mt-3 text-xs text-muted-foreground">Every eligible Team member already has Project access.</p>}</SectionCard>}
      {members.isLoading ? <LoadingState label="Loading project members..." /> : members.data?.length ? <SectionCard title="Project members / access" description={`${members.data.length} ${members.data.length === 1 ? 'person has' : 'people have'} access`} icon={Users} contentClassName="p-0"><div className="divide-y divide-border/70">{members.data.map(member => <div key={member.id} className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"><div className="flex min-w-0 items-center gap-3"><Avatar name={member.full_name} /><div className="min-w-0"><p className="truncate text-sm font-medium">{member.full_name}</p><p className="truncate text-xs text-muted-foreground">{member.title || member.department || 'Project member'} · {member.email}</p></div></div>{canManage && member.user_id !== data.created_by && <button className="text-xs font-semibold text-rose-600 hover:underline" onClick={() => removeMember.mutate(member.user_id)}>Remove</button>}</div>)}</div></SectionCard> : <EmptyState icon={Users} title="No project members" description="Assign Team members to give them access to this Project." />}
    </div>}

    {tab === 'meetings' && (meetings.isLoading ? <LoadingState label="Loading meetings..." /> : meetings.data?.length ? <SectionCard title="Project meetings" description={`${meetings.data.length} meeting${meetings.data.length === 1 ? '' : 's'} in this project`} contentClassName="p-0"><div className="divide-y divide-border/70">{meetings.data.map(meeting => <Link key={meeting.id} to={`/meetings/${meeting.id}`} className="flex items-center justify-between gap-4 px-4 py-3.5 transition-colors hover:bg-muted/40 sm:px-5"><div className="min-w-0"><span className="block truncate text-sm font-medium">{meeting.title}</span><span className="mt-0.5 block text-xs text-muted-foreground">{formatDate(meeting.meeting_date)}</span></div><StatusBadge status={meeting.status} size="sm" /></Link>)}</div></SectionCard> : <EmptyState title="No project meetings" description="Meetings assigned to this project will appear here." />)}

    {tab === 'tasks' && (tasks.isLoading ? <LoadingState label="Loading tasks..." /> : tasks.data?.tasks.length ? <SectionCard title="Project tasks" description="Follow-up work generated from project meetings" contentClassName="p-0"><div className="divide-y divide-border/70">{tasks.data.tasks.map(task => { const canUpdate = canManage || task.assigned_user_id === user?.id; return <div key={task.id} className="flex flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-5"><div className="min-w-0"><p className="truncate text-sm font-medium">{task.title}</p><p className="mt-0.5 truncate text-xs text-muted-foreground">{task.meeting_title}</p></div><div className="flex items-center gap-2"><PriorityBadge priority={task.priority} /><select aria-label={`Update ${task.title} status`} className="rounded-lg border border-input bg-background px-2.5 py-1.5 text-xs font-semibold" value={task.status} disabled={!canUpdate} onChange={event => updateTask.mutate({ id: task.id, status: event.target.value as TaskStatus })}>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(status => <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>)}</select></div></div>; })}</div></SectionCard> : <EmptyState title="No project tasks" description="Tasks generated from project meetings will appear here." />)}

    {tab === 'context' && <SectionCard title="Project context" description="This context is included only in authorized meeting processing." icon={ShieldCheck}>{canManage ? <><textarea className={fieldClass} rows={12} value={context} onChange={event => setContext(event.target.value)} /><div className="mt-4 flex justify-end"><button className={primaryButton} onClick={() => update.mutate({ context })} disabled={update.isPending}>{update.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Save context</button></div></> : <p className="whitespace-pre-wrap text-sm leading-7">{context || 'No project context has been added.'}</p>}</SectionCard>}

    <ConfirmDialog isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} onConfirm={() => removeProject.mutate()} title="Delete project?" description={`Delete "${data.name}"? Existing meetings and tasks will be retained without this project.`} confirmLabel="Delete project" isDestructive isLoading={removeProject.isPending} />
  </div>;
}

export function MembersPage() {
  const { activeTeam, activeRole } = useTeam();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ full_name: '', email: '', title: '', department: '', role: 'member' as TeamRole });
  const members = useQuery({ queryKey: ['team-members', activeTeam?.id], queryFn: () => teamsApi.listMembers(activeTeam!.id), enabled: Boolean(activeTeam) });
  const add = useMutation({ mutationFn: () => teamsApi.addMember(activeTeam!.id, { full_name: form.full_name, email: form.email, title: form.title || null, department: form.department || null, role: form.role }), onSuccess: member => { setForm({ full_name: '', email: '', title: '', department: '', role: 'member' }); queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }); toast.success(member.status === 'pending' ? 'Invitation created' : 'Team member added'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const updateRole = useMutation({ mutationFn: ({ id, nextRole }: { id: number; nextRole: TeamRole }) => teamsApi.updateMemberRole(activeTeam!.id, id, nextRole), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }), onError: error => toast.error(formatErrorMessage(error)) });
  const remove = useMutation({ mutationFn: (id: number) => teamsApi.removeMember(activeTeam!.id, id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }); queryClient.invalidateQueries({ queryKey: ['projects', activeTeam?.id] }); toast.success('Team member removed'); }, onError: error => toast.error(formatErrorMessage(error)) });
  const revoke = useMutation({ mutationFn: (id: string) => teamsApi.revokeInvitation(activeTeam!.id, id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['team-members', activeTeam?.id] }); toast.success('Invitation revoked'); }, onError: error => toast.error(formatErrorMessage(error)) });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to manage members." />;
  if (members.isLoading) return <LoadingState label="Loading team members..." />;
  if (members.isError) return <ErrorState message={formatErrorMessage(members.error)} onRetry={() => members.refetch()} />;
  return <div className="space-y-6">
    <PageHeader title="Team members" description={`Manage access to ${activeTeam.name}. Project access is assigned separately.`} icon={Users} />
    <SectionCard title="Add or invite a member" description="Existing accounts join immediately. New email addresses remain pending until that person registers." icon={UserPlus}><form className="grid gap-4 sm:grid-cols-2" onSubmit={(event: FormEvent) => { event.preventDefault(); add.mutate(); }}><label className="text-sm font-medium">Name<input className={`mt-1.5 ${fieldClass}`} value={form.full_name} onChange={event => setForm({ ...form, full_name: event.target.value })} placeholder="Ali Khan" required /></label><label className="text-sm font-medium">Work email<input className={`mt-1.5 ${fieldClass}`} type="email" value={form.email} onChange={event => setForm({ ...form, email: event.target.value })} placeholder="ali@example.com" required /></label><label className="text-sm font-medium">Title <span className="font-normal text-muted-foreground">(optional)</span><input className={`mt-1.5 ${fieldClass}`} value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} placeholder="Backend Developer" /></label><label className="text-sm font-medium">Department <span className="font-normal text-muted-foreground">(optional)</span><input className={`mt-1.5 ${fieldClass}`} value={form.department} onChange={event => setForm({ ...form, department: event.target.value })} placeholder="Engineering" /></label><label className="text-sm font-medium">Workspace role<select className={`mt-1.5 ${fieldClass}`} value={form.role} onChange={event => setForm({ ...form, role: event.target.value as TeamRole })}><option value="member">Member</option>{activeRole === 'owner' && <option value="admin">Admin</option>}</select></label><div className="flex items-end justify-end"><button className={primaryButton} disabled={add.isPending}><UserPlus className="h-4 w-4" />Add / invite member</button></div></form></SectionCard>
    <SectionCard title="Members" description={`${members.data?.length ?? 0} joined or invited people`} icon={Users} contentClassName="p-0"><div className="divide-y divide-border/70">{members.data?.map(member => <div key={member.id} className="flex flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between sm:px-5"><div className="flex min-w-0 items-center gap-3"><Avatar name={member.full_name} /><span className="min-w-0"><span className="flex items-center gap-2"><span className="truncate text-sm font-medium">{member.full_name}</span><span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${member.status === 'pending' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>{member.status === 'pending' ? 'Invitation pending' : 'Active'}</span></span><span className="block truncate text-xs text-muted-foreground">{member.title || member.department || 'Team member'} · {member.email}</span></span></div><div className="flex items-center gap-3 pl-12 sm:pl-0">{member.user_id && activeRole === 'owner' && member.role !== 'owner' ? <select aria-label={`Role for ${member.full_name}`} className="rounded-lg border border-input bg-background px-2.5 py-1.5 text-xs font-semibold capitalize" value={member.role} onChange={event => updateRole.mutate({ id: member.user_id!, nextRole: event.target.value as TeamRole })}><option value="member">Member</option><option value="admin">Admin</option></select> : <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-[11px] font-semibold capitalize text-muted-foreground">{member.role}</span>}{member.status === 'pending' ? <button className="text-xs font-semibold text-rose-600 hover:underline" onClick={() => revoke.mutate(member.id)}>Revoke</button> : member.role !== 'owner' && member.user_id ? <button className="text-xs font-semibold text-rose-600 hover:underline" onClick={() => remove.mutate(member.user_id!)}>Remove</button> : null}</div></div>)}</div></SectionCard>
  </div>;
}

export function TeamSettingsPage() {
  const { activeTeam, refreshTeams } = useTeam();
  const [form, setForm] = useState({ name: '', description: '' });
  useEffect(() => { if (activeTeam) setForm({ name: activeTeam.name, description: activeTeam.description ?? '' }); }, [activeTeam]);
  const save = useMutation({ mutationFn: () => teamsApi.updateTeam(activeTeam!.id, { name: form.name, description: form.description || null }), onSuccess: async () => { await refreshTeams(); toast.success('Team settings saved'); }, onError: error => toast.error(formatErrorMessage(error)) });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to open its settings." />;
  return <div className="space-y-6"><PageHeader title="Team settings" description="Workspace identity and shared details. Personal account settings remain separate." icon={ShieldCheck} /><SectionCard title="Workspace details" description="Shown to everyone with access to this team." className="max-w-3xl"><form className="space-y-5" onSubmit={(event: FormEvent) => { event.preventDefault(); save.mutate(); }}><label className="block text-sm font-medium">Team name<input className={`mt-1.5 ${fieldClass}`} value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} required /></label><label className="block text-sm font-medium">Description<textarea className={`mt-1.5 ${fieldClass}`} rows={5} value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} placeholder="What does this team work on?" /></label><div className="flex justify-end border-t border-border pt-4"><button className={primaryButton} disabled={save.isPending}>{save.isPending && <Loader2 className="h-4 w-4 animate-spin" />}Save settings</button></div></form></SectionCard></div>;
}

function Meta({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">{label}</dt><dd className="mt-1.5 text-sm font-medium text-foreground">{value}</dd></div>;
}
