import React from 'react';
import { Task, TaskStatus } from '../../types/task';
import { PriorityBadge } from '../ui/PriorityBadge';
import { StatusBadge } from '../ui/StatusBadge';
import { formatDate } from '../../utils/date';
import { Calendar, User, CheckCircle2 } from 'lucide-react';
import { cn } from '../../utils/cn';

interface TaskCardProps {
  task: Task;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
  onClick?: () => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onStatusChange, onClick }) => {
  const isDone = task.status === 'done';

  const handleToggleDone = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onStatusChange) {
      onStatusChange(task.id, isDone ? 'todo' : 'done');
    }
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'group p-4 rounded-xl border bg-card text-card-foreground shadow-xs transition-all',
        onClick && 'cursor-pointer hover:border-teal-500/40 hover:shadow-sm',
        isDone && 'opacity-70 bg-muted/20'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <button
            type="button"
            onClick={handleToggleDone}
            className="mt-0.5 text-muted-foreground hover:text-teal-600 transition-colors shrink-0"
            title={isDone ? 'Mark as todo' : 'Mark as done'}
          >
            {isDone ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 fill-emerald-50 dark:fill-emerald-950/50" />
            ) : (
              <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/50 hover:border-teal-500 transition-colors" />
            )}
          </button>
          <div className="min-w-0">
            <h4
              className={cn(
                'text-sm font-medium text-foreground truncate',
                isDone && 'line-through text-muted-foreground'
              )}
            >
              {task.title}
            </h4>
            {task.description && (
              <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5 leading-relaxed">
                {task.description}
              </p>
            )}
          </div>
        </div>
        <PriorityBadge priority={task.priority} />
      </div>

      <div className="mt-4 pt-3 border-t border-border/50 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-3 flex-wrap">
          {task.assignee && (
            <span className="inline-flex items-center gap-1">
              <User className="w-3.5 h-3.5" />
              <span>{task.assignee}</span>
            </span>
          )}
          {task.due_date && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>{formatDate(task.due_date)}</span>
            </span>
          )}
        </div>

        <StatusBadge status={task.status} size="sm" />
      </div>
    </div>
  );
};
