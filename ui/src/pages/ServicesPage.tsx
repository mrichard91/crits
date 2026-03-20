import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Wrench, Search, ChevronDown, ChevronRight, Save, RotateCcw, Play, X } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Card, CardContent, Input, Spinner, Badge, Button } from '@/components/ui'

const SERVICES_QUERY = `
  query {
    services {
      name
      version
      description
      enabled
      runOnTriage
      supportedTypes
      isModern
      configOptions {
        key
        value
        default
        description
        configType
        required
        private
      }
    }
  }
`

const TOGGLE_ENABLED_MUTATION = `
  mutation ToggleServiceEnabled($serviceName: String!, $enabled: Boolean!) {
    toggleServiceEnabled(serviceName: $serviceName, enabled: $enabled) {
      success
      message
    }
  }
`

const TOGGLE_TRIAGE_MUTATION = `
  mutation ToggleServiceTriage($serviceName: String!, $runOnTriage: Boolean!) {
    toggleServiceTriage(serviceName: $serviceName, runOnTriage: $runOnTriage) {
      success
      message
    }
  }
`

const UPDATE_CONFIG_MUTATION = `
  mutation UpdateServiceConfig($serviceName: String!, $configJson: String!) {
    updateServiceConfig(serviceName: $serviceName, configJson: $configJson) {
      success
      message
    }
  }
`

const RUN_SERVICE_MUTATION = `
  mutation RunService($serviceName: String!, $objType: String!, $objId: String!) {
    runService(serviceName: $serviceName, objType: $objType, objId: $objId) {
      success
      message
      analysisId
    }
  }
`

const ALL_TLO_TYPES = [
  'Actor',
  'Backdoor',
  'Campaign',
  'Certificate',
  'Domain',
  'Email',
  'Event',
  'Exploit',
  'Indicator',
  'IP',
  'PCAP',
  'RawData',
  'Sample',
  'Screenshot',
  'Signature',
  'Target',
]

interface ConfigOption {
  key: string
  value: string
  default: string
  description: string
  configType: string
  required: boolean
  private: boolean
}

interface ServiceInfo {
  name: string
  version: string
  description: string | null
  enabled: boolean
  runOnTriage: boolean
  supportedTypes: string[] | null
  isModern: boolean
  configOptions: ConfigOption[] | null
}

