import { useState } from 'react';
import { CheckCircle2, Check } from 'lucide-react';

interface Connector {
  key: string;
  label: string;
  abbr: string;
  bg: string;
}

const FILE_UPLOAD: Connector = { key: 'csv', label: 'File Upload (CSV/XLSX/TSV)', abbr: 'CSV', bg: '#10B981' };
const CLOUD_PLATFORMS: Connector[] = [
  { key: 'databricks', label: 'Databricks', abbr: 'DB', bg: '#EA580C' },
  { key: 'aep', label: 'Adobe Experience Platform', abbr: 'AEP', bg: '#FA0F00' },
  { key: 'snowflake', label: 'Snowflake', abbr: 'SF', bg: '#29B5E8' },
];
const ENTERPRISE_SYSTEMS: Connector[] = [
  { key: 'salesforce', label: 'Salesforce CRM', abbr: 'SC', bg: '#0EA5E9' },
];
const MARKETING_PLATFORMS: Connector[] = [
  { key: 'google-ads', label: 'Google Ads', abbr: 'GA', bg: '#4285F4' },
];

const ALL_CONNECTORS: Connector[] = [FILE_UPLOAD, ...CLOUD_PLATFORMS, ...ENTERPRISE_SYSTEMS, ...MARKETING_PLATFORMS];

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
      { key: 'sandbox', label: 'Sandbox Name', required: false, placeholder: 'prod' },
    ],
  },
];

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
  salesforce: 'Connect to Salesforce',
  'google-ads': 'Connect to Google Ads',
};

function fieldsComplete(fields: FieldDef[], values: Record<string, string>): boolean {
  return fields.every(f => !f.required || (values[f.key] || '').trim() !== '');
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

export default function BankingDataIntegration() {
  const [step, setStep] = useState<'select' | 'configure' | 'success'>('select');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [snowflakeOptionKey, setSnowflakeOptionKey] = useState<string>('oauth');

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
    setFormValues({});
    setSnowflakeOptionKey('oauth');
    setStep('configure');
  };

  const restart = () => {
    setStep('select');
    setSelectedKey(null);
    setFormValues({});
    setSnowflakeOptionKey('oauth');
  };

  return (
    <div className="min-h-full bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-10 px-6">
      <div className="max-w-4xl mx-auto">

        {step === 'select' && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Choose destination for data integration</h2>
            <p className="text-sm text-gray-500 mb-6">Pick where your data should be delivered.</p>

            <SectionLabel>File Upload</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-6">
              <ConnectorCard connector={FILE_UPLOAD} selected={selectedKey === FILE_UPLOAD.key} onSelect={setSelectedKey} />
            </div>

            <SectionLabel>Cloud Platforms</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-6">
              {CLOUD_PLATFORMS.map(c => (
                <ConnectorCard key={c.key} connector={c} selected={selectedKey === c.key} onSelect={setSelectedKey} />
              ))}
            </div>

            <SectionLabel>Enterprise Systems</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-6">
              {ENTERPRISE_SYSTEMS.map(c => (
                <ConnectorCard key={c.key} connector={c} selected={selectedKey === c.key} onSelect={setSelectedKey} />
              ))}
            </div>

            <SectionLabel>Marketing Platforms</SectionLabel>
            <div className="grid grid-cols-3 gap-3 mb-8">
              {MARKETING_PLATFORMS.map(c => (
                <ConnectorCard key={c.key} connector={c} selected={selectedKey === c.key} onSelect={setSelectedKey} />
              ))}
            </div>

            <div className="flex justify-end">
              <button
                onClick={goToConfigure}
                disabled={!selectedConnector}
                className={`text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors ${
                  selectedConnector
                    ? 'bg-violet-600 hover:bg-violet-700 text-white cursor-pointer'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                Continue →
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

            <div className="flex justify-between mt-2">
              <button
                onClick={() => setStep('select')}
                className="text-sm font-semibold px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ← Back
              </button>
              <button
                onClick={() => canProceed && setStep('success')}
                disabled={!canProceed}
                className={`text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors ${
                  canProceed
                    ? 'bg-violet-600 hover:bg-violet-700 text-white cursor-pointer'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                {CONNECT_BUTTON_LABEL[connectorKey] || 'Proceed with integration →'}
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
              Data integration to {selectedConnector?.label} was successful
            </h2>
            <p className="text-sm text-gray-500 mb-8">Your data has been connected and delivered to the selected destination.</p>
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
