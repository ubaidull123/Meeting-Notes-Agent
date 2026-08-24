import { Loader2 } from 'lucide-react';
import { ReactNode } from 'react';

export const settingsFieldClass =
  'mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30';

export function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="border-b border-border py-6 first:pt-0 last:border-0 last:pb-0">
      <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          {description && <p className="mt-1 text-sm leading-5 text-muted-foreground">{description}</p>}
        </div>
        <div>{children}</div>
      </div>
    </section>
  );
}

export function SettingsSaveButton({
  isSaving,
  isDirty,
  label = 'Save changes',
}: {
  isSaving: boolean;
  isDirty: boolean;
  label?: string;
}) {
  return (<>
    {isDirty && !isSaving && <span className="self-center text-sm text-amber-700 dark:text-amber-300">You have unsaved changes.</span>}
    <button
      type="submit"
      disabled={isSaving || !isDirty}
      className="inline-flex min-w-32 items-center justify-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
      {isSaving ? 'Saving...' : label}
    </button>
  </>);
}

export function SettingsToggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
}) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-4 py-2">
      <span>
        <span className="block text-sm font-medium">{label}</span>
        {description && <span className="mt-0.5 block text-sm text-muted-foreground">{description}</span>}
      </span>
      <input className="peer sr-only" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span className="relative mt-0.5 h-6 w-11 shrink-0 rounded-full bg-muted transition peer-checked:bg-teal-600 peer-focus-visible:ring-2 peer-focus-visible:ring-teal-500/40 after:absolute after:left-1 after:top-1 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
    </label>
  );
}
