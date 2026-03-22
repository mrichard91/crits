import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Shield, Search, Plus, ChevronDown, ChevronRight, X, Trash2 } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Card, CardContent, Input, Spinner, Badge, Button } from '@/components/ui'

// ── GraphQL ──────────────────────────────────────────────────────────

const ROLES_QUERY = `
  query {
    roles {
      id
      name
      active
      description
      sources {
        name
        read
        write
        tlpRed
        tlpAmber
        tlpGreen
      }
      apiInterface
      scriptInterface
      webInterface
      controlPanelRead
      controlPanelUsersRead
      controlPanelUsersAdd
      controlPanelUsersEdit
      controlPanelRolesRead
      controlPanelRolesEdit
      controlPanelServicesRead
      controlPanelServicesEdit
      controlPanelAuditLogRead
    }
  }
`

const SOURCES_QUERY = `
  query {
    sources {
      name
      active
    }
  }
`

const CREATE_ROLE_MUTATION = `
  mutation CreateRole($name: String!, $description: String) {
    createRole(name: $name, description: $description) {
      success
      message
      id
    }
  }
`

const TOGGLE_ROLE_MUTATION = `
  mutation ToggleRole($id: String!, $active: Boolean!) {
    toggleRole(id: $id, active: $active) {
      success
      message
    }
  }
`

const SET_ROLE_PERMISSION_MUTATION = `
  mutation SetRolePermission($id: String!, $permission: String!, $value: Boolean!) {
    setRolePermission(id: $id, permission: $permission, value: $value) {
      success
      message
    }
  }
`

const ADD_ROLE_SOURCE_MUTATION = `
  mutation AddRoleSource($id: String!, $sourceName: String!, $read: Boolean!, $write: Boolean!, $tlpRed: Boolean!, $tlpAmber: Boolean!, $tlpGreen: Boolean!) {
    addRoleSource(id: $id, sourceName: $sourceName, read: $read, write: $write, tlpRed: $tlpRed, tlpAmber: $tlpAmber, tlpGreen: $tlpGreen) {
      success
      message
    }
  }
`

const REMOVE_ROLE_SOURCE_MUTATION = `
  mutation RemoveRoleSource($id: String!, $sourceName: String!) {
    removeRoleSource(id: $id, sourceName: $sourceName) {
      success
      message
    }
  }
`

// ── Types ────────────────────────────────────────────────────────────

interface SourceACL {
  name: string
  read: boolean
  write: boolean
  tlpRed: boolean
  tlpAmber: boolean
  tlpGreen: boolean
}

interface RoleInfo {
  id: string
  name: string
  active: boolean
  description: string | null
  sources: SourceACL[]
  apiInterface: boolean
  scriptInterface: boolean
  webInterface: boolean
  controlPanelRead: boolean
  controlPanelUsersRead: boolean
  controlPanelUsersAdd: boolean
  controlPanelUsersEdit: boolean
  controlPanelRolesRead: boolean
  controlPanelRolesEdit: boolean
  controlPanelServicesRead: boolean
  controlPanelServicesEdit: boolean
  controlPanelAuditLogRead: boolean
}

interface SourceBasic {
  name: string
  active: boolean
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

// ── Permission definitions ───────────────────────────────────────────

interface PermissionDef {
  key: string
  label: string
}

interface PermissionGroup {
  label: string
  permissions: PermissionDef[]
}

const PERMISSION_GROUPS: PermissionGroup[] = [
  {
    label: 'Interface',
    permissions: [
      { key: 'apiInterface', label: 'API' },
      { key: 'scriptInterface', label: 'Script' },
      { key: 'webInterface', label: 'Web' },
    ],
  },
  {
    label: 'Control Panel',
    permissions: [
      { key: 'controlPanelRead', label: 'Read' },
      { key: 'controlPanelUsersRead', label: 'Users — Read' },
      { key: 'controlPanelUsersAdd', label: 'Users — Add' },
      { key: 'controlPanelUsersEdit', label: 'Users — Edit' },
      { key: 'controlPanelRolesRead', label: 'Roles — Read' },
      { key: 'controlPanelRolesEdit', label: 'Roles — Edit' },
      { key: 'controlPanelServicesRead', label: 'Services — Read' },
      { key: 'controlPanelServicesEdit', label: 'Services — Edit' },
      { key: 'controlPanelAuditLogRead', label: 'Audit Log — Read' },
    ],
  },
]

// Map camelCase GQL field to snake_case backend permission name
function toSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (m) => '_' + m.toLowerCase())
}

// ── Create Role Dialog ───────────────────────────────────────────────

function CreateRoleDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const createRole = useMutation({
    mutationFn: (vars: { name: string; description?: string }) =>
      gqlQuery<{ createRole: { success: boolean; message: string; id: string } }>(
        CREATE_ROLE_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.createRole
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['roles'] })
        setName('')
        setDescription('')
        setResult({ type: 'success', text: res.message })
        setTimeout(() => onClose(), 1000)
      } else {
        setResult({ type: 'error', text: res.message })
      }
    },
    onError: (err) => {
      setResult({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create role',
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
    createRole.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
    })
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">Add Role</h3>
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
              Role Name *
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Analyst, Administrator"
              className="text-sm"
              autoFocus
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Description
            </label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              className="text-sm"
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
            <Button size="sm" type="submit" disabled={createRole.isPending}>
              <Plus className="h-3 w-3 mr-1" />
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Permissions Editor ───────────────────────────────────────────────

function PermissionsEditor({ role }: { role: RoleInfo }) {
  const queryClient = useQueryClient()

  const setPermission = useMutation({
    mutationFn: (vars: { id: string; permission: string; value: boolean }) =>
      gqlQuery<{ setRolePermission: { success: boolean; message: string } }>(
        SET_ROLE_PERMISSION_MUTATION,
        vars,
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['roles'] }),
  })

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
        Permissions
      </h4>
      {PERMISSION_GROUPS.map((group) => (
        <div key={group.label}>
          <h5 className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
            {group.label}
          </h5>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {group.permissions.map((perm) => {
              const value = role[perm.key as keyof RoleInfo] as boolean
              return (
                <label
                  key={perm.key}
                  className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary"
                >
                  <Toggle
                    checked={value}
                    disabled={setPermission.isPending}
                    onChange={(val) =>
                      setPermission.mutate({
                        id: role.id,
                        permission: toSnakeCase(perm.key),
                        value: val,
                      })
                    }
                  />
                  <span>{perm.label}</span>
                </label>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Source ACLs Editor ────────────────────────────────────────────────

function SourceACLsEditor({ role, allSources }: { role: RoleInfo; allSources: SourceBasic[] }) {
  const queryClient = useQueryClient()
  const [addingSource, setAddingSource] = useState('')

  const assignedNames = new Set(role.sources.map((s) => s.name))
  const availableSources = allSources.filter((s) => !assignedNames.has(s.name))

  const addSource = useMutation({
    mutationFn: (vars: {
      id: string
      sourceName: string
      read: boolean
      write: boolean
      tlpRed: boolean
      tlpAmber: boolean
      tlpGreen: boolean
    }) =>
      gqlQuery<{ addRoleSource: { success: boolean; message: string } }>(
        ADD_ROLE_SOURCE_MUTATION,
        vars,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
      setAddingSource('')
    },
  })

  const removeSource = useMutation({
    mutationFn: (vars: { id: string; sourceName: string }) =>
      gqlQuery<{ removeRoleSource: { success: boolean; message: string } }>(
        REMOVE_ROLE_SOURCE_MUTATION,
        vars,
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['roles'] }),
  })

  const handleToggleFlag = (
    acl: SourceACL,
    flag: keyof Omit<SourceACL, 'name'>,
    value: boolean,
  ) => {
    addSource.mutate({
      id: role.id,
      sourceName: acl.name,
      read: flag === 'read' ? value : acl.read,
      write: flag === 'write' ? value : acl.write,
      tlpRed: flag === 'tlpRed' ? value : acl.tlpRed,
      tlpAmber: flag === 'tlpAmber' ? value : acl.tlpAmber,
      tlpGreen: flag === 'tlpGreen' ? value : acl.tlpGreen,
    })
  }

  const handleAddSource = () => {
    if (!addingSource) return
    addSource.mutate({
      id: role.id,
      sourceName: addingSource,
      read: false,
      write: false,
      tlpRed: false,
      tlpAmber: false,
      tlpGreen: false,
    })
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
        Source ACLs
      </h4>

      {role.sources.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-light-border dark:border-dark-border">
                <th className="text-left py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  Source
                </th>
                <th className="text-center py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  Read
                </th>
                <th className="text-center py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  Write
                </th>
                <th className="text-center py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  TLP Red
                </th>
                <th className="text-center py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  TLP Amber
                </th>
                <th className="text-center py-1.5 px-2 font-medium text-light-text-secondary dark:text-dark-text-secondary">
                  TLP Green
                </th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {role.sources.map((acl) => (
                <tr
                  key={acl.name}
                  className="border-b border-light-border/50 dark:border-dark-border/50"
                >
                  <td className="py-1.5 px-2 font-medium text-light-text dark:text-dark-text">
                    {acl.name}
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    <Toggle
                      checked={acl.read}
                      disabled={addSource.isPending}
                      onChange={(val) => handleToggleFlag(acl, 'read', val)}
                    />
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    <Toggle
                      checked={acl.write}
                      disabled={addSource.isPending}
                      onChange={(val) => handleToggleFlag(acl, 'write', val)}
                    />
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    <Toggle
                      checked={acl.tlpRed}
                      disabled={addSource.isPending}
                      onChange={(val) => handleToggleFlag(acl, 'tlpRed', val)}
                    />
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    <Toggle
                      checked={acl.tlpAmber}
                      disabled={addSource.isPending}
                      onChange={(val) => handleToggleFlag(acl, 'tlpAmber', val)}
                    />
                  </td>
                  <td className="py-1.5 px-2 text-center">
                    <Toggle
                      checked={acl.tlpGreen}
                      disabled={addSource.isPending}
                      onChange={(val) => handleToggleFlag(acl, 'tlpGreen', val)}
                    />
                  </td>
                  <td className="py-1.5 px-2">
                    <button
                      onClick={() => removeSource.mutate({ id: role.id, sourceName: acl.name })}
                      disabled={removeSource.isPending}
                      className="p-1 rounded text-light-text-muted dark:text-dark-text-muted hover:text-status-error transition-colors disabled:opacity-50"
                      title={`Remove ${acl.name}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-xs text-light-text-muted dark:text-dark-text-muted">
          No sources assigned to this role
        </p>
      )}

      {availableSources.length > 0 && (
        <div className="flex items-center gap-2">
          <select
            value={addingSource}
            onChange={(e) => setAddingSource(e.target.value)}
            className="flex-1 rounded-md border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-xs text-light-text dark:text-dark-text px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-crits-blue"
          >
            <option value="">Add a source...</option>
            {availableSources.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleAddSource}
            disabled={!addingSource || addSource.isPending}
          >
            <Plus className="h-3 w-3 mr-1" />
            Add
          </Button>
        </div>
      )}
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────

export function RolesPage() {
  const [filter, setFilter] = useState('')
  const [expandedRole, setExpandedRole] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['roles'],
    queryFn: () => gqlQuery<{ roles: RoleInfo[] }>(ROLES_QUERY),
  })

  const { data: sourcesData } = useQuery({
    queryKey: ['sources', 'names'],
    queryFn: () => gqlQuery<{ sources: SourceBasic[] }>(SOURCES_QUERY),
    staleTime: 0, // Always refetch — sources may have been created on another page
  })

  const toggleRole = useMutation({
    mutationFn: (vars: { id: string; active: boolean }) => gqlQuery(TOGGLE_ROLE_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['roles'] }),
  })

  const roles = data?.roles ?? []
  const allSources = sourcesData?.sources ?? []
  const filtered = filter
    ? roles.filter(
        (r) =>
          r.name.toLowerCase().includes(filter.toLowerCase()) ||
          (r.description ?? '').toLowerCase().includes(filter.toLowerCase()),
      )
    : roles

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Shield className="h-6 w-6 text-crits-blue" />
            Roles
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {roles.length} roles configured
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3 mr-1" />
          Add Role
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder="Search roles..."
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
                ? 'You do not have permission to manage roles'
                : 'Failed to load roles'}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              {filter ? 'No roles match your search' : 'No roles found'}
            </div>
          ) : (
            <div className="divide-y divide-light-border dark:divide-dark-border">
              {filtered.map((role) => {
                const isExpanded = expandedRole === role.id

                return (
                  <div key={role.id}>
                    <div className="flex items-center gap-4 px-4 py-3 bg-light-surface dark:bg-dark-surface">
                      <button
                        onClick={() => setExpandedRole(isExpanded ? null : role.id)}
                        className="shrink-0 cursor-pointer text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-light-text dark:text-dark-text">
                            {role.name}
                          </span>
                        </div>
                        {role.description && (
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5 truncate">
                            {role.description}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <Toggle
                          checked={role.active}
                          disabled={toggleRole.isPending}
                          onChange={(active) => toggleRole.mutate({ id: role.id, active })}
                        />
                        <Badge variant={role.active ? 'success' : 'error'}>
                          {role.active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-4 py-4 bg-light-bg-secondary dark:bg-dark-bg-secondary border-t border-light-border dark:border-dark-border space-y-6">
                        <PermissionsEditor role={role} />
                        <SourceACLsEditor role={role} allSources={allSources} />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <CreateRoleDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}
