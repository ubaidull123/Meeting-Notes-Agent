import { FormEvent, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import {
  SettingsSaveButton,
  SettingsSection,
  settingsFieldClass,
} from '../../components/settings/SettingsControls';
import { useAuth } from '../../context/AuthContext';
import { useProfileSettings, useUpdateProfileSettings } from '../../hooks/useSettings';
import { ProfileSettings } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

const timezones = ['UTC', 'Asia/Karachi', 'Asia/Dubai', 'Europe/London', 'America/New_York'];

export function ProfileSettingsPage() {
  const query = useProfileSettings();
  const update = useUpdateProfileSettings();
  const { refreshProfile } = useAuth();
  const [draft, setDraft] = useState<ProfileSettings | null>(null);

  useEffect(() => {
    if (query.data) setDraft(query.data);
  }, [query.data]);

  const isDirty = useMemo(
    () => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)),
    [draft, query.data],
  );

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!isDirty) return;
      event.preventDefault();
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [isDirty]);

  if (query.isError) {
    return <ErrorState message={formatErrorMessage(query.error)} onRetry={() => query.refetch()} />;
  }
  if (query.isLoading || !draft) return <LoadingState />;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, {
      onSuccess: async (saved) => {
        setDraft(saved);
        await refreshProfile();
        toast.success('Profile settings saved');
      },
      onError: (error) => toast.error(formatErrorMessage(error)),
    });
  };

  return (
    <form onSubmit={submit}>
      <SettingsSection title="Personal details" description="Your account identity and workplace context.">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium sm:col-span-2">
            Display name
            <input className={settingsFieldClass} value={draft.display_name} onChange={(event) => setDraft({ ...draft, display_name: event.target.value })} required />
          </label>
          <label className="text-sm font-medium sm:col-span-2">
            Email
            <input className={settingsFieldClass} value={draft.email} readOnly aria-readonly="true" />
          </label>
          <label className="text-sm font-medium">
            Organization
            <input className={settingsFieldClass} value={draft.organization ?? ''} onChange={(event) => setDraft({ ...draft, organization: event.target.value || null })} />
          </label>
          <label className="text-sm font-medium">
            Job title
            <input className={settingsFieldClass} value={draft.job_title ?? ''} onChange={(event) => setDraft({ ...draft, job_title: event.target.value || null })} />
          </label>
        </div>
      </SettingsSection>

      <SettingsSection title="Locale" description="Defaults used when dates, times, and generated content are presented.">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium">
            Timezone
            <select className={settingsFieldClass} value={draft.timezone} onChange={(event) => setDraft({ ...draft, timezone: event.target.value })}>
              {timezones.map((timezone) => <option key={timezone}>{timezone}</option>)}
            </select>
          </label>
          <label className="text-sm font-medium">
            Language
            <select className={settingsFieldClass} value={draft.language} onChange={(event) => setDraft({ ...draft, language: event.target.value as ProfileSettings['language'] })}>
              <option value="en">English</option>
              <option value="ur">Urdu</option>
            </select>
          </label>
          <label className="text-sm font-medium">
            Date format
            <select className={settingsFieldClass} value={draft.date_format} onChange={(event) => setDraft({ ...draft, date_format: event.target.value as ProfileSettings['date_format'] })}>
              <option value="yyyy-mm-dd">YYYY-MM-DD</option>
              <option value="dd-mm-yyyy">DD-MM-YYYY</option>
              <option value="mm-dd-yyyy">MM-DD-YYYY</option>
            </select>
          </label>
          <label className="text-sm font-medium">
            Time format
            <select className={settingsFieldClass} value={draft.time_format} onChange={(event) => setDraft({ ...draft, time_format: event.target.value as ProfileSettings['time_format'] })}>
              <option value="12h">12 hour</option>
              <option value="24h">24 hour</option>
            </select>
          </label>
        </div>
      </SettingsSection>

      <div className="flex justify-end pt-6">
        <SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} />
      </div>
    </form>
  );
}
