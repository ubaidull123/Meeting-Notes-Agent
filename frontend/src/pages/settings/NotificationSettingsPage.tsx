import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Info } from 'lucide-react';
import { toast } from 'sonner';
import { SettingsSaveButton, SettingsSection, SettingsToggle } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useNotificationSettings, useUpdateNotificationSettings } from '../../hooks/useSettings';
import { NotificationSettings } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

export function NotificationSettingsPage() {
  const query = useNotificationSettings();
  const update = useUpdateNotificationSettings();
  const [draft, setDraft] = useState<NotificationSettings | null>(null);

  useEffect(() => { if (query.data) setDraft(query.data); }, [query.data]);
  const isDirty = useMemo(() => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)), [draft, query.data]);

  if (query.isError) return <ErrorState message={formatErrorMessage(query.error)} onRetry={() => query.refetch()} />;
  if (query.isLoading || !draft) return <LoadingState />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, {
      onSuccess: (saved) => { setDraft(saved); toast.success('Notification preferences saved'); },
      onError: (error) => toast.error(formatErrorMessage(error)),
    });
  };

  const toggle = (key: keyof NotificationSettings, label: string, description: string) => (
    <SettingsToggle checked={Boolean(draft[key])} onChange={(value) => setDraft({ ...draft, [key]: value })} label={label} description={description} />
  );

  return (
    <form onSubmit={submit}>
      <SettingsSection title="Processing alerts" description="Choose which workflow events should notify you when delivery is enabled.">
        <div className="divide-y divide-border">
          {toggle('processing_finished', 'Processing finishes', 'A meeting has completed processing.')}
          {toggle('processing_failed', 'Processing fails', 'A meeting needs attention after an error.')}
          {toggle('review_required', 'Review is required', 'Generated meeting results are awaiting human review.')}
          {toggle('email_approval_required', 'Email approval is required', 'A follow-up email is ready for approval.')}
          {toggle('credits_low', 'Credits are low', 'The application credit balance reaches a low threshold.')}
        </div>
      </SettingsSection>
      {!draft.delivery_available && (
        <div className="flex gap-3 rounded-md border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900 dark:border-sky-900 dark:bg-sky-950/30 dark:text-sky-200">
          <Info className="h-5 w-5 shrink-0" />
          <p>Preferences are saved now. Notification delivery is not connected in this phase, so no external messages are sent yet.</p>
        </div>
      )}
      <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} /></div>
    </form>
  );
}
