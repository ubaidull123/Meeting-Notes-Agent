import React from 'react';
import { Task, TaskStatus } from '../../types/task';
import { PriorityBadge } from '../ui/PriorityBadge';
import { formatDate } from '../../utils/date';
import { Trash2, Edit3, Calendar, User } from 'lucide-react';
import { cn } from '../../utils/cn';

interface TaskTableProps {
  tasks: Task[];
  onSelectTask: (task: Task) => void;
  onDeleteTask: (task: Task) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  canManageActions?: boolean;
  canChangeStatus?: (task: Task) => boolean;
}

export const TaskTable: React.FC<TaskTableProps> = ({
  tasks,
  onSelectTask,
  onDeleteTask,
  onStatusChange,
  canManageActions = true,
  canChangeStatus = () => true,
}) => {
  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-card">
      <table className="w-full text-left text-sm">
        <thead className="bg-muted/50 border-b border-border text-xs text-muted-foreground uppercase font-medium">
          <tr>
            <th className="py-3 px-4">Task</th>
            <th className="py-3 px-4">Meeting</th>
            <th className="py-3 px-4">Assignee</th>
            <th className="py-3 px-4">Priority</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4">Due Date</th>
            {canManageActions && <th className="py-3 px-4 text-right">Actions</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {tasks.map((task) => (
            <tr
              key={task.id}
              onClick={() => onSelectTask(task)}
              className="hover:bg-muted/30 transition-colors cursor-pointer group"
            >
              <td className="py-3.5 px-4 font-medium text-foreground max-w-xs truncate">
                <span className={cn(task.status === 'done' && 'line-through text-muted-foreground')}>
                  {task.title}
                </span>
              </td>
              <td className="py-3.5 px-4 text-xs text-muted-foreground max-w-[160px] truncate">
                {task.meeting_title}
              </td>
              <td className="py-3.5 px-4 text-xs text-muted-foreground">
                {task.assignee ? (
                  <span className="inline-flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-muted-foreground" />
                    <span>{task.assignee}</span>
                  </span>
                ) : (
                  <span className="text-muted-foreground/60">Unassigned</span>
                )}
              </td>
              <td className="py-3.5 px-4">
                <PriorityBadge priority={task.priority} />
              </td>
              <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                <select
                  value={task.status}
                  disabled={!canChangeStatus(task)}
                  onChange={(e) => onStatusChange(task.id, e.target.value as TaskStatus)}
                  className="text-xs bg-background border border-input rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-teal-500 font-medium"
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="in_review">In Review</option>
                  <option value="done">Done</option>
                  <option value="blocked">Blocked</option>
                </select>
              </td>
              <td className="py-3.5 px-4 text-xs text-muted-foreground whitespace-nowrap">
                {task.due_date ? (
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{formatDate(task.due_date)}</span>
                  </span>
                ) : (
                  <span className="text-muted-foreground/60">—</span>
                )}
              </td>
              {canManageActions && <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-1">
                  <button
                    type="button"
                    onClick={() => onSelectTask(task)}
                    className="p-1 text-muted-foreground hover:text-foreground rounded-md hover:bg-muted"
                    title="Edit task"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onDeleteTask(task)}
                    className="p-1 text-muted-foreground hover:text-rose-600 rounded-md hover:bg-muted"
                    title="Delete task"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
