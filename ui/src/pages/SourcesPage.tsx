import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Search, Plus, X } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import {
  Card,
  CardContent,
  Input,
  Spinner,
  Badge,
  Button,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui'

// ── GraphQL ──────────────────────────────────────────────────────────

const SOURCES_QUERY = `
  query {
    sources {
      name
      active
      sampleCount
    }
  }
`

const CREATE_SOURCE_MUTATION = `
  mutation CreateSource($name: String!) {
    createSource(name: $name) {
      success
      message
      id
    }
  }
`

const TOGGLE_SOURCE_MUTATION = `
  mutation ToggleSource($name: String!, $active: Boolean!) {
    toggleSource(name: $name, active: $active) {
      success
      message
    }
  }
`

// ── Types ────────────────────────────────────────────────────────────

interface SourceInfo {
  name: string
  active: boolean
  sampleCount: number | null
}

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

// ── Create Source Dialog ─────────────────────────────────────────────

function CreateSourceDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const createSource = useMutation({
    mutationFn: (vars: { name: string }) =>
      gqlQuery<{ createSource: { success: boolean; message: string; id: string } }>(
        CREATE_SOURCE_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.createSource
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['sources'] }) // SourcesPage + RolesPage
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
        text: err instanceof Error ? err.message : 'Failed to create source',
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
    createSource.mutate({ name: name.trim() })
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">Add Source</h3>
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
              Source Name *
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. OSINT, VirusTotal, Internal"
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
            <Button size="sm" type="submit" disabled={createSource.isPending}>
              <Plus className="h-3 w-3 mr-1" />
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────

export function SourcesPage() {
  const [filter, setFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['sources'],
    queryFn: () => gqlQuery<{ sources: SourceInfo[] }>(SOURCES_QUERY),
  })

  const toggleSource = useMutation({
    mutationFn: (vars: { name: string; active: boolean }) => gqlQuery(TOGGLE_SOURCE_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sources'] }),
  })

  const sources = data?.sources ?? []
  const filtered = filter
    ? sources.filter((s) => s.name.toLowerCase().includes(filter.toLowerCase()))
    : sources

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Database className="h-6 w-6 text-crits-blue" />
            Sources
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {sources.length} sources configured
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3 mr-1" />
          Add Source
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder="Search sources..."
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
            <div className="text-center text-status-error py-12">
              {error instanceof Error && error.message.includes('permission')
                ? 'You do not have permission to manage sources'
                : 'Failed to load sources'}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              {filter ? 'No sources match your search' : 'No sources found'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Sample Count</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((source) => (
                    <TableRow key={source.name}>
                      <TableCell>
                        <span className="text-sm font-medium text-light-text dark:text-dark-text">
                          {source.name}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                          {(source.sampleCount ?? 0).toLocaleString()}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Toggle
                            checked={source.active}
                            disabled={toggleSource.isPending}
                            onChange={(active) =>
                              toggleSource.mutate({ name: source.name, active })
                            }
                          />
                          <Badge variant={source.active ? 'success' : 'error'}>
                            {source.active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <CreateSourceDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}
