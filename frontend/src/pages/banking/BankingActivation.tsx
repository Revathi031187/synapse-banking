import { useState } from 'react';
import { CheckCircle2, Check, XCircle, AlertTriangle, Database, Loader2, Info, RotateCcw } from 'lucide-react';
import { getBankingApiBase } from '../../utils/apiBase';
import { useSessionStorageState } from '../../hooks/useSessionStorageState';
import { AGENT_D_SESSION_LOG_KEY, type AgentDSessionLogEntry } from './BankingAgentD';

const API_BASE = getBankingApiBase();
const AEP_LAST_PUSHED_KEY = 'bankingActivation.aep.lastPushedTimestamp';

interface Connector {
  key: string;
  label: string;
  abbr: string;
  bg: string;
}

const CLOUD_PLATFORMS: Connector[] = [
  { key: 'databricks', label: 'Databricks', abbr: 'DB', bg: '#EA580C' },
  { key: 'snowflake', label: 'Snowflake', abbr: 'SF', bg: '#29B5E8' },
];
const MARKETING_PLATFORMS: Connector[] = [
  { key: 'google-ads', label: 'Google Ads', abbr: 'GA', bg: '#4285F4' },
  { key: 'salesforce', label: 'Salesforce Data 360', abbr: 'SD', bg: '#0EA5E9' },
  { key: 'aep', label: 'Adobe Experience Platform', abbr: 'AEP', bg: '#FA0F00' },
];

const ALL_CONNECTORS: Connector[] = [...CLOUD_PLATFORMS, ...MARKETING_PLATFORMS];

// ─── Field / section schema ────────────────────────────────────────────────
interface FieldDef {
  key: string;
  label: string;
  required?: boolean;
  type?: 'text' | 'textarea';
  placeholder?: string;
}

interface SectionDef {
  title: string;
  tag?: string;
  fields: FieldDef[];
}

const AEP_SECTIONS: SectionDef[] = [
  {
    title: 'Authentication',
    fields: [
      { key: 'clientId', label: 'Client ID (API Key)', required: true, placeholder: 'Enter your Client ID' },
      { key: 'clientSecret', label: 'Client Secret', required: true, placeholder: 'Enter your Client Secret' },
      { key: 'orgId', label: 'Organization ID (IMS Org)', required: true, placeholder: 'e.g. ABC123@AdobeOrg' },
    ],
  },
  {
    title: 'OAuth Credentials',
    tag: 'Recommended',
    fields: [
      { key: 'accessToken', label: 'Access Token (Generated)', required: true, type: 'textarea', placeholder: 'Paste your access token here' },
    ],
  },
  {
    title: 'Connection',
    fields: [
      { key: 'tenantId', label: 'Tenant ID', required: true, placeholder: 'e.g. yourcompany' },
      { key: 'sandbox', label: 'Sandbox Name', required: false, placeholder: 'prod' },
      { key: 'schemaName', label: 'Schema Name', required: false, placeholder: 'Synapse-Connection-Test-Schema' },
    ],
  },
];

// Pre-filled defaults for the demo AEP sandbox  -  never stored server-side, only used for this session.
const AEP_DEFAULT_VALUES: Record<string, string> = {
  clientId: 'c98c75d80dfc48d7bf209265bc1d441e',
  clientSecret: 'p8e-VZ5SpYW7WadWFMkx-R0a9mgQkaZPg6JR',
  orgId: '83E53FDE5D14A9330A495E27@AdobeOrg',
  tenantId: 'wrkshp5snbxamer',
  sandbox: 'latentviewanalytics-ucp',
};

// Credentials of the last successfully-tested AEP connection, cached locally so the
// user can come back and edit rather than re-enter everything from scratch.
const AEP_CREDENTIALS_STORAGE_KEY = 'bankingActivation.aep.credentials';

