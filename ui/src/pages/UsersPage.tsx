import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Search, Plus, Pencil, X } from 'lucide-react'
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

const USERS_QUERY = `
  query {
    users {
      id
      username
      email
      firstName
      lastName
      isActive
      isSuperuser
      organization
      roles
      totp
      lastLogin
    }
  }
`

const ROLES_QUERY = `
  query {
    roles {
      id
      name
      active
    }
  }
`

const CREATE_USER_MUTATION = `
  mutation CreateUser($username: String!, $password: String!, $email: String!, $firstName: String!, $lastName: String!, $roles: [String!]) {
    createUser(username: $username, password: $password, email: $email, firstName: $firstName, lastName: $lastName, roles: $roles) {
      success
      message
      id
    }
  }
`

const UPDATE_USER_MUTATION = `
  mutation UpdateUser($id: String!, $email: String, $firstName: String, $lastName: String, $organization: String) {
    updateUser(id: $id, email: $email, firstName: $firstName, lastName: $lastName, organization: $organization) {
      success
      message
    }
  }
`

const TOGGLE_USER_ACTIVE_MUTATION = `
  mutation ToggleUserActive($id: String!, $active: Boolean!) {
    toggleUserActive(id: $id, active: $active) {
      success
      message
    }
  }
`

const SET_USER_ROLES_MUTATION = `
  mutation SetUserRoles($id: String!, $roles: [String!]!) {
    setUserRoles(id: $id, roles: $roles) {
      success
      message
    }
  }
`

const RESET_PASSWORD_MUTATION = `
  mutation ResetUserPassword($id: String!, $newPassword: String!) {
    resetUserPassword(id: $id, newPassword: $newPassword) {
      success
      message
    }
  }
`

// ── Types ────────────────────────────────────────────────────────────

interface UserInfo {
  id: string
  username: string
  email: string | null
  firstName: string | null
  lastName: string | null
  isActive: boolean
  isSuperuser: boolean
  organization: string | null
  roles: string[] | null
  totp: boolean
  lastLogin: string | null
}

