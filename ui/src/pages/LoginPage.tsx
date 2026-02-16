import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Moon, Sun } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Button, Input, Card, CardContent, Spinner } from '@/components/ui'

const LOGIN_MUTATION = `
  mutation Login($username: String!, $password: String!, $totpPass: String) {
    login(username: $username, password: $password, totpPass: $totpPass) {
      success
      message
      status
      totpSecret
    }
  }
`

interface LoginResponse {
  login: {
    success: boolean
    message: string
    status: string
    totpSecret: string | null
  }
}

export function LoginPage() {
  const { isAuthenticated, isLoading: authLoading, refetch } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totpPass, setTotpPass] = useState('')
  const [showTotp, setShowTotp] = useState(false)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate('/')
    }
  }, [isAuthenticated, authLoading, navigate])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setInfo('')
    setIsSubmitting(true)

    try {
      const res = await fetch('/api/graphql', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: LOGIN_MUTATION,
          variables: {
            username,
            password,
            totpPass: showTotp ? totpPass : null,
          },
        }),
      })

      const json = await res.json()

      if (json.errors?.length) {
        setError(json.errors.map((err: { message: string }) => err.message).join(', '))
        return
      }

      const result = (json.data as LoginResponse['login'] | undefined)
        ? (json.data as { login: LoginResponse['login'] }).login
        : null

      if (!result) {
        setError('Unexpected response from server')
        return
      }

      switch (result.status) {
        case 'login_successful':
          await refetch()
          navigate('/')
          break
        case 'totp_required':
          setShowTotp(true)
          setInfo(result.message)
          break
        case 'no_secret':
          setShowTotp(true)
          setInfo(result.message)
          break
        case 'secret_generated':
          setShowTotp(false)
          setInfo(result.message)
          setPassword('')
          setTotpPass('')
          break
        case 'login_failed':
          setError(result.message)
          break
        default:
          setError(result.message || 'Login failed')
      }
    } catch {
      setError('Network error. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800 p-4">
      {/* Theme toggle */}
      <div className="absolute top-4 right-4">
        <Button variant="ghost" size="sm" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>
      </div>

      {/* Logo and title */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Shield className="h-12 w-12 text-crits-blue" />
          <h1 className="text-4xl font-bold text-light-text dark:text-dark-text">CRITs</h1>
        </div>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          Collaborative Research Into Threats
        </p>
      </div>

      {/* Login card */}
      <Card className="w-full max-w-md">
        <CardContent>
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 text-center">
            Sign In
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Username"
              name="username"
              type="text"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isSubmitting}
            />

            <Input
              label="Password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
            />

            {showTotp && (
              <Input
                label="TOTP Code"
                name="totp"
                type="text"
                autoComplete="one-time-code"
                placeholder="PIN + token"
                value={totpPass}
                onChange={(e) => setTotpPass(e.target.value)}
                disabled={isSubmitting}
              />
            )}

            {error && <p className="text-sm text-status-error">{error}</p>}

            {info && !error && <p className="text-sm text-crits-blue">{info}</p>}

            <Button type="submit" variant="primary" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Spinner size="sm" /> : 'Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-xs text-light-text-muted dark:text-dark-text-muted">
        CRITs - Threat Intelligence Platform
      </p>
    </div>
  )
}