function loadCachedAEPCredentials(): Record<string, string> | null {
  try {
    const raw = window.localStorage.getItem(AEP_CREDENTIALS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveCachedAEPCredentials(values: Record<string, string>) {
  try {
    window.localStorage.setItem(AEP_CREDENTIALS_STORAGE_KEY, JSON.stringify(values));
  } catch {
    // Ignore storage errors (e.g. private browsing with storage disabled).
  }
}

function clearCachedAEPCredentials() {
  try {
    window.localStorage.removeItem(AEP_CREDENTIALS_STORAGE_KEY);
  } catch {
    // Ignore storage errors (e.g. private browsing with storage disabled).
  }
}

const SALESFORCE_SECTIONS: SectionDef[] = [
  {
    title: 'Authentication',
    fields: [
      { key: 'clientId', label: 'Client ID', required: true, placeholder: 'Enter your Client ID' },
      { key: 'clientSecret', label: 'Client Secret', required: true, placeholder: 'Enter your Client Secret' },
      { key: 'username', label: 'Username (during OAuth flow)', required: true, placeholder: 'Enter your username' },
      { key: 'password', label: 'Password (during OAuth flow)', required: true, placeholder: 'Enter your password' },
      { key: 'securityToken', label: 'Security Token', required: false, placeholder: 'Sometimes required by your org' },
      { key: 'refreshToken', label: 'Refresh Token', required: true, type: 'textarea', placeholder: 'Paste your refresh token here' },
      { key: 'accessToken', label: 'Access Token', required: true, type: 'textarea', placeholder: 'Paste your access token here' },
    ],
  },
];

const GOOGLE_ADS_SECTIONS: SectionDef[] = [
  {
    title: 'Authentication',
    fields: [
      { key: 'clientId', label: 'Client ID', required: true, placeholder: 'Enter your Client ID' },
      { key: 'clientSecret', label: 'Client Secret', required: true, placeholder: 'Enter your Client Secret' },
      { key: 'refreshToken', label: 'Refresh Token', required: true, type: 'textarea', placeholder: 'Paste your refresh token here' },
      { key: 'developerToken', label: 'Developer Token', required: true, placeholder: 'Enter your developer token' },
    ],
  },
];

const FORM_CONFIG: Record<string, SectionDef[]> = {
  aep: AEP_SECTIONS,
  salesforce: SALESFORCE_SECTIONS,
  'google-ads': GOOGLE_ADS_SECTIONS,
};

interface SnowflakeOption {
  key: string;
  label: string;
  tag?: string;
  fields: FieldDef[];
}

const SNOWFLAKE_OPTIONS: SnowflakeOption[] = [
  {
    key: 'password',
    label: 'Username & Password',
    tag: 'Most Common',
    fields: [
      { key: 'username', label: 'Username', required: true, placeholder: 'Enter your username' },
      { key: 'password', label: 'Password', required: true, placeholder: 'Enter your password' },
    ],
  },
  {
    key: 'oauth',
    label: 'OAuth',
    tag: 'Recommended',
    fields: [
      { key: 'clientId', label: 'Client ID', required: true, placeholder: 'Enter your Client ID' },
      { key: 'clientSecret', label: 'Client Secret', required: true, placeholder: 'Enter your Client Secret' },
      { key: 'accessToken', label: 'Access Token (Generated)', required: true, type: 'textarea', placeholder: 'Paste your access token here' },
    ],
  },
  {
    key: 'keypair',
    label: 'Key Pair Authentication',
    fields: [
      { key: 'username', label: 'Username', required: true, placeholder: 'Enter your username' },
      { key: 'privateKey', label: 'Private Key', required: true, type: 'textarea', placeholder: 'Paste your private key here' },
      { key: 'passphrase', label: 'Passphrase', required: false, placeholder: 'Only if your key is encrypted' },
    ],
  },
];

const CONNECT_BUTTON_LABEL: Record<string, string> = {
  aep: 'Connect to AEP',
  snowflake: 'Connect to Snowflake',
  salesforce: 'Connect to Salesforce Data 360',
  'google-ads': 'Connect to Google Ads',
};

function fieldsComplete(fields: FieldDef[], values: Record<string, string>): boolean {
  return fields.every(f => !f.required || (values[f.key] || '').trim() !== '');
}

// ─── Adobe Experience Platform  -  real activation ───────────────────────────
interface AEPErrorDetail {
  step: string;
  status: number | null;
  title: string;
  detail: string;
  type: string | null;
  registryRequestId: string | null;
  subErrors: unknown[];
  timestamp: string | null;
  rawResponse: unknown;
}

interface AEPConnectionResult {
  schemaId: string;
  schemaTitle: string;
  fieldGroupId: string;
  fieldGroupTitle: string;
  tenantId: string;
  sandbox: string;
  imsOrg: string;
  connectedAt: string;
}

const AEP_STEP_LABELS: Record<string, string> = {
  auth_validation: 'Credential validation failed',
  fieldgroup_creation: 'Field Group creation failed',
  schema_creation: 'Schema creation failed',
  schema_lookup: 'Schema lookup failed',
  dataset_creation: 'Dataset creation failed',
  batch_creation: 'Batch creation failed',
  batch_upload: 'Batch file upload failed',
  batch_completion: 'Batch completion failed',
  batch_validation: 'Batch validation failed',
  network: 'Network request failed',
  unknown: 'Request failed',
};

interface AEPDatasetResult {
  datasetId: string;
  datasetName: string;
  schemaId: string;
  pushedCount: number;
  skippedCount: number;
  records: Array<{
    customerId: string;
    nbaPersona: string;
    recommendedProductId: string;
    offerName: string;
    lastActivationDate: string;
  }>;
  batch: { batchId: string; status: string; recordCount: number };
}

// ─── UI bits ────────────────────────────────────────────────────────────────
function ConnectorCard({
  connector, selected, onSelect,
}: { connector: Connector; selected: boolean; onSelect: (key: string) => void }) {
  return (
    <button
      onClick={() => onSelect(connector.key)}
      className={`relative flex items-center gap-3 bg-white border-2 rounded-xl p-4 text-left transition-all ${
        selected ? 'border-violet-600 ring-2 ring-violet-100' : 'border-gray-200 hover:shadow-md hover:border-gray-300'
      }`}
    >
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0"
        style={{ background: connector.bg }}
      >
        {connector.abbr}
      </div>
      <span className="text-sm font-semibold text-gray-900">{connector.label}</span>
      {selected && (
        <span className="absolute top-2 right-2 w-5 h-5 rounded-full bg-violet-600 flex items-center justify-center">
          <Check className="w-3 h-3 text-white" />
        </span>
      )}
    </button>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-bold uppercase tracking-wide text-gray-400 mb-3">{children}</p>
  );
}

function FieldLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <label className="block text-[11px] font-bold uppercase tracking-wide text-gray-400 mb-1.5">
      {children} {required && <span className="text-rose-500">*</span>}
    </label>
  );
}

const inputClass =
  'w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 ' +
  'focus:outline-none focus:ring-2 focus:ring-violet-100 focus:border-violet-500 transition-colors';

function FormField({
  field, value, onChange,
}: { field: FieldDef; value: string; onChange: (v: string) => void }) {
  const isTextarea = field.type === 'textarea';
  return (
    <div className={isTextarea ? 'col-span-2' : ''}>
      <FieldLabel required={field.required}>{field.label}</FieldLabel>
      {isTextarea ? (
        <textarea
          rows={3}
          placeholder={field.placeholder}
          className={`${inputClass} resize-y`}
          value={value}
          onChange={e => onChange(e.target.value)}
        />
      ) : (
        <input
          type="text"
          placeholder={field.placeholder}
          className={inputClass}
          value={value}
          onChange={e => onChange(e.target.value)}
        />
      )}
    </div>
  );
}

function DetailRow({ label, value, mono }: { label: string; value?: string | null; mono?: boolean }) {
  if (!value) return null;
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] font-bold uppercase tracking-wide text-gray-400 flex-shrink-0">{label}</span>
      <span
        className={`text-sm text-gray-800 truncate max-w-[240px] ${mono ? 'font-mono text-xs' : ''}`}
        title={value}
      >
        {value}
      </span>
    </div>
  );
}

