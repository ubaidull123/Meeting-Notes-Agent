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
        'flex min-h-48 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/60 px-5 py-8 text-center',
        className
      )}
    >
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground shadow-sm">
        <Icon className="h-5 w-5" />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm leading-6 text-muted-foreground">{description}</p>
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-5 inline-flex min-h-9 items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
        >
          {ActionIcon && <ActionIcon className="w-4 h-4" />}
          <span>{action.label}</span>
        </button>
      )}
    </div>
  );
};
