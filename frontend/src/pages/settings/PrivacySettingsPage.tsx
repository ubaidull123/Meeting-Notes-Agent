import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Info, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { SettingsSaveButton, SettingsSection, SettingsToggle, settingsFieldClass } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { usePrivacySettings, useUpdatePrivacySettings } from '../../hooks/useSettings';
import { PrivacySettings } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

export function PrivacySettingsPage() {
  const query = usePrivacySettings();
  const update = useUpdatePrivacySettings();
  const [draft, setDraft] = useState<PrivacySettings | null>(null);
  useEffect(() => { if (query.data) setDraft(query.data); }, [query.data]);
  const isDirty = useMemo(() => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)), [draft, query.data]);

  if (query.isError) return <ErrorState message={formatErrorMessage(query.error)} onRetry={() => query.refetch()} />;
  if (query.isLoading || !draft) return <LoadingState />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, {
      onSuccess: (saved) => { setDraft(saved); toast.success('Privacy preferences saved'); },
      onError: (error) => toast.error(formatErrorMessage(error)),
    });
  };

  return (
    <form onSubmit={submit}>
      <SettingsSection title="Recording retention" description="Set your preferred lifecycle for uploaded meeting recordings.">
        <label className="text-sm font-medium">Delete uploaded recording after
          <select className={settingsFieldClass} value={draft.recording_retention} onChange={(event) => setDraft({ ...draft, recording_retention: event.target.value as PrivacySettings['recording_retention'] })}>
            <option value="never">Never</option><option value="24_hours">24 hours</option><option value="7_days">7 days</option><option value="30_days">30 days</option>
          </select>
        </label>
        <div className="mt-4"><SettingsToggle checked={draft.keep_transcript} onChange={(value) => setDraft({ ...draft, keep_transcript: value })} label="Keep transcript" description="Retain transcript text after recording cleanup." /></div>
      </SettingsSection>
      {!draft.automatic_cleanup_available && (
        <div className="flex gap-3 rounded-md border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900 dark:border-sky-900 dark:bg-sky-950/30 dark:text-sky-200">
          <Info className="h-5 w-5 shrink-0" /><p>Your retention preference is stored, but scheduled file cleanup is not active in this phase.</p>
        </div>
      )}
      <SettingsSection title="Data controls" description="Delete individual meetings from the meeting workspace.">
        <Link to="/meetings" className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted"><Trash2 className="h-4 w-4" />Manage meeting data</Link>
        <p className="mt-3 text-sm text-muted-foreground">Account deletion is not available until a recoverable production deletion workflow is in place.</p>
      </SettingsSection>
      <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} /></div>
    </form>
  );
}