function AEPErrorPanel({ error }: { error: AEPErrorDetail }) {
  const responseJson = {
    detail: error.detail,
    status: error.status,
    title: error.title,
    type: error.type,
    report: {
      'detailed-message': error.detail,
      registryRequestId: error.registryRequestId,
      'sub-errors': error.subErrors,
      timestamp: error.timestamp,
    },
  };
  return (
    <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 overflow-hidden">
      <div className="flex items-start gap-3 px-5 py-4 border-b border-rose-200">
        <XCircle className="w-5 h-5 text-rose-600 mt-0.5 flex-shrink-0" />
        <div>
          <h4 className="text-sm font-bold text-rose-800">{error.title || 'Connection Failed'}</h4>
          <p className="text-sm text-rose-700 mt-0.5">
            {AEP_STEP_LABELS[error.step] || AEP_STEP_LABELS.unknown}
            {error.status ? ` (HTTP ${error.status})` : ''}
          </p>
        </div>
      </div>
      <div className="px-5 py-4 space-y-4">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-rose-400 mb-1.5">Failed Step</p>
          <div className="bg-white border border-rose-100 rounded-lg px-3 py-2 text-sm font-mono text-rose-900">
            {error.step}
          </div>
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-rose-400 mb-1.5">API Response</p>
          <pre className="bg-white border border-rose-100 rounded-lg px-3 py-3 text-xs font-mono text-rose-900 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(responseJson, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}

function SectionTag({ children }: { children: React.ReactNode }) {
  return (
    <span className="ml-2 text-[10px] font-bold uppercase tracking-wide text-violet-600 bg-violet-50 border border-violet-100 rounded-full px-2 py-0.5">
      {children}
    </span>
  );
}

function FormSections({
  sections, values, onChange,
}: { sections: SectionDef[]; values: Record<string, string>; onChange: (key: string, value: string) => void }) {
  return (
    <>
      {sections.map((section, idx) => (
        <div key={section.title + idx} className={idx === 0 ? 'mb-6' : 'mt-6 mb-6'}>
          <div className="flex items-center border-b border-gray-100 pb-2 mb-4">
            <h3 className="text-sm font-bold text-gray-800">{section.title}</h3>
            {section.tag && <SectionTag>{section.tag}</SectionTag>}
          </div>
          <div className="grid grid-cols-2 gap-5">
            {section.fields.map(field => (
              <FormField
                key={field.key}
                field={field}
                value={values[field.key] || ''}
                onChange={v => onChange(field.key, v)}
              />
            ))}
          </div>
        </div>
      ))}
    </>
  );
}

export default function BankingActivation() {
  const [step, setStep] = useState<'select' | 'configure' | 'success'>('select');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [snowflakeOptionKey, setSnowflakeOptionKey] = useState<string>('oauth');
  const [aepConnecting, setAepConnecting] = useState(false);
  const [aepError, setAepError] = useState<AEPErrorDetail | null>(null);
  const [aepResult, setAepResult] = useState<AEPConnectionResult | null>(null);
  const [hasCachedAepCredentials, setHasCachedAepCredentials] = useState(() => loadCachedAEPCredentials() !== null);

  const [datasetName, setDatasetName] = useState('');
  const [datasetCreating, setDatasetCreating] = useState(false);
  const [datasetError, setDatasetError] = useState<AEPErrorDetail | null>(null);
  const [datasetResult, setDatasetResult] = useState<AEPDatasetResult | null>(null);
  const [sessionLog] = useSessionStorageState<AgentDSessionLogEntry[]>(AGENT_D_SESSION_LOG_KEY, []);
  const [lastPushedTimestamp, setLastPushedTimestamp] = useSessionStorageState<string | null>(
    AEP_LAST_PUSHED_KEY,
    null
  );
  const unpushedEntries = sessionLog.filter((e) => !lastPushedTimestamp || e.timestamp > lastPushedTimestamp);

  const selectedConnector = ALL_CONNECTORS.find(c => c.key === selectedKey) || null;
  const connectorKey = selectedConnector?.key || '';
  const isSnowflake = connectorKey === 'snowflake';
  const formSections = FORM_CONFIG[connectorKey];
  const activeSnowflakeOption = SNOWFLAKE_OPTIONS.find(o => o.key === snowflakeOptionKey) || SNOWFLAKE_OPTIONS[0];

  const canProceed = isSnowflake
    ? fieldsComplete(activeSnowflakeOption.fields, formValues)
    : formSections
      ? fieldsComplete(formSections.flatMap(s => s.fields), formValues)
      : true;

  const handleFieldChange = (key: string, value: string) => setFormValues(prev => ({ ...prev, [key]: value }));

  const goToConfigure = () => {
    if (!selectedConnector) return;
    if (connectorKey === 'aep') {
      setFormValues(loadCachedAEPCredentials() || { ...AEP_DEFAULT_VALUES });
    } else {
      setFormValues({});
    }
    setSnowflakeOptionKey('oauth');
    setAepError(null);
    setAepResult(null);
    setStep('configure');
  };

  const goBackToSelect = () => {
    setAepError(null);
    setStep('select');
  };

  const handleResetAepConnection = () => {
    clearCachedAEPCredentials();
    setHasCachedAepCredentials(false);
    setAepResult(null);
    setAepError(null);
    setFormValues({});
    setStep('configure');
  };

  const restart = () => {
    setStep('select');
    setSelectedKey(null);
    setFormValues({});
    setSnowflakeOptionKey('oauth');
    setAepConnecting(false);
    setAepError(null);
    setAepResult(null);
    setDatasetName('');
    setDatasetCreating(false);
    setDatasetError(null);
    setDatasetResult(null);
  };

  const handleCreateDataset = async () => {
    if (unpushedEntries.length === 0 || datasetCreating || !datasetName.trim()) return;

    setDatasetCreating(true);
    setDatasetError(null);
    try {
      const res = await fetch(`${API_BASE}/api/banking/aep/create-dataset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          datasetName: datasetName.trim(),
          schemaName: formValues.schemaName || '',
          clientId: formValues.clientId || '',
          orgId: formValues.orgId || '',
          accessToken: formValues.accessToken || '',
          sandbox: formValues.sandbox || 'prod',
          tenantId: formValues.tenantId || '',
          agentDResults: unpushedEntries.map((e) => ({
            customerId: e.customerId,
            timestamp: e.timestamp,
            data: e.data,
          })),
        }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setDatasetError(
          data.error || {
            step: 'unknown',
            status: res.status,
            title: 'Dataset Creation Failed',
            detail: data.detail || 'The request to Adobe Experience Platform failed.',
            type: null,
            registryRequestId: null,
            subErrors: [],
            timestamp: null,
            rawResponse: data,
          }
        );
        return;
      }

      // All entries in this attempt are considered handled (pushed, or permanently
      // skipped as malformed)  -  advance the watermark past the newest one so a
      // retry only ever picks up entries generated after this click.
      const newestTimestamp = unpushedEntries.reduce(
        (max, e) => (e.timestamp > max ? e.timestamp : max),
        unpushedEntries[0].timestamp
      );
      setLastPushedTimestamp(newestTimestamp);
      setDatasetResult(data);
    } catch (err) {
      setDatasetError({
        step: 'network',
        status: null,
        title: 'Network Error',
        detail: err instanceof Error ? err.message : 'Could not reach the activation service.',
        type: null,
        registryRequestId: null,
        subErrors: [],
        timestamp: null,
        rawResponse: null,
      });
    } finally {
      setDatasetCreating(false);
    }
  };

  const handleConnect = async () => {
    if (!canProceed || aepConnecting) return;

    if (connectorKey !== 'aep') {
      setStep('success');
      return;
    }

    const credentials = {
      clientId: formValues.clientId || '',
      clientSecret: formValues.clientSecret || '',
      orgId: formValues.orgId || '',
      accessToken: formValues.accessToken || '',
      sandbox: formValues.sandbox || 'prod',
      tenantId: formValues.tenantId || '',
      schemaName: formValues.schemaName || '',
    };

    setAepConnecting(true);
    setAepError(null);
    try {
      const res = await fetch(`${API_BASE}/api/banking/activation/aep/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: credentials.clientId,
          client_secret: credentials.clientSecret,
          org_id: credentials.orgId,
          access_token: credentials.accessToken,
          sandbox: credentials.sandbox,
          tenant_id: credentials.tenantId,
          schema_name: credentials.schemaName,
        }),
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setAepError(
          data.error || {
            step: 'unknown',
            status: res.status,
            title: 'Connection Failed',
            detail: data.detail || 'The request to Adobe Experience Platform failed.',
            type: null,
            registryRequestId: null,
            subErrors: [],
            timestamp: null,
            rawResponse: data,
          }
        );
        return;
      }

      saveCachedAEPCredentials(credentials);
      setHasCachedAepCredentials(true);
      setAepResult(data.connection);
      setStep('success');
    } catch (err) {
      setAepError({
        step: 'network',
        status: null,
        title: 'Network Error',
        detail: err instanceof Error ? err.message : 'Could not reach the activation service.',
        type: null,
        registryRequestId: null,
        subErrors: [],
        timestamp: null,
        rawResponse: null,
      });
    } finally {
      setAepConnecting(false);
    }
  };

  return (
    <div className="min-h-full bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-10 px-6">
      <div className="max-w-4xl mx-auto">

        {step === 'select' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Choose destination for activation</h2>
            <p className="text-sm text-gray-500 mb-6">Pick where your data should be delivered.</p>

            <SectionLabel>Cloud Platforms</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-6">
              {CLOUD_PLATFORMS.map(c => (
                <ConnectorCard key={c.key} connector={c} selected={selectedKey === c.key} onSelect={setSelectedKey} />
              ))}
            </div>

            <SectionLabel>Marketing Platforms</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-8">
              {MARKETING_PLATFORMS.map(c => (
                <ConnectorCard key={c.key} connector={c} selected={selectedKey === c.key} onSelect={setSelectedKey} />
              ))}
            </div>

            <div className="flex justify-end gap-3">
              {connectorKey === 'aep' && hasCachedAepCredentials && (
                <button
                  onClick={handleResetAepConnection}
                  className="flex items-center gap-1.5 text-sm font-semibold px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset Connection
                </button>
              )}
              <button
                onClick={goToConfigure}
                disabled={!selectedConnector}
                className={`text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors ${
                  selectedConnector
                    ? 'bg-violet-600 hover:bg-violet-700 text-white cursor-pointer'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {connectorKey === 'aep' && hasCachedAepCredentials ? 'Edit Connection →' : 'Continue →'}
              </button>
            </div>
          </div>
        )}

        {step === 'configure' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
            {isSnowflake ? (
              <>
                <h2 className="text-lg font-bold text-gray-900 mb-1">Snowflake Authentication</h2>
                <p className="text-sm text-gray-500 mb-6">
                  Choose an authentication method. These credentials are used only for this session and are never stored.
                </p>

                <div className="flex gap-2 mb-6 flex-wrap">
                  {SNOWFLAKE_OPTIONS.map((opt, idx) => (
                    <button
                      key={opt.key}
                      onClick={() => setSnowflakeOptionKey(opt.key)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 text-sm font-semibold transition-colors ${
                        snowflakeOptionKey === opt.key
                          ? 'border-violet-600 bg-violet-50 text-violet-700'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      Option {idx + 1}: {opt.label}
                      {opt.tag && <SectionTag>{opt.tag}</SectionTag>}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-5 mb-2">
                  {activeSnowflakeOption.fields.map(field => (
                    <FormField
                      key={field.key}
                      field={field}
                      value={formValues[field.key] || ''}
                      onChange={v => handleFieldChange(field.key, v)}
                    />
                  ))}
                </div>
              </>
            ) : formSections ? (
              <>
                <h2 className="text-lg font-bold text-gray-900 mb-1">{selectedConnector?.label} Credentials</h2>
                <p className="text-sm text-gray-500 mb-2">
                  Enter your {selectedConnector?.label} credentials. These are used only for this session and are never stored.
                </p>
                <FormSections sections={formSections} values={formValues} onChange={handleFieldChange} />
              </>
            ) : (
              <>
                <h2 className="text-lg font-bold text-gray-900 mb-1">
                  Configure {selectedConnector?.label}
                </h2>
                <p className="text-sm text-gray-500 mb-10">Ready to connect this destination.</p>
                <div className="min-h-[220px]" />
              </>
            )}

            {connectorKey === 'aep' && aepError && <AEPErrorPanel error={aepError} />}

            <div className="flex justify-between mt-2">
              <button
                onClick={goBackToSelect}
                className="text-sm font-semibold px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={handleConnect}
                disabled={!canProceed || aepConnecting}
                className={`text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors ${
                  canProceed && !aepConnecting
                    ? 'bg-violet-600 hover:bg-violet-700 text-white cursor-pointer'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {aepConnecting ? 'Connecting…' : CONNECT_BUTTON_LABEL[connectorKey] || 'Proceed with activation →'}
              </button>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-12 flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-9 h-9 text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">
              Activation to {selectedConnector?.label} was successful
            </h2>
            <p className="text-sm text-gray-500 mb-8">
              {connectorKey === 'aep' && aepResult?.schemaTitle
                ? `Schema "${aepResult.schemaTitle}" was created in your Adobe Experience Platform sandbox.`
                : 'Your data has been connected and delivered to the selected destination.'}
            </p>

            {connectorKey === 'aep' && aepResult && (
              <div className="w-full max-w-md text-left bg-gray-50 border border-gray-200 rounded-xl p-5 mb-8 space-y-2.5">
                <DetailRow label="Schema Name" value={aepResult.schemaTitle} />
                <DetailRow label="Schema ID" value={aepResult.schemaId} mono />
                <DetailRow label="Field Group ID" value={aepResult.fieldGroupId} mono />
                <DetailRow label="Tenant ID" value={aepResult.tenantId} />
                <DetailRow label="Sandbox" value={aepResult.sandbox} />
                <DetailRow label="IMS Org" value={aepResult.imsOrg} />
                <DetailRow
                  label="Connected At"
                  value={aepResult.connectedAt ? new Date(aepResult.connectedAt).toLocaleString() : undefined}
                />
              </div>
            )}

            {connectorKey === 'aep' && aepResult && (
              <div className="w-full max-w-md text-left bg-white border border-gray-200 rounded-xl p-5 mb-8">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="w-4 h-4 text-violet-600" />
                  <h3 className="text-sm font-bold text-gray-800">Create Dataset from Agent D</h3>
                </div>

                {sessionLog.length === 0 ? (
                  <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-amber-800">
                      Run Agent D for a customer first  -  there's no orchestration result to ingest yet.
                    </p>
                  </div>
                ) : datasetResult ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-emerald-700 text-sm font-semibold mb-1">
                      <CheckCircle2 className="w-4 h-4" />
                      {datasetResult.pushedCount} record{datasetResult.pushedCount === 1 ? '' : 's'} ingested
                      {datasetResult.skippedCount > 0 && ` (${datasetResult.skippedCount} skipped)`}
                    </div>
                    <DetailRow label="Dataset Name" value={datasetResult.datasetName} />
                    <DetailRow label="Dataset ID" value={datasetResult.datasetId} mono />
                    <DetailRow label="Batch Status" value={datasetResult.batch.status} />
                    <div className="border-t border-gray-100 pt-2.5 space-y-2 max-h-48 overflow-y-auto">
                      {datasetResult.records.map((r, i) => (
                        <div key={i} className="text-xs bg-gray-50 rounded-lg px-3 py-2">
                          <span className="font-mono text-gray-500">{r.customerId}</span>
                          <span className="text-gray-400"> · </span>
                          <span className="text-gray-700">{r.nbaPersona}</span>
                          <span className="text-gray-400"> · </span>
                          <span className="font-mono text-gray-500">{r.recommendedProductId}</span>
                          <span className="text-gray-400"> · </span>
                          <span className="text-gray-700">{r.offerName || ' - '}</span>
                          <span className="text-gray-400"> · </span>
                          <span className="text-gray-500">{new Date(r.lastActivationDate).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                    {unpushedEntries.length > 0 && (
                      <div className="flex items-center justify-between gap-3 bg-violet-50 border border-violet-100 rounded-lg px-3 py-2">
                        <p className="text-xs text-violet-700">
                          {unpushedEntries.length} more result{unpushedEntries.length === 1 ? '' : 's'} generated since.
                        </p>
                        <button
                          onClick={() => setDatasetResult(null)}
                          className="flex-shrink-0 text-xs font-semibold text-violet-700 hover:text-violet-900 underline"
                        >
                          Push {unpushedEntries.length} more →
                        </button>
                      </div>
                    )}
                  </div>
                ) : unpushedEntries.length === 0 ? (
                  <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2.5">
                    <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-blue-800">
                      All {sessionLog.length} Agent D result{sessionLog.length === 1 ? '' : 's'} generated this session
                      {sessionLog.length === 1 ? ' has' : ' have'} already been pushed. Run Agent D again for more
                      customers to add new records.
                    </p>
                  </div>
                ) : (
                  <>
                    <p className="text-xs text-gray-500 mb-3">
                      {unpushedEntries.length} new Agent D result{unpushedEntries.length === 1 ? '' : 's'} from this
                      session (across {new Set(unpushedEntries.map((e) => e.customerId)).size} customer
                      {new Set(unpushedEntries.map((e) => e.customerId)).size === 1 ? '' : 's'}) will be pulled,
                      mapped to the schema above, and ingested as one batch.
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Dataset name"
                        className={inputClass}
                        value={datasetName}
                        onChange={e => setDatasetName(e.target.value)}
                      />
                      <button
                        onClick={handleCreateDataset}
                        disabled={datasetCreating || !datasetName.trim()}
                        className={`flex-shrink-0 text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors ${
                          !datasetCreating && datasetName.trim()
                            ? 'bg-violet-600 hover:bg-violet-700 text-white cursor-pointer'
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        {datasetCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Dataset'}
                      </button>
                    </div>
                  </>
                )}

                {datasetError && <AEPErrorPanel error={datasetError} />}
              </div>
            )}

            <button
              onClick={restart}
              className="text-sm font-semibold px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Start over
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