interface RoleInfo {
  id: string
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

// ── Create User Dialog ───────────────────────────────────────────────

function CreateUserDialog({
  open,
  onClose,
  roleOptions,
}: {
  open: boolean
  onClose: () => void
  roleOptions: RoleInfo[]
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    firstName: '',
    lastName: '',
    roles: [] as string[],
  })
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const createUser = useMutation({
    mutationFn: (vars: typeof form) =>
      gqlQuery<{ createUser: { success: boolean; message: string; id: string } }>(
        CREATE_USER_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.createUser
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['users'] })
        setForm({ username: '', password: '', email: '', firstName: '', lastName: '', roles: [] })
        setResult({ type: 'success', text: res.message })
        setTimeout(() => onClose(), 1000)
      } else {
        setResult({ type: 'error', text: res.message })
      }
    },
    onError: (err) => {
      setResult({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create user',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.username.trim() || !form.password.trim()) {
      setResult({ type: 'error', text: 'Username and password are required' })
      return
    }
    setResult(null)
    createUser.mutate(form)
  }

  const toggleRole = (roleName: string) => {
    setForm((prev) => ({
      ...prev,
      roles: prev.roles.includes(roleName)
        ? prev.roles.filter((r) => r !== roleName)
        : [...prev.roles, roleName],
    }))
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">Create User</h3>
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
              Username *
            </label>
            <Input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Password *
            </label>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Email
            </label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                First Name
              </label>
              <Input
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                className="text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                Last Name
              </label>
              <Input
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                className="text-sm"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Roles
            </label>
            <div className="flex flex-wrap gap-1.5">
              {roleOptions
                .filter((r) => r.active)
                .map((role) => (
                  <button
                    key={role.id}
                    type="button"
                    onClick={() => toggleRole(role.name)}
                    className={`px-2 py-0.5 rounded text-xs border transition-colors ${
                      form.roles.includes(role.name)
                        ? 'bg-crits-blue text-white border-crits-blue'
                        : 'border-light-border dark:border-dark-border text-light-text-secondary dark:text-dark-text-secondary hover:border-crits-blue'
                    }`}
                  >
                    {role.name}
                  </button>
                ))}
              {roleOptions.filter((r) => r.active).length === 0 && (
                <span className="text-xs text-light-text-muted dark:text-dark-text-muted">
                  No roles available
                </span>
              )}
            </div>
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
            <Button size="sm" type="submit" disabled={createUser.isPending}>
              <Plus className="h-3 w-3 mr-1" />
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Edit User Dialog ─────────────────────────────────────────────────

function EditUserDialog({
  user,
  onClose,
  roleOptions,
}: {
  user: UserInfo
  onClose: () => void
  roleOptions: RoleInfo[]
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    email: user.email ?? '',
    firstName: user.firstName ?? '',
    lastName: user.lastName ?? '',
    organization: user.organization ?? '',
    roles: [...(user.roles ?? [])],
  })
  const [newPassword, setNewPassword] = useState('')
  const [result, setResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [pwResult, setPwResult] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const updateUser = useMutation({
    mutationFn: (vars: {
      id: string
      email: string
      firstName: string
      lastName: string
      organization: string
    }) =>
      gqlQuery<{ updateUser: { success: boolean; message: string } }>(UPDATE_USER_MUTATION, vars),
    onSuccess: (data) => {
      const res = data.updateUser
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['users'] })
        setResult({ type: 'success', text: 'User updated' })
      } else {
        setResult({ type: 'error', text: res.message })
      }
    },
    onError: () => setResult({ type: 'error', text: 'Failed to update user' }),
  })

  const setUserRoles = useMutation({
    mutationFn: (vars: { id: string; roles: string[] }) =>
      gqlQuery<{ setUserRoles: { success: boolean; message: string } }>(
        SET_USER_ROLES_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.setUserRoles
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['users'] })
      } else {
        setResult({ type: 'error', text: res.message })
      }
    },
    onError: () => setResult({ type: 'error', text: 'Failed to update roles' }),
  })

  const resetPassword = useMutation({
    mutationFn: (vars: { id: string; newPassword: string }) =>
      gqlQuery<{ resetUserPassword: { success: boolean; message: string } }>(
        RESET_PASSWORD_MUTATION,
        vars,
      ),
    onSuccess: (data) => {
      const res = data.resetUserPassword
      if (res.success) {
        setNewPassword('')
        setPwResult({ type: 'success', text: 'Password reset successfully' })
      } else {
        setPwResult({ type: 'error', text: res.message })
      }
    },
    onError: () => setPwResult({ type: 'error', text: 'Failed to reset password' }),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    updateUser.mutate({
      id: user.id,
      email: form.email,
      firstName: form.firstName,
      lastName: form.lastName,
      organization: form.organization,
    })
    // Check if roles changed
    const userRoles = user.roles ?? []
    const rolesChanged =
      form.roles.length !== userRoles.length || form.roles.some((r) => !userRoles.includes(r))
    if (rolesChanged) {
      setUserRoles.mutate({ id: user.id, roles: form.roles })
    }
  }

  const handleResetPassword = () => {
    if (!newPassword.trim()) {
      setPwResult({ type: 'error', text: 'Password is required' })
      return
    }
    setPwResult(null)
    resetPassword.mutate({ id: user.id, newPassword })
  }

  const toggleRole = (roleName: string) => {
    setForm((prev) => ({
      ...prev,
      roles: prev.roles.includes(roleName)
        ? prev.roles.filter((r) => r !== roleName)
        : [...prev.roles, roleName],
    }))
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-light-bg dark:bg-dark-bg rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-medium text-light-text dark:text-dark-text">
            Edit User: {user.username}
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
              Email
            </label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                First Name
              </label>
              <Input
                value={form.firstName}
                onChange={(e) => setForm({ ...form, firstName: e.target.value })}
                className="text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                Last Name
              </label>
              <Input
                value={form.lastName}
                onChange={(e) => setForm({ ...form, lastName: e.target.value })}
                className="text-sm"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Organization
            </label>
            <Input
              value={form.organization}
              onChange={(e) => setForm({ ...form, organization: e.target.value })}
              className="text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
              Roles
            </label>
            <div className="flex flex-wrap gap-1.5">
              {roleOptions
                .filter((r) => r.active)
                .map((role) => (
                  <button
                    key={role.id}
                    type="button"
                    onClick={() => toggleRole(role.name)}
                    className={`px-2 py-0.5 rounded text-xs border transition-colors ${
                      form.roles.includes(role.name)
                        ? 'bg-crits-blue text-white border-crits-blue'
                        : 'border-light-border dark:border-dark-border text-light-text-secondary dark:text-dark-text-secondary hover:border-crits-blue'
                    }`}
                  >
                    {role.name}
                  </button>
                ))}
            </div>
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
            <Button
              size="sm"
              type="submit"
              disabled={updateUser.isPending || setUserRoles.isPending}
            >
              Save
            </Button>
          </div>
        </form>

        {/* Reset Password Section */}
        <div className="px-4 py-3 border-t border-light-border dark:border-dark-border">
          <h4 className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider mb-2">
            Reset Password
          </h4>
          <div className="flex items-end gap-2">
            <div className="flex-1 space-y-1">
              <Input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="text-sm"
              />
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleResetPassword}
              disabled={resetPassword.isPending}
            >
              Reset
            </Button>
          </div>
          {pwResult && (
            <p
              className={`text-xs mt-1 ${pwResult.type === 'success' ? 'text-status-success' : 'text-status-error'}`}
            >
              {pwResult.text}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────

export function UsersPage() {
  const [filter, setFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => gqlQuery<{ users: UserInfo[] }>(USERS_QUERY),
  })

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => gqlQuery<{ roles: RoleInfo[] }>(ROLES_QUERY),
  })

  const toggleActive = useMutation({
    mutationFn: (vars: { id: string; active: boolean }) =>
      gqlQuery(TOGGLE_USER_ACTIVE_MUTATION, vars),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const users = data?.users ?? []
  const roles = rolesData?.roles ?? []
  const filtered = filter
    ? users.filter(
        (u) =>
          u.username.toLowerCase().includes(filter.toLowerCase()) ||
          (u.email ?? '').toLowerCase().includes(filter.toLowerCase()),
      )
    : users

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Users className="h-6 w-6 text-crits-blue" />
            Users
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {users.length} users registered
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3 mr-1" />
          Add User
        </Button>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder="Search by username or email..."
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
                ? 'You do not have permission to manage users'
                : 'Failed to load users'}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              {filter ? 'No users match your search' : 'No users found'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Roles</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead className="w-24">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div>
                          <span className="text-sm font-medium text-light-text dark:text-dark-text">
                            {user.username}
                          </span>
                          {user.isSuperuser && (
                            <Badge variant="warning" className="ml-1.5">
                              admin
                            </Badge>
                          )}
                          {user.totp && (
                            <Badge variant="info" className="ml-1">
                              TOTP
                            </Badge>
                          )}
                        </div>
                        {(user.firstName ?? user.lastName) && (
                          <span className="text-xs text-light-text-muted dark:text-dark-text-muted">
                            {user.firstName ?? ''} {user.lastName ?? ''}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                          {user.email || '-'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {(user.roles ?? []).length > 0 ? (
                            (user.roles ?? []).map((role) => (
                              <Badge key={role} variant="default">
                                {role}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-xs text-light-text-muted dark:text-dark-text-muted">
                              None
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Toggle
                            checked={user.isActive}
                            disabled={toggleActive.isPending}
                            onChange={(active) => toggleActive.mutate({ id: user.id, active })}
                          />
                          <Badge variant={user.isActive ? 'success' : 'error'}>
                            {user.isActive ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-light-text-muted dark:text-dark-text-muted">
                          {formatDate(user.lastLogin)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <button
                          onClick={() => setEditingUser(user)}
                          className="p-1.5 rounded-md text-light-text-secondary dark:text-dark-text-secondary hover:text-crits-blue hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary transition-colors"
                          title={`Edit ${user.username}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <CreateUserDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        roleOptions={roles}
      />

      {editingUser && (
        <EditUserDialog
          user={editingUser}
          onClose={() => setEditingUser(null)}
          roleOptions={roles}
        />
      )}
    </div>
  )
}
