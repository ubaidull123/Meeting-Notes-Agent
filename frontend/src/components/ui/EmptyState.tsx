import React from 'react';
import { LucideIcon, FolderOpen } from 'lucide-react';
import { cn } from '../../utils/cn';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = FolderOpen,
  title,
  description,
  action,
  className,
}) => {
  const ActionIcon = action?.icon;

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-border bg-card/50',
        className
      )}
    >
      <div className="p-3.5 rounded-full bg-muted text-muted-foreground mb-4">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-1.5 text-sm text-muted-foreground max-w-sm">{description}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 active:bg-teal-800 rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500/20"
        >
          {ActionIcon && <ActionIcon className="w-4 h-4" />}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
};
