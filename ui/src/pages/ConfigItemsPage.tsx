import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings2, Search, Plus, Trash2, X } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Card, CardContent, Input, Spinner, Badge, Button } from '@/components/ui'

// ── GraphQL ──────────────────────────────────────────────────────────

const RAW_DATA_TYPES_QUERY = `
  query { rawDataTypes { name active } }
`
const SIGNATURE_TYPES_QUERY = `
  query { signatureTypes { name active } }
`
const SIGNATURE_DEPS_QUERY = `
  query { signatureDependencies { name active } }
`
const ACTIONS_QUERY = `
  query { actions { name active } }
`

const CREATE_CONFIG_ITEM_MUTATION = `
  mutation CreateConfigItem($configType: ConfigTypeEnum!, $name: String!) {
    createConfigItem(configType: $configType, name: $name) {
      success
      message
      id
    }
  }
`

const TOGGLE_CONFIG_ITEM_MUTATION = `
  mutation ToggleConfigItem($configType: ConfigTypeEnum!, $name: String!, $active: Boolean!) {
    toggleConfigItem(configType: $configType, name: $name, active: $active) {
      success
      message
    }
  }
`

const DELETE_CONFIG_ITEM_MUTATION = `
  mutation DeleteConfigItem($configType: ConfigTypeEnum!, $name: String!) {
    deleteConfigItem(configType: $configType, name: $name) {
      success
      message
      deletedId
    }
  }
`

// ── Types ────────────────────────────────────────────────────────────

interface ConfigItem {
  name: string
  active: boolean
}

interface TabDef {
  label: string
  configType: string
  queryKey: string
  query: string
  dataKey: string
}

const TABS: TabDef[] = [
  {
    label: 'Raw Data Types',
    configType: 'RAW_DATA_TYPE',
    queryKey: 'rawDataTypes',
    query: RAW_DATA_TYPES_QUERY,
    dataKey: 'rawDataTypes',
  },
  {
    label: 'Signature Types',
    configType: 'SIGNATURE_TYPE',
    queryKey: 'signatureTypes',
    query: SIGNATURE_TYPES_QUERY,
    dataKey: 'signatureTypes',
  },
  {
    label: 'Signature Dependencies',
    configType: 'SIGNATURE_DEPENDENCY',
    queryKey: 'signatureDependencies',
    query: SIGNATURE_DEPS_QUERY,
    dataKey: 'signatureDependencies',
  },
  {
    label: 'Actions',
    configType: 'ACTION',
    queryKey: 'actions',
    query: ACTIONS_QUERY,
    dataKey: 'actions',
  },
]

// ── Toggle Component ─────────────────────────────────────────────────

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

// ── Create Item Dialog ───────────────────────────────────────────────

function CreateItemDialog({
  open,
  onClose,
  tab,
}: {
  open: boolean
  onClose: () => void
  tab: TabDef
}) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const createItem = useMutation({
    mutationFn: (vars: { configType: string; name: string }) =>
      gqlQuery<{ createConfigItem: { success: boolean; message: string; id: string } }>(
        CREATE_CONFIG_ITEM_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.createConfigItem
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: [tab.queryKey] })
        setName('')
        setResult({ type: 'success', text: res.message })
        setTimeout(() => onClose(), 1000)
      } else {
        setResult({ type: 'error', text: res.message })
      }
    },
    onError: (err) => {
      setResult({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create item',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setResult({ type: 'error', text: 'Name is required' })
      return
    }
    setResult(null)
    createItem.mutate({ configType: tab.configType, name: name.trim() })
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">
            Add {tab.label.replace(/s$/, '')}
          </h3>
          <button
            onClick={onClose}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-4 py-4 space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Name *
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="text-sm"
              autoFocus
            />
          </div>

          {result && (
            <p
              className={`text-xs ${result.type === 'success' ? 'text-status-success' : 'text-status-error'}`}
            >
              {result.text}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button size="sm" type="submit" disabled={createItem.isPending}>
              <Plus className="h-3 w-3 mr-1" />
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Tab Content ──────────────────────────────────────────────────────

function TabContent({ tab, filter }: { tab: TabDef; filter: string }) {
  const queryClient = useQueryClient()
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: [tab.queryKey],
    queryFn: () => gqlQuery<Record<string, ConfigItem[]>>(tab.query),
  })

  const toggleItem = useMutation({
    mutationFn: (vars: { configType: string; name: string; active: boolean }) =>
      gqlQuery(TOGGLE_CONFIG_ITEM_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: [tab.queryKey] }),
  })

  const deleteItem = useMutation({
    mutationFn: (vars: { configType: string; name: string }) =>
      gqlQuery<{ deleteConfigItem: { success: boolean; message: string } }>(
        DELETE_CONFIG_ITEM_MUTATION,
        vars,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tab.queryKey] })
      setConfirmDelete(null)
    },
  })

  const items = data?.[tab.dataKey] ?? []
  const filtered = filter
    ? items.filter((item) => item.name.toLowerCase().includes(filter.toLowerCase()))
    : items

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-status-error py-12">
        {error instanceof Error && error.message.includes('permission')
          ? 'You do not have permission to manage config items'
          : 'Failed to load items'}
      </div>
    )
  }

  if (filtered.length === 0) {
    return (
      <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
        {filter ? 'No items match your search' : 'No items configured'}
      </div>
    )
  }

  return (
    <div className="divide-y divide-light-border dark:divide-dark-border">
      {filtered.map((item) => (
        <div
          key={item.name}
          className="flex items-center gap-4 px-4 py-3 bg-light-surface dark:bg-dark-surface"
        >
          <span className="flex-1 text-sm font-medium text-light-text dark:text-dark-text">
            {item.name}
          </span>

          <div className="flex items-center gap-2 shrink-0">
            <Toggle
              checked={item.active}
              disabled={toggleItem.isPending}
              onChange={(active) =>
                toggleItem.mutate({ configType: tab.configType, name: item.name, active })
              }
            />
            <Badge variant={item.active ? 'success' : 'error'}>
              {item.active ? 'Active' : 'Inactive'}
            </Badge>
          </div>

          {confirmDelete === item.name ? (
            <div className="flex items-center gap-1 shrink-0">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setConfirmDelete(null)}
                className="text-xs px-2 py-1 h-auto"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => deleteItem.mutate({ configType: tab.configType, name: item.name })}
                disabled={deleteItem.isPending}
                className="text-xs px-2 py-1 h-auto text-status-error hover:text-status-error"
              >
                Confirm
              </Button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(item.name)}
              className="shrink-0 p-1.5 rounded-md text-light-text-muted dark:text-dark-text-muted hover:text-status-error transition-colors"
              title={`Delete ${item.name}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────

export function ConfigItemsPage() {
  const [activeTab, setActiveTab] = useState(0)
  const [filter, setFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const tab = TABS[activeTab]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Settings2 className="h-6 w-6 text-crits-blue" />
            Config Items
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            Manage data types, signature types, dependencies, and actions
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3 mr-1" />
          Add Item
        </Button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-light-border dark:border-dark-border">
        {TABS.map((t, i) => (
          <button
            key={t.configType}
            onClick={() => {
              setActiveTab(i)
              setFilter('')
            }}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
              i === activeTab
                ? 'border-crits-blue text-crits-blue'
                : 'border-transparent text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder={`Search ${tab.label.toLowerCase()}...`}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <TabContent tab={tab} filter={filter} />
        </CardContent>
      </Card>

      <CreateItemDialog open={showCreate} onClose={() => setShowCreate(false)} tab={tab} />
    </div>
  )
}
