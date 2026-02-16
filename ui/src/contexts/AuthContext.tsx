import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  username: string
  firstName: string
  lastName: string
  email: string
  organization: string
  roles: string[]
  isActive: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  logout: () => Promise<void>
  refetch: () => Promise<void>
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
      roles
      isActive
    }
  }
`

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ query: ME_QUERY }),
      })
      const json = await response.json()
      if (json.data?.me) {
        setUser(json.data.me)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const logout = async () => {
    try {
      await fetch('/api/graphql', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `mutation { logout { success } }`,
        }),
      })
    } catch {
      // Even if the request fails, clear local state
    }
    setUser(null)
  }

  const refetch = async () => {
    setIsLoading(true)
    await checkAuth()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        logout,
        refetch,
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
