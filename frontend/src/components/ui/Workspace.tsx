import { ReactNode } from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

export const primaryButton = 'inline-flex min-h-9 items-center justify-center gap-2 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
export const secondaryButton = 'inline-flex min-h-9 items-center justify-center gap-2 rounded-lg border border-border bg-card px-3.5 py-2 text-sm font-semibold text-foreground shadow-sm transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
export const ghostButton = 'inline-flex min-h-9 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50';
export const dangerButton = 'inline-flex min-h-9 items-center justify-center gap-2 rounded-lg border border-rose-200 bg-card px-3.5 py-2 text-sm font-semibold text-rose-700 shadow-sm transition-colors hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/30 disabled:pointer-events-none disabled:opacity-50';
export const fieldClass = 'w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground shadow-sm outline-none transition placeholder:text-muted-foreground/70 hover:border-foreground/20 focus:border-primary focus:ring-2 focus:ring-ring/20 disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-70';

interface PageHeaderProps {
  title: string;
  description?: ReactNode;
  eyebrow?: ReactNode;
  icon?: LucideIcon;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, description, eyebrow, icon: Icon, actions, className }: PageHeaderProps) {
  return <header className={cn('flex flex-col gap-4 border-b border-border/80 pb-5 sm:flex-row sm:items-start sm:justify-between', className)}>
    <div className="min-w-0">
      {eyebrow && <div className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</div>}
      <div className="flex min-w-0 items-center gap-3">
        {Icon && <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-primary/15 bg-primary/10 text-primary"><Icon className="h-[18px] w-[18px]" /></span>}
        <h1 className="truncate text-2xl font-semibold tracking-tight text-foreground sm:text-[1.75rem]">{title}</h1>
      </div>
      {description && <div className={cn('text-sm leading-6 text-muted-foreground', Icon ? 'mt-2 sm:ml-12' : 'mt-1.5')}>{description}</div>}
    </div>
    {actions && <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">{actions}</div>}
  </header>;
}

interface SectionCardProps {
  children: ReactNode;
  title?: ReactNode;
  description?: ReactNode;
  icon?: LucideIcon;
  action?: ReactNode;
  className?: string;
  contentClassName?: string;
}

export function SectionCard({ children, title, description, icon: Icon, action, className, contentClassName }: SectionCardProps) {
  const hasHeader = title || description || Icon || action;
  return <section className={cn('overflow-hidden rounded-xl border border-border/80 bg-card shadow-[0_1px_2px_rgba(15,23,42,0.04)]', className)}>
    {hasHeader && <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border/70 px-4 py-3.5 sm:px-5">
      <div className="flex min-w-0 items-start gap-2.5">
        {Icon && <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground"><Icon className="h-4 w-4" /></span>}
        <div className="min-w-0">
          {title && <h2 className="text-sm font-semibold text-foreground">{title}</h2>}
          {description && <p className="mt-0.5 text-xs leading-5 text-muted-foreground">{description}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>}
    <div className={cn('p-4 sm:p-5', contentClassName)}>{children}</div>
  </section>;
}

interface WorkspaceTabsProps<T extends string> {
  items: Array<{ id: T; label: string; count?: number }>;
  active: T;
  onChange: (id: T) => void;
  label: string;
}

export function WorkspaceTabs<T extends string>({ items, active, onChange, label }: WorkspaceTabsProps<T>) {
  return <div className="overflow-x-auto border-b border-border" role="tablist" aria-label={label}>
    <div className="flex min-w-max gap-1">
      {items.map(item => <button
        key={item.id}
        type="button"
        role="tab"
        aria-selected={active === item.id}
        onClick={() => onChange(item.id)}
        className={cn(
          'relative flex items-center gap-2 px-3 py-3 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground sm:px-4',
          active === item.id && 'text-foreground after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:rounded-full after:bg-primary sm:after:inset-x-4',
        )}
      >
        {item.label}
        {typeof item.count === 'number' && <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-muted-foreground">{item.count}</span>}
      </button>)}
    </div>
  </div>;
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name.trim().split(/\s+/).slice(0, 2).map(part => part.charAt(0)).join('').toUpperCase() || 'U';
  return <span className={cn('inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-primary/15 bg-primary/10 text-xs font-semibold text-primary', className)}>{initials}</span>;
}