function Toggle({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean
  onChange: (val: boolean) => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-crits-blue focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${
        checked ? 'bg-crits-blue' : 'bg-light-bg-tertiary dark:bg-dark-bg-tertiary'
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
          checked ? 'translate-x-4' : 'translate-x-0'
        }`}
      />
    </button>
  )
}

function ConfigEditor({ serviceName, options }: { serviceName: string; options: ConfigOption[] }) {
  const queryClient = useQueryClient()
  const [edits, setEdits] = useState<Record<string, string>>({})
  const [saveMessage, setSaveMessage] = useState<{
    type: 'success' | 'error'
    text: string
  } | null>(null)
  const hasEdits = Object.keys(edits).length > 0

  useEffect(() => {
    if (saveMessage?.type === 'success') {
      const timer = setTimeout(() => setSaveMessage(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [saveMessage])

  const updateConfig = useMutation({
    mutationFn: (vars: { serviceName: string; configJson: string }) =>
      gqlQuery<{ updateServiceConfig: { success: boolean; message: string } }>(
        UPDATE_CONFIG_MUTATION,
        vars,
      ),
    onSuccess: (result) => {
      const res = result.updateServiceConfig
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['services'] })
        setEdits({})
        setSaveMessage({ type: 'success', text: res.message || 'Configuration saved' })
      } else {
        setSaveMessage({ type: 'error', text: res.message || 'Validation failed' })
      }
    },
    onError: () => {
      setSaveMessage({ type: 'error', text: 'Failed to save configuration' })
    },
  })

  const handleChange = (key: string, value: string) => {
    const original = options.find((o) => o.key === key)
    if (original && value === original.value) {
      const next = { ...edits }
      delete next[key]
      setEdits(next)
    } else {
      setEdits({ ...edits, [key]: value })
    }
  }

  const handleSave = () => {
    // Client-side validation
    const errors: string[] = []
    for (const [key, val] of Object.entries(edits)) {
      const opt = options.find((o) => o.key === key)
      if (!opt) continue
      if (opt.required && val.trim() === '') {
        errors.push(`'${key}' is required`)
      }
      if (opt.configType === 'int' && val.trim() !== '' && !/^-?\d+$/.test(val.trim())) {
        errors.push(`'${key}' must be an integer`)
      }
    }
    if (errors.length > 0) {
      setSaveMessage({ type: 'error', text: errors.join('; ') })
      return
    }

    // Build the config object with proper types
    const configObj: Record<string, unknown> = {}
    for (const [key, val] of Object.entries(edits)) {
      const opt = options.find((o) => o.key === key)
      if (opt?.configType === 'int') {
        configObj[key] = parseInt(val, 10) || 0
      } else if (opt?.configType === 'bool') {
        configObj[key] = val === 'true'
      } else {
        configObj[key] = val
      }
    }
    updateConfig.mutate({
      serviceName,
      configJson: JSON.stringify(configObj),
    })
  }

  const handleReset = () => {
    setEdits({})
    setSaveMessage(null)
  }

  return (
    <div className="px-4 py-3 bg-light-bg-secondary dark:bg-dark-bg-secondary border-t border-light-border dark:border-dark-border">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
          Configuration
        </h4>
        {hasEdits && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              disabled={updateConfig.isPending}
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
            <Button size="sm" onClick={handleSave} disabled={updateConfig.isPending}>
              <Save className="h-3 w-3 mr-1" />
              Save
            </Button>
          </div>
        )}
      </div>
      <div className="space-y-3">
        {options.map((opt) => {
          const currentVal = edits[opt.key] ?? opt.value
          const isEdited = opt.key in edits

          return (
            <div key={opt.key} className="space-y-1">
              <div className="flex items-center gap-2">
                <label className="text-xs font-mono font-medium text-light-text dark:text-dark-text">
                  {opt.key}
                </label>
                {opt.required && <Badge variant="warning">required</Badge>}
                {opt.private && <Badge variant="error">private</Badge>}
                <Badge variant="default">{opt.configType}</Badge>
              </div>
              {opt.description && (
                <p className="text-xs text-light-text-muted dark:text-dark-text-muted">
                  {opt.description}
                </p>
              )}
              <div className="flex items-center gap-2">
                {opt.configType === 'bool' ? (
                  <div className="flex items-center gap-2">
                    <Toggle
                      checked={currentVal === 'true' || currentVal === 'True'}
                      onChange={(val) => handleChange(opt.key, String(val))}
                    />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      {currentVal === 'true' || currentVal === 'True' ? 'Yes' : 'No'}
                    </span>
                  </div>
                ) : (
                  <Input
                    type={opt.configType === 'int' ? 'number' : opt.private ? 'password' : 'text'}
                    value={currentVal}
                    onChange={(e) => handleChange(opt.key, e.target.value)}
                    className={`text-xs font-mono max-w-lg ${isEdited ? 'ring-2 ring-crits-blue' : ''}`}
                  />
                )}
                {opt.default && currentVal !== opt.default && (
                  <button
                    onClick={() => handleChange(opt.key, opt.default)}
                    className="text-xs text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text whitespace-nowrap"
                    title="Reset to default"
                  >
                    default: {opt.private ? '***' : opt.default}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
      {saveMessage && (
        <p
          className={`text-xs mt-2 ${saveMessage.type === 'success' ? 'text-status-success' : 'text-status-error'}`}
        >
          {saveMessage.text}
        </p>
      )}
    </div>
  )
}

function TestRunDialog({
  service,
  open,
  onClose,
}: {
  service: ServiceInfo
  open: boolean
  onClose: () => void
}) {
  const types = service.supportedTypes ?? []
  const typeOptions = types.includes('all') || types.length === 0 ? ALL_TLO_TYPES : types
  const [objType, setObjType] = useState(typeOptions[0] || 'Sample')
  const [objId, setObjId] = useState('')
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const runService = useMutation({
    mutationFn: (vars: { serviceName: string; objType: string; objId: string }) =>
      gqlQuery<{
        runService: { success: boolean; message: string; analysisId: string }
      }>(RUN_SERVICE_MUTATION, vars),
    onSuccess: (data) => {
      const res = data.runService
      if (res.success) {
        setResult({ type: 'success', text: res.message || 'Service dispatched' })
      } else {
        setResult({ type: 'error', text: res.message || 'Failed to dispatch service' })
      }
    },
    onError: () => {
      setResult({ type: 'error', text: 'Failed to dispatch service' })
    },
  })

  const handleSubmit = () => {
    if (!objId.trim()) {
      setResult({ type: 'error', text: 'Object ID is required' })
      return
    }
    setResult(null)
    runService.mutate({ serviceName: service.name, objType, objId: objId.trim() })
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">
            Test Run: {service.name}
          </h3>
          <button
            onClick={onClose}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-4 py-4 space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              TLO Type
            </label>
            <select
              value={objType}
              onChange={(e) => setObjType(e.target.value)}
              className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-sm text-light-text dark:text-dark-text px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-crits-blue"
            >
              {typeOptions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Object ID
            </label>
            <Input
              placeholder="Enter ObjectId..."
              value={objId}
              onChange={(e) => setObjId(e.target.value)}
              className="text-sm font-mono"
            />
          </div>

          {result && (
            <p
              className={`text-xs ${result.type === 'success' ? 'text-status-success' : 'text-status-error'}`}
            >
              {result.text}
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 px-4 py-3 border-t border-light-border dark:border-dark-border">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} disabled={runService.isPending}>
            <Play className="h-3 w-3 mr-1" />
            Run
          </Button>
        </div>
      </div>
    </div>
  )
}

export function ServicesPage() {
  const [filter, setFilter] = useState('')
  const [expandedService, setExpandedService] = useState<string | null>(null)
  const [testRunService, setTestRunService] = useState<ServiceInfo | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['services'],
    queryFn: () => gqlQuery<{ services: ServiceInfo[] }>(SERVICES_QUERY),
  })

  const toggleEnabled = useMutation({
    mutationFn: (vars: { serviceName: string; enabled: boolean }) =>
      gqlQuery(TOGGLE_ENABLED_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['services'] }),
  })

  const toggleTriage = useMutation({
    mutationFn: (vars: { serviceName: string; runOnTriage: boolean }) =>
      gqlQuery(TOGGLE_TRIAGE_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['services'] }),
  })

  const services = data?.services ?? []
  const filtered = filter
    ? services.filter(
        (s) =>
          s.name.toLowerCase().includes(filter.toLowerCase()) ||
          (s.description ?? '').toLowerCase().includes(filter.toLowerCase()),
      )
    : services

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
          <Wrench className="h-6 w-6 text-crits-blue" />
          Services
        </h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          {services.length} services registered
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder="Filter services..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center text-status-error py-12">Failed to load services</div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              {filter ? 'No services match your filter' : 'No services found'}
            </div>
          ) : (
            <div className="divide-y divide-light-border dark:divide-dark-border">
              {filtered.map((svc) => {
                const isExpanded = expandedService === svc.name
                const configOpts = svc.configOptions ?? []
                const hasConfig = configOpts.length > 0

                return (
                  <div key={svc.name}>
                    <div className="flex items-center gap-4 px-4 py-3 bg-light-surface dark:bg-dark-surface">
                      {/* Expand button */}
                      <button
                        onClick={() =>
                          hasConfig ? setExpandedService(isExpanded ? null : svc.name) : undefined
                        }
                        className={`shrink-0 ${hasConfig ? 'cursor-pointer text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text' : 'cursor-default text-transparent'}`}
                        disabled={!hasConfig}
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>

                      {/* Service info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-light-text dark:text-dark-text">
                            {svc.name}
                          </span>
                          <Badge variant="default">{svc.version}</Badge>
                          {svc.isModern && <Badge variant="info">modern</Badge>}
                        </div>
                        {svc.description && (
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5 truncate">
                            {svc.description}
                          </p>
                        )}
                      </div>

                      {/* Supported types */}
                      <div className="hidden md:flex items-center gap-1 shrink-0">
                        {(svc.supportedTypes ?? []).slice(0, 3).map((t) => (
                          <Badge key={t} variant="default">
                            {t}
                          </Badge>
                        ))}
                        {(svc.supportedTypes ?? []).length > 3 && (
                          <Badge variant="default">+{(svc.supportedTypes ?? []).length - 3}</Badge>
                        )}
                      </div>

                      {/* Test run button */}
                      <button
                        onClick={() => setTestRunService(svc)}
                        className="shrink-0 p-1.5 rounded-md text-light-text-secondary dark:text-dark-text-secondary hover:text-crits-blue hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary transition-colors"
                        title={`Test run ${svc.name}`}
                      >
                        <Play className="h-4 w-4" />
                      </button>

                      {/* Toggles */}
                      <div className="flex items-center gap-6 shrink-0">
                        <label className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          <span>Enabled</span>
                          <Toggle
                            checked={svc.enabled}
                            disabled={toggleEnabled.isPending}
                            onChange={(enabled) =>
                              toggleEnabled.mutate({ serviceName: svc.name, enabled })
                            }
                          />
                        </label>
                        <label className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          <span>Triage</span>
                          <Toggle
                            checked={svc.runOnTriage}
                            disabled={toggleTriage.isPending}
                            onChange={(runOnTriage) =>
                              toggleTriage.mutate({ serviceName: svc.name, runOnTriage })
                            }
                          />
                        </label>
                      </div>
                    </div>

                    {/* Expanded config editor */}
                    {isExpanded && hasConfig && (
                      <ConfigEditor serviceName={svc.name} options={configOpts} />
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {testRunService && (
        <TestRunDialog
          service={testRunService}
          open={true}
          onClose={() => setTestRunService(null)}
        />
      )}
    </div>
  )
}
