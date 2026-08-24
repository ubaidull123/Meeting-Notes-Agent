import { FormEvent, useEffect, useMemo, useState } from 'react';
import { CheckCircle2, KeyRound, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { SettingsSaveButton, SettingsSection, SettingsToggle, settingsFieldClass } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useCredentials, useDeleteCredential, useEmailSettings, useMeetingDefaults, useProviderCatalog, useSaveCredential, useTestCredential, useUpdateEmailSettings, useUpdateMeetingDefaults } from '../../hooks/useSettings';
import { EmailSettings, MeetingDefaults, UsageMode } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

function UsageModeControl({ value, onChange }: { value: UsageMode; onChange: (value: UsageMode) => void }) {
  return <div className="grid grid-cols-2 gap-2">{([['app_credits', 'Application email'], ['byok', 'My email provider']] as const).map(([mode, label]) => <button key={mode} type="button" onClick={() => onChange(mode)} className={`rounded-md border px-3 py-2 text-sm font-medium ${value === mode ? 'border-teal-600 bg-teal-50 text-teal-800 dark:bg-teal-950/50 dark:text-teal-200' : 'border-border hover:bg-muted'}`}>{label}</button>)}</div>;
}

export function EmailSettingsPage() {
  const emailQuery = useEmailSettings();
  const defaultsQuery = useMeetingDefaults();
  const credentialsQuery = useCredentials();
  const catalogQuery = useProviderCatalog();
  const updateEmail = useUpdateEmailSettings();
  const updateDefaults = useUpdateMeetingDefaults();
  const saveCredential = useSaveCredential();
  const testCredential = useTestCredential();
  const deleteCredential = useDeleteCredential();
  const [draft, setDraft] = useState<EmailSettings | null>(null);
  const [defaults, setDefaults] = useState<MeetingDefaults | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [domain, setDomain] = useState('');

  useEffect(() => { if (emailQuery.data) setDraft(emailQuery.data); }, [emailQuery.data]);
  useEffect(() => { if (defaultsQuery.data) setDefaults(defaultsQuery.data); }, [defaultsQuery.data]);
  useEffect(() => { const saved = credentialsQuery.data?.find((item) => item.provider === draft?.provider); if (saved?.configuration.domain) setDomain(saved.configuration.domain); }, [credentialsQuery.data, draft?.provider]);
  const isDirty = useMemo(() => Boolean(draft && defaults && ((emailQuery.data && JSON.stringify(draft) !== JSON.stringify(emailQuery.data)) || (defaultsQuery.data && JSON.stringify(defaults) !== JSON.stringify(defaultsQuery.data)))), [draft, defaults, emailQuery.data, defaultsQuery.data]);

  if (emailQuery.isError || defaultsQuery.isError || credentialsQuery.isError || catalogQuery.isError) return <ErrorState message={formatErrorMessage(emailQuery.error ?? defaultsQuery.error ?? credentialsQuery.error ?? catalogQuery.error)} onRetry={() => { void emailQuery.refetch(); void defaultsQuery.refetch(); void credentialsQuery.refetch(); void catalogQuery.refetch(); }} />;
  if (!draft || !defaults || !catalogQuery.data || emailQuery.isLoading || defaultsQuery.isLoading || credentialsQuery.isLoading || catalogQuery.isLoading) return <LoadingState />;
  const credential = credentialsQuery.data?.find((item) => item.provider === draft.provider);
  const emailProviders = Object.entries(catalogQuery.data).filter(([, item]) => item.enabled && item.capabilities.includes('email'));
  const config = draft.provider === 'mailgun' ? { domain } : undefined;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const [savedEmail, savedDefaults] = await Promise.all([updateEmail.mutateAsync(draft), updateDefaults.mutateAsync(defaults)]);
      setDraft(savedEmail); setDefaults(savedDefaults); toast.success('Email settings saved');
    } catch (error) { toast.error(formatErrorMessage(error)); }
  };

  const saveKey = async () => {
    if (!apiKey.trim()) { toast.error('Enter an API key'); return; }
    if (draft.provider === 'mailgun' && !domain.trim()) { toast.error('Enter the Mailgun sending domain'); return; }
    try { await saveCredential.mutateAsync({ provider: draft.provider, apiKey, config }); setApiKey(''); toast.success('Credential saved. Test the connection before use.'); } catch (error) { toast.error(formatErrorMessage(error)); }
  };

  return <form onSubmit={submit}>
    <SettingsSection title="Delivery mode" description="Use application-managed delivery or an encrypted personal provider credential.">
      <UsageModeControl value={draft.email_mode} onChange={(email_mode) => setDraft({ ...draft, email_mode })} />
      <label className="mt-4 block text-sm font-medium">Provider<select className={settingsFieldClass} value={draft.provider} onChange={(event) => { setDraft({ ...draft, provider: event.target.value }); setApiKey(''); setDomain(''); }}>{emailProviders.map(([id, item]) => <option key={id} value={id}>{item.name}</option>)}</select></label>
    </SettingsSection>
    <SettingsSection title="Sender identity" description="Sender fields are applied to follow-up email delivery.">
      <div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium">Sender name<input className={settingsFieldClass} value={draft.sender_name ?? ''} onChange={(event) => setDraft({ ...draft, sender_name: event.target.value || null })}/></label><label className="text-sm font-medium">Sender email<input type="email" className={settingsFieldClass} value={draft.sender_email ?? ''} onChange={(event) => setDraft({ ...draft, sender_email: event.target.value || null })}/></label><label className="text-sm font-medium sm:col-span-2">Reply-to email<input type="email" className={settingsFieldClass} value={draft.reply_to_email ?? ''} onChange={(event) => setDraft({ ...draft, reply_to_email: event.target.value || null })}/></label></div>
    </SettingsSection>
    {draft.email_mode === 'byok' && <SettingsSection title={`${draft.provider === 'mailgun' ? 'Mailgun' : 'Resend'} credential`} description="Secrets are encrypted at rest and are never returned to this page.">
      {credential?.has_api_key && <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-md border border-border p-3"><span className="flex items-center gap-2 text-sm"><CheckCircle2 className={`h-4 w-4 ${credential.is_valid ? 'text-emerald-600' : 'text-amber-600'}`}/>{credential.is_valid ? 'Connected' : 'Saved, not verified'} <span className="text-muted-foreground">{credential.api_key_hint}</span></span><div className="flex gap-2"><button type="button" onClick={() => testCredential.mutate({ provider: draft.provider }, { onSuccess: (result) => result.valid ? toast.success(result.message) : toast.error(result.message) })} className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted">Test connection</button><button type="button" title="Remove credential" onClick={() => deleteCredential.mutate(draft.provider)} className="rounded-md border border-border p-2 text-rose-600 hover:bg-muted"><Trash2 className="h-4 w-4"/></button></div></div>}
      <div className="grid gap-4 sm:grid-cols-2">{draft.provider === 'mailgun' && <label className="text-sm font-medium">Sending domain<input className={settingsFieldClass} value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="mg.example.com" /></label>}<label className="text-sm font-medium">{credential ? 'Replacement API key' : 'API key'}<input type="password" autoComplete="off" className={settingsFieldClass} value={apiKey} onChange={(event) => setApiKey(event.target.value)} /></label></div><button type="button" onClick={saveKey} disabled={saveCredential.isPending} className="mt-4 inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"><KeyRound className="h-4 w-4" />{credential ? 'Replace credential' : 'Save credential'}</button>
    </SettingsSection>}
    <SettingsSection title="Email behavior" description="These use the same defaults as the processing and approval workflow."><SettingsToggle checked={defaults.generate_follow_up_email} onChange={(value) => setDefaults({ ...defaults, generate_follow_up_email: value })} label="Generate follow-up email automatically"/><SettingsToggle checked={defaults.require_email_approval} onChange={(value) => setDefaults({ ...defaults, require_email_approval: value })} label="Require approval before sending" description="Keeps generated email in review until a user approves it."/></SettingsSection>
    <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={updateEmail.isPending || updateDefaults.isPending} isDirty={isDirty}/></div>
  </form>;
}
