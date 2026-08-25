import { FormEvent, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, ListFilter, ListTodo, Trash2, UserRound, X } from 'lucide-react';
import { toast } from 'sonner';
import { tasksApi } from '../api/tasks';
import { projectsApi, teamsApi } from '../api/teams';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { PriorityBadge } from '../components/ui/PriorityBadge';
import { dangerButton, fieldClass, PageHeader, primaryButton, secondaryButton, SectionCard } from '../components/ui/Workspace';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { Task, TaskStatus, TaskUpdateRequest } from '../types/task';
import { MemberOption } from '../types/team';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

const statuses: Array<{ value: TaskStatus | ''; label: string }> = [
  { value: '', label: 'All' }, { value: 'todo', label: 'To do' }, { value: 'in_progress', label: 'In progress' }, { value: 'in_review', label: 'In review' }, { value: 'blocked', label: 'Blocked' }, { value: 'done', label: 'Done' },
];

export function TasksWorkspacePage() {
  const { user } = useAuth();
  const { activeTeam, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<TaskStatus | ''>('');
  const [assigningTask, setAssigningTask] = useState<Task | null>(null);
  const tasks = useQuery({ queryKey: ['tasks', activeTeam?.id, status], queryFn: () => tasksApi.listTasks({ team_id: activeTeam!.id, status: status || undefined, page_size: 100 }), enabled: Boolean(activeTeam) });
  const update = useMutation({ mutationFn: ({ id, data }: { id: string; data: TaskUpdateRequest }) => tasksApi.updateTask(id, data), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }), onError: error => toast.error(formatErrorMessage(error)) });
  const remove = useMutation({ mutationFn: (id: string) => tasksApi.deleteTask(id), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }); toast.success('Task deleted'); }, onError: error => toast.error(formatErrorMessage(error)) });

  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to view tasks." />;
  if (tasks.isLoading) return <LoadingState label="Loading tasks..." />;
  if (tasks.isError) return <ErrorState message={formatErrorMessage(tasks.error)} onRetry={() => tasks.refetch()} />;
  const items = tasks.data?.tasks ?? [];

  const updateStatus = (task: Task, nextStatus: TaskStatus) => {
    if (!canManageActiveTeam && task.assigned_user_id !== user?.id) return;
    update.mutate({ id: task.id, data: { status: nextStatus } });
  };

  return <div className="space-y-6">
    <PageHeader title={canManageActiveTeam ? 'Tasks' : 'My tasks'} description={canManageActiveTeam ? `Team and project follow-up in ${activeTeam.name}.` : 'Your assigned work and visible project follow-up.'} icon={ListTodo} />
    <div className="flex items-center gap-2 overflow-x-auto pb-1" aria-label="Filter tasks by status">
      <span className="mr-1 flex items-center gap-1.5 text-xs font-semibold text-muted-foreground"><ListFilter className="h-3.5 w-3.5" />Filter</span>
      {statuses.map(item => <button key={item.value || 'all'} type="button" onClick={() => setStatus(item.value)} className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${status === item.value ? 'border-primary/25 bg-primary/10 text-primary' : 'border-border bg-card text-muted-foreground hover:bg-muted hover:text-foreground'}`}>{item.label}</button>)}
    </div>

    {items.length ? <>
      <div className="grid gap-3 md:hidden">{items.map(task => <TaskMobileCard key={task.id} task={task} isMine={task.assigned_user_id === user?.id} canManage={canManageActiveTeam} canUpdate={canManageActiveTeam || task.assigned_user_id === user?.id} onStatusChange={next => updateStatus(task, next)} onAssign={() => setAssigningTask(task)} onDelete={() => remove.mutate(task.id)} />)}</div>
      <SectionCard className="hidden md:block" contentClassName="p-0">
        <div className="overflow-x-auto"><table className="w-full min-w-[820px] text-left text-sm">
          <thead className="border-b border-border bg-muted/45 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground"><tr><th className="px-5 py-3">Task</th><th className="px-4 py-3">Meeting</th><th className="px-4 py-3">Priority</th><th className="px-4 py-3">Due date</th><th className="px-4 py-3">Status</th>{canManageActiveTeam && <th className="px-5 py-3 text-right">Actions</th>}</tr></thead>
          <tbody className="divide-y divide-border/70">{items.map(task => { const canUpdate = canManageActiveTeam || task.assigned_user_id === user?.id; return <tr key={task.id} className="transition-colors hover:bg-muted/30"><td className="px-5 py-4"><div className="max-w-sm"><p className={`font-medium ${task.status === 'done' ? 'text-muted-foreground line-through' : ''}`}>{task.title}</p><div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">{task.assignee ? <span className="inline-flex items-center gap-1"><UserRound className="h-3.5 w-3.5" />{task.assignee}</span> : <span>Unassigned</span>}{task.assigned_user_id === user?.id && <span className="rounded-full bg-primary/10 px-2 py-0.5 font-semibold text-primary">Assigned to you</span>}</div></div></td><td className="max-w-[180px] px-4 py-4 text-xs text-muted-foreground"><span className="block truncate">{task.meeting_title}</span></td><td className="px-4 py-4"><PriorityBadge priority={task.priority} /></td><td className="px-4 py-4"><DueDate value={task.due_date} done={task.status === 'done'} /></td><td className="px-4 py-4"><select aria-label={`Update ${task.title} status`} className="rounded-lg border border-input bg-background px-2.5 py-1.5 text-xs font-semibold" value={task.status} disabled={!canUpdate} onChange={event => updateStatus(task, event.target.value as TaskStatus)}>{statuses.filter(item => item.value).map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></td>{canManageActiveTeam && <td className="px-5 py-4"><div className="flex justify-end gap-2"><button className="text-xs font-semibold text-primary hover:underline" onClick={() => setAssigningTask(task)}>Assign</button><button className="text-xs font-semibold text-rose-600 hover:underline" onClick={() => remove.mutate(task.id)}>Delete</button></div></td>}</tr>; })}</tbody>
        </table></div>
      </SectionCard>
    </> : <EmptyState icon={ListTodo} title="No tasks found" description={status ? 'No tasks match this status. Try another filter.' : 'Tasks generated from authorized meetings will appear here.'} />}

    {assigningTask && <AssignTaskDialog task={assigningTask} isSaving={update.isPending} onClose={() => setAssigningTask(null)} onAssign={assignedUserId => update.mutate({ id: assigningTask.id, data: { assigned_user_id: assignedUserId } }, { onSuccess: () => { setAssigningTask(null); toast.success(assignedUserId ? 'Task assigned' : 'Task unassigned'); } })} />}
  </div>;
}

function TaskMobileCard({ task, isMine, canManage, canUpdate, onStatusChange, onAssign, onDelete }: { task: Task; isMine: boolean; canManage: boolean; canUpdate: boolean; onStatusChange: (status: TaskStatus) => void; onAssign: () => void; onDelete: () => void }) {
  return <article className="rounded-xl border border-border/80 bg-card p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"><div className="flex items-start justify-between gap-3"><div><h2 className={`text-sm font-semibold ${task.status === 'done' ? 'text-muted-foreground line-through' : ''}`}>{task.title}</h2><p className="mt-1 text-xs text-muted-foreground">{task.meeting_title}</p></div><PriorityBadge priority={task.priority} /></div><div className="mt-4 grid grid-cols-2 gap-3 border-t border-border/70 pt-3 text-xs"><div><span className="block text-muted-foreground">Assignee</span><span className="mt-1 block truncate font-medium">{task.assignee || 'Unassigned'}{isMine ? ' · You' : ''}</span></div><div><span className="block text-muted-foreground">Due date</span><span className="mt-1 block"><DueDate value={task.due_date} done={task.status === 'done'} /></span></div></div><div className="mt-4 flex items-center justify-between gap-3"><select aria-label={`Update ${task.title} status`} className="min-w-0 flex-1 rounded-lg border border-input bg-background px-2.5 py-2 text-xs font-semibold" value={task.status} disabled={!canUpdate} onChange={event => onStatusChange(event.target.value as TaskStatus)}>{statuses.filter(item => item.value).map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select>{canManage && <div className="flex gap-1"><button className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground" onClick={onAssign} aria-label={`Assign ${task.title}`}><UserRound className="h-4 w-4" /></button><button className="rounded-lg p-2 text-muted-foreground hover:bg-rose-50 hover:text-rose-600" onClick={onDelete} aria-label={`Delete ${task.title}`}><Trash2 className="h-4 w-4" /></button></div>}</div></article>;
}

function DueDate({ value, done }: { value?: string | null; done: boolean }) {
  if (!value) return <span className="text-muted-foreground">No due date</span>;
  const overdue = !done && new Date(value) < new Date();
  return <span className={`inline-flex items-center gap-1 whitespace-nowrap text-xs ${overdue ? 'font-semibold text-rose-600' : 'text-muted-foreground'}`}><CalendarDays className="h-3.5 w-3.5" />{formatDate(value)}{overdue ? ' · Overdue' : ''}</span>;
}

function AssignTaskDialog({ task, isSaving, onClose, onAssign }: { task: Task; isSaving: boolean; onClose: () => void; onAssign: (userId: number | null) => void }) {
  const [userId, setUserId] = useState(task.assigned_user_id?.toString() ?? '');
  const members = useQuery<MemberOption[]>({ queryKey: ['task-assignee-options', task.team_id, task.project_id || 'team'], queryFn: async () => task.project_id ? await projectsApi.listMembers(task.project_id) : await teamsApi.listMembers(task.team_id) });
  const submit = (event: FormEvent) => { event.preventDefault(); onAssign(userId.trim() ? Number(userId) : null); };
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-[2px]" role="dialog" aria-modal="true" aria-labelledby="assign-task-title" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><form onSubmit={submit} className="w-full max-w-md overflow-hidden rounded-xl border border-border bg-card shadow-2xl"><div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4"><div><h2 id="assign-task-title" className="text-base font-semibold">Assign task</h2><p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{task.title}</p></div><button type="button" onClick={onClose} className="rounded-lg p-2 text-muted-foreground hover:bg-muted" aria-label="Close"><X className="h-4 w-4" /></button></div><div className="p-5"><label className="text-sm font-medium">Project member<select autoFocus className={`mt-1.5 ${fieldClass}`} value={userId} onChange={event => setUserId(event.target.value)}><option value="">Unassigned</option>{members.data?.filter(member => member.status === 'active' && member.user_id).map(member => <option key={member.id} value={member.user_id ?? ''}>{member.full_name} — {member.title || member.email}</option>)}</select></label><p className="mt-2 text-xs leading-5 text-muted-foreground">Only eligible {task.project_id ? 'Project' : 'Team'} members can be assigned.</p></div><div className="flex justify-end gap-2 border-t border-border bg-muted/30 px-5 py-3"><button type="button" className={secondaryButton} onClick={onClose}>Cancel</button>{task.assigned_user_id && <button type="button" className={dangerButton} onClick={() => onAssign(null)} disabled={isSaving}>Unassign</button>}<button className={primaryButton} disabled={isSaving || members.isLoading}>Save assignment</button></div></form></div>;
}
