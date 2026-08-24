import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { tasksApi } from '../api/tasks';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { LoadingState } from '../components/ui/LoadingState';
import { PriorityBadge } from '../components/ui/PriorityBadge';
import { useAuth } from '../context/AuthContext';
import { useTeam } from '../context/TeamContext';
import { TaskStatus, TaskUpdateRequest } from '../types/task';
import { formatDate } from '../utils/date';
import { formatErrorMessage } from '../utils/errors';

export function TasksWorkspacePage() {
  const { user } = useAuth();
  const { activeTeam, canManageActiveTeam } = useTeam();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('');
  const tasks = useQuery({
    queryKey: ['tasks', activeTeam?.id, status],
    queryFn: () => tasksApi.listTasks({ team_id: activeTeam!.id, status: (status || undefined) as TaskStatus | undefined, page_size: 100 }),
    enabled: Boolean(activeTeam),
  });
  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdateRequest }) => tasksApi.updateTask(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }),
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const remove = useMutation({
    mutationFn: (id: string) => tasksApi.deleteTask(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['tasks', activeTeam?.id] }); toast.success('Task deleted'); },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  if (!activeTeam) return <EmptyState title="No active team" description="Select a team to view tasks." />;
  if (tasks.isLoading) return <LoadingState label="Loading tasks..." />;
  if (tasks.isError) return <ErrorState message={formatErrorMessage(tasks.error)} onRetry={() => tasks.refetch()} />;
  return <div className="space-y-6"><header><h1 className="text-2xl font-bold">{canManageActiveTeam ? 'Tasks' : 'My tasks'}</h1><p className="mt-1 text-sm text-muted-foreground">{canManageActiveTeam ? `Team and project tasks in ${activeTeam.name}.` : 'Your assigned tasks and visible project follow-up.'}</p></header><select className="w-full max-w-xs rounded-lg border border-input bg-background px-3 py-2 text-sm" value={status} onChange={event => setStatus(event.target.value)} aria-label="Filter tasks"><option value="">All statuses</option>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}</select>{tasks.data?.tasks.length ? <section className="overflow-x-auto rounded-xl border border-border bg-card"><table className="w-full text-left text-sm"><thead className="border-b border-border bg-muted/40 text-xs uppercase text-muted-foreground"><tr><th className="px-4 py-3">Task</th><th className="px-4 py-3">Meeting</th><th className="px-4 py-3">Priority</th><th className="px-4 py-3">Due</th><th className="px-4 py-3">Status</th>{canManageActiveTeam && <th className="px-4 py-3 text-right">Manage</th>}</tr></thead><tbody className="divide-y divide-border">{tasks.data.tasks.map(task => { const canUpdateStatus = canManageActiveTeam || task.assigned_user_id === user?.id; return <tr key={task.id}><td className="px-4 py-3 font-medium">{task.title}{task.assigned_user_id === user?.id && <span className="ml-2 rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800">Assigned to you</span>}</td><td className="px-4 py-3 text-muted-foreground">{task.meeting_title}</td><td className="px-4 py-3"><PriorityBadge priority={task.priority} /></td><td className="px-4 py-3 text-muted-foreground">{task.due_date ? formatDate(task.due_date) : '—'}</td><td className="px-4 py-3"><select className="rounded-lg border border-input bg-background px-2 py-1 text-sm" value={task.status} disabled={!canUpdateStatus} onChange={event => update.mutate({ id: task.id, data: { status: event.target.value as TaskStatus } })}>{['todo', 'in_progress', 'in_review', 'done', 'blocked'].map(value => <option key={value} value={value}>{value.replace(/_/g, ' ')}</option>)}</select></td>{canManageActiveTeam && <td className="px-4 py-3 text-right"><button className="mr-3 text-sm font-semibold text-teal-700" onClick={() => { const value = window.prompt('Assign to team/project member user ID. Leave blank to unassign.', task.assigned_user_id?.toString() ?? ''); if (value !== null) update.mutate({ id: task.id, data: { assigned_user_id: value.trim() ? Number(value) : null } }); }}>Assign</button><button className="text-sm font-semibold text-rose-600" onClick={() => remove.mutate(task.id)}>Delete</button></td>}</tr>; })}</tbody></table></section> : <EmptyState title="No tasks found" description="Tasks generated from authorized meetings will appear here." />}</div>;
}
