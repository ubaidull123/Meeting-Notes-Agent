import { FormEvent, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { CredentialManager, ProviderModelControls, UsageModeControl, availableProviders } from '../../components/settings/AIProviderControls';
import { SettingsSaveButton, SettingsSection, settingsFieldClass } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useProviderCatalog, useTranscriptionSettings, useUpdateTranscriptionSettings } from '../../hooks/useSettings';
import { TranscriptionSettings } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

export function TranscriptionSettingsPage() {
  const query = useTranscriptionSettings();
  const catalog = useProviderCatalog();
  const update = useUpdateTranscriptionSettings();
  const [draft, setDraft] = useState<TranscriptionSettings | null>(null);
  useEffect(() => { if (query.data) setDraft(query.data); }, [query.data]);
  const isDirty = useMemo(() => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)), [draft, query.data]);

  if (query.isError || catalog.isError) return <ErrorState message={formatErrorMessage(query.error ?? catalog.error)} onRetry={() => { query.refetch(); catalog.refetch(); }} />;
  if (query.isLoading || catalog.isLoading || !draft || !catalog.data) return <LoadingState />;
  const providers = availableProviders(catalog.data, 'transcription').map(([id]) => id);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, { onSuccess: (saved) => { setDraft(saved); toast.success('Transcription settings saved'); }, onError: (error) => toast.error(formatErrorMessage(error)) });
  };

  return (
    <form onSubmit={submit}>
      <SettingsSection title="Transcription usage">
        <UsageModeControl value={draft.usage_mode} onChange={(usage_mode) => setDraft({ ...draft, usage_mode })} />
      </SettingsSection>
      <SettingsSection title="Provider and model">
        <ProviderModelControls catalog={catalog.data} capability="transcription" provider={draft.provider} model={draft.model} onProviderChange={(provider, model) => setDraft({ ...draft, provider, model })} onModelChange={(model) => setDraft({ ...draft, model })} />
      </SettingsSection>
      <SettingsSection title="Language">
        <label className="block max-w-md text-sm font-medium">Audio language<select className={settingsFieldClass} value={draft.language} onChange={(event) => setDraft({ ...draft, language: event.target.value })}><option value="auto">Auto detect</option><option value="en">English</option><option value="ur">Urdu</option></select></label>
      </SettingsSection>
      <SettingsSection title="API credentials" description="The same provider key can be used for supported AI and transcription services.">
        <CredentialManager providerIds={providers} catalog={catalog.data} credentials={draft.credentials} />
      </SettingsSection>
      <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} /></div>
    </form>
  );
}
