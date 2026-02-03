import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Layout } from '@/components/layout/Layout'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { TLOListPage } from '@/pages/TLOListPage'
import { TLODetailPage } from '@/pages/TLODetailPage'
import { TLO_CONFIGS } from '@/lib/tloConfig'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-crits-blue"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        {Object.values(TLO_CONFIGS).map((config) => (
          <Route key={config.type} path={config.route.slice(1)}>
            <Route index element={<TLOListPage config={config} />} />
            <Route path=":id" element={<TLODetailPage config={config} />} />
          </Route>
        ))}
      </Route>
    </Routes>
  )
}

export default App
