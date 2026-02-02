import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { graphqlClient } from '@/lib/graphql'

interface User {
  id: string
  username: string
  firstName: string
  lastName: string
  email: string
  organization: string
  role: string
  isActive: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const ME_QUERY = `
  query Me {
    me {
      id
      username
      firstName
      lastName
      email
      organization
      role
      isActive
    }
  }
`

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = async () => {
    try {
      const data = await graphqlClient.request<{ me: User }>(ME_QUERY)
      setUser(data.me)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (username: string, password: string) => {
    // Login via Django endpoint (shared session)
    const response = await fetch('/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password,
        csrfmiddlewaretoken: getCsrfToken(),
      }),
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    // Check if we're authenticated now
    await checkAuth()

    if (!user) {
      throw new Error('Login failed')
    }
  }

  const logout = async () => {
    await fetch('/logout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        csrfmiddlewaretoken: getCsrfToken(),
      }),
      credentials: 'include',
    })
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

function getCsrfToken(): string {
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return value
    }
  }
  return ''
}
