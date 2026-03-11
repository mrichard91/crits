import { useState, useEffect } from 'react'
import { X } from 'lucide-react'

const STORAGE_KEY = 'crits-chat-settings'

export interface ChatSettings {
  provider: 'openai' | 'anthropic'
  model: string
  apiKey: string
}

const DEFAULTS: ChatSettings = {
  provider: 'openai',
  model: 'gpt-4o',
  apiKey: '',
}

const PROVIDER_DEFAULTS: Record<string, string> = {
  openai: 'gpt-4o',
  anthropic: 'claude-sonnet-4-5-20250929',
}

export function loadChatSettings(): ChatSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) }
  } catch {
    // ignore
  }
  return { ...DEFAULTS }
}

export function saveChatSettings(settings: ChatSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

interface ChatSettingsModalProps {
  open: boolean
  onClose: () => void
}

export function ChatSettingsModal({ open, onClose }: ChatSettingsModalProps) {
  const [settings, setSettings] = useState<ChatSettings>(loadChatSettings)

  useEffect(() => {
    if (open) setSettings(loadChatSettings())
  }, [open])

  if (!open) return null

  const handleSave = () => {
    saveChatSettings(settings)
    onClose()
  }

  const handleProviderChange = (provider: 'openai' | 'anthropic') => {
    setSettings((prev) => ({
      ...prev,
      provider,
      model: PROVIDER_DEFAULTS[provider] || prev.model,
    }))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-light-border dark:border-dark-border">
          <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
            Chat Settings
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          {/* Provider */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
              Provider
            </label>
            <div className="flex gap-2">
              {(['openai', 'anthropic'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => handleProviderChange(p)}
                  className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                    settings.provider === p
                      ? 'bg-crits-blue text-white'
                      : 'bg-light-bg-secondary dark:bg-dark-bg-secondary text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                  }`}
                >
                  {p === 'openai' ? 'OpenAI' : 'Anthropic'}
                </button>
              ))}
            </div>
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
              Model
            </label>
            <input
              type="text"
              value={settings.model}
              onChange={(e) => setSettings((s) => ({ ...s, model: e.target.value }))}
              className="w-full px-3 py-2 rounded border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm"
              placeholder={PROVIDER_DEFAULTS[settings.provider]}
            />
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
              API Key
            </label>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => setSettings((s) => ({ ...s, apiKey: e.target.value }))}
              className="w-full px-3 py-2 rounded border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm"
              placeholder={settings.provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
            />
            <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
              Stored locally in your browser. Never sent to the CRITs server.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 border-t border-light-border dark:border-dark-border">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded text-sm font-medium bg-crits-blue text-white hover:bg-crits-blue/90"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
