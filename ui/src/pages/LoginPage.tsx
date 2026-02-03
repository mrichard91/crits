import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Moon, Sun } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Button, Card, CardContent } from '@/components/ui'

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  // If already authenticated, go to dashboard
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/')
    }
  }, [isAuthenticated, isLoading, navigate])

  const handleLogin = () => {
    // Redirect to Django login with next=/app/ to come back here after auth
    window.location.href = '/login/?next=/app/'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-crits-blue"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800 p-4">
      {/* Theme toggle */}
      <div className="absolute top-4 right-4">
        <Button variant="ghost" size="sm" onClick={toggleTheme}>
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Logo and title */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Shield className="h-12 w-12 text-crits-blue" />
          <h1 className="text-4xl font-bold text-light-text dark:text-dark-text">
            CRITs
          </h1>
        </div>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          Collaborative Research Into Threats
        </p>
      </div>

      {/* Login card */}
      <Card className="w-full max-w-md">
        <CardContent className="text-center">
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4">
            Welcome to CRITs
          </h2>
          <p className="text-light-text-secondary dark:text-dark-text-secondary mb-6">
            Sign in with your CRITs account to access the threat intelligence platform.
          </p>
          <Button
            variant="primary"
            className="w-full"
            onClick={handleLogin}
          >
            Sign In
          </Button>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-xs text-light-text-muted dark:text-dark-text-muted">
        CRITs - Threat Intelligence Platform
      </p>
    </div>
  )
}
