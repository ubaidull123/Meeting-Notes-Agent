import { FormEvent, useEffect, useRef, useState } from 'react';
import { Building2, Check, ChevronsUpDown, Loader2, Plus, X } from 'lucide-react';
import { toast } from 'sonner';
import { useTeam } from '../../context/TeamContext';
import { formatErrorMessage } from '../../utils/errors';
import { cn } from '../../utils/cn';
import { fieldClass, primaryButton, secondaryButton } from '../ui/Workspace';

export function WorkspaceSwitcher({ collapsed }: { collapsed: boolean }) {
  const { activeTeam, teams, selectTeam, createTeam } = useTeam();
  const [isOpen, setIsOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setIsSaving(true);
    try {
      await createTeam({ name: name.trim(), description: description.trim() || null });
      toast.success(`${name.trim()} workspace created`);
      setName('');
      setDescription('');
      setIsCreating(false);
      setIsOpen(false);
    } catch (error) {
      toast.error(formatErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  };

  return <div ref={rootRef} className="relative">
    {!collapsed && <p className="mb-1.5 px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Current workspace</p>}
    <button
      type="button"
      aria-haspopup="menu"
      aria-expanded={isOpen}
      title={collapsed ? activeTeam?.name || 'Choose workspace' : undefined}
      onClick={() => setIsOpen(value => !value)}
      className={cn(
        'flex w-full items-center rounded-lg border border-border bg-background shadow-sm transition-colors hover:border-foreground/20 hover:bg-muted/30',
        collapsed ? 'h-10 justify-center px-2' : 'gap-2 px-2.5 py-2 text-left',
      )}
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary"><Building2 className="h-3.5 w-3.5" /></span>
      {!collapsed && <><span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold text-foreground">{activeTeam?.name || 'Choose workspace'}</span><span className="block text-[10px] capitalize text-muted-foreground">{activeTeam ? `${activeTeam.role} access` : 'No workspace selected'}</span></span><ChevronsUpDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" /></>}
    </button>

    {isOpen && <div role="menu" className={cn('absolute z-40 mt-2 w-64 overflow-hidden rounded-xl border border-border bg-popover p-1.5 shadow-xl', collapsed ? 'left-full bottom-0 ml-2' : 'left-0 top-full')}>
      <p className="px-2.5 pb-1.5 pt-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Switch workspace</p>
      <div className="max-h-64 overflow-y-auto">
        {teams.map(team => <button key={team.id} type="button" role="menuitem" onClick={() => { selectTeam(team.id); setIsOpen(false); }} className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left hover:bg-muted">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary">{team.name.charAt(0).toUpperCase()}</span>
          <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{team.name}</span><span className="block text-[10px] capitalize text-muted-foreground">{team.role}</span></span>
          {team.id === activeTeam?.id && <Check className="h-4 w-4 text-primary" />}
        </button>)}
      </div>
      <div className="my-1 border-t border-border" />
      <button type="button" role="menuitem" onClick={() => { setIsCreating(true); setIsOpen(false); }} className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm font-semibold text-primary hover:bg-primary/10"><Plus className="h-4 w-4" />Create workspace</button>
    </div>}

    {isCreating && <div className="fixed inset-0 z-[70] flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="create-workspace-title">
      <button type="button" className="fixed inset-0 bg-slate-950/50 backdrop-blur-[2px]" aria-label="Close create workspace dialog" onClick={() => !isSaving && setIsCreating(false)} />
      <form onSubmit={submit} className="relative z-10 w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl">
        <div className="flex items-start justify-between border-b border-border px-5 py-4"><div><h2 id="create-workspace-title" className="text-lg font-semibold">Create workspace</h2><p className="mt-1 text-sm text-muted-foreground">Start an independent Team with its own Projects, Meetings, and Members.</p></div><button type="button" disabled={isSaving} onClick={() => setIsCreating(false)} className="rounded-lg p-2 text-muted-foreground hover:bg-muted" aria-label="Close"><X className="h-4 w-4" /></button></div>
        <div className="space-y-4 p-5"><label className="block text-sm font-medium">Workspace name<input autoFocus required maxLength={255} className={`mt-1.5 ${fieldClass}`} value={name} onChange={event => setName(event.target.value)} placeholder="Meeting Notes Startup" /></label><label className="block text-sm font-medium">Description <span className="font-normal text-muted-foreground">(optional)</span><textarea rows={3} className={`mt-1.5 ${fieldClass}`} value={description} onChange={event => setDescription(event.target.value)} placeholder="What this workspace is for" /></label></div>
        <div className="flex justify-end gap-2 border-t border-border px-5 py-4"><button type="button" disabled={isSaving} className={secondaryButton} onClick={() => setIsCreating(false)}>Cancel</button><button type="submit" disabled={isSaving || !name.trim()} className={primaryButton}>{isSaving && <Loader2 className="h-4 w-4 animate-spin" />}{isSaving ? 'Creating...' : 'Create workspace'}</button></div>
      </form>
    </div>}
  </div>;
}
