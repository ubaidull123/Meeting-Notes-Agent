import React from 'react';
import { TaskPriority } from '../../types/task';
import { cn } from '../../utils/cn';

interface PriorityBadgeProps {
  priority: TaskPriority | string;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, className }) => {
  const getPriorityConfig = () => {
    switch (priority?.toLowerCase()) {
      case 'urgent':
        return {
          label: 'Urgent',
          color: 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300 border-red-200 dark:border-red-800',
          dot: 'bg-red-500',
        };
      case 'high':
        return {
          label: 'High',
          color: 'bg-orange-50 text-orange-700 dark:bg-orange-950/60 dark:text-orange-300 border-orange-200 dark:border-orange-800',
          dot: 'bg-orange-500',
        };
      case 'medium':
        return {
          label: 'Medium',
          color: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/60 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
          dot: 'bg-yellow-500',
        };
      case 'low':
      default:
        return {
          label: 'Low',
          color: 'bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
          dot: 'bg-slate-400',
        };
    }
  };

  const config = getPriorityConfig();

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium border rounded-md',
        config.color,
        className
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
      {config.label}
    </span>
  );
};
