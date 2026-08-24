import { FormEvent, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { CredentialManager, ProviderModelControls, UsageModeControl, availableProviders } from '../../components/settings/AIProviderControls';
import { SettingsSaveButton, SettingsSection, settingsFieldClass } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useAISettings, useProviderCatalog, useUpdateAISettings } from '../../hooks/useSettings';
import { AISettings } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

export function AISettingsPage() {
  const query = useAISettings();
  const catalog = useProviderCatalog();
  const update = useUpdateAISettings();
  const [draft, setDraft] = useState<AISettings | null>(null);
  useEffect(() => { if (query.data) setDraft(query.data); }, [query.data]);
  const isDirty = useMemo(() => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)), [draft, query.data]);

  if (query.isError || catalog.isError) return <ErrorState message={formatErrorMessage(query.error ?? catalog.error)} onRetry={() => { query.refetch(); catalog.refetch(); }} />;
  if (query.isLoading || catalog.isLoading || !draft || !catalog.data) return <LoadingState />;

  const providers = availableProviders(catalog.data, 'chat').map(([id]) => id);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, { onSuccess: (saved) => { setDraft(saved); toast.success('AI settings saved'); }, onError: (error) => toast.error(formatErrorMessage(error)) });
  };

  return (
    <form onSubmit={submit}>
      <SettingsSection title="AI usage" description="Choose how generated meeting content is processed.">
        <UsageModeControl value={draft.llm_usage_mode} onChange={(llm_usage_mode) => setDraft({ ...draft, llm_usage_mode })} />
      </SettingsSection>
      <SettingsSection title="Provider and model">
        <ProviderModelControls
          catalog={catalog.data}
          capability="chat"
          provider={draft.llm_provider}
          model={draft.llm_model}
          onProviderChange={(llm_provider, llm_model) => setDraft({ ...draft, llm_provider, llm_model })}
          onModelChange={(llm_model) => setDraft({ ...draft, llm_model })}
        />
      </SettingsSection>
      <SettingsSection title="Advanced" description="Provider-independent generation controls.">
        <details>
          <summary className="cursor-pointer text-sm font-semibold">Generation controls</summary>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium">Temperature<input className={settingsFieldClass} type="number" min="0" max="2" step="0.1" value={draft.temperature} onChange={(event) => setDraft({ ...draft, temperature: Number(event.target.value) })} /></label>
            <label className="text-sm font-medium">Maximum output tokens<input className={settingsFieldClass} type="number" min="128" max="16000" step="128" value={draft.max_output_tokens} onChange={(event) => setDraft({ ...draft, max_output_tokens: Number(event.target.value) })} /></label>
            <label className="text-sm font-medium sm:col-span-2">Default response language<select className={settingsFieldClass} value={draft.response_language} onChange={(event) => setDraft({ ...draft, response_language: event.target.value })}><option value="auto">Match meeting language</option><option value="English">English</option><option value="Urdu">Urdu</option></select></label>
          </div>
        </details>
      </SettingsSection>
      <SettingsSection title="API credentials" description="Keys are encrypted and never returned to this browser.">
        <CredentialManager providerIds={providers} catalog={catalog.data} credentials={draft.credentials} />
      </SettingsSection>
      <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} /></div>
    </form>
  );
}
