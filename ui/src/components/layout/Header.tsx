import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Moon, Sun, User, LogOut, Menu, Search } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { useGlobalSearch } from '@/hooks/useGlobalSearch'
import { TLO_CONFIGS } from '@/lib/tloConfig'
import type { TLOType } from '@/types'
import { Button, Badge, Spinner } from '@/components/ui'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [searchInput, setSearchInput] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [showResults, setShowResults] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)
  const blurTimeoutRef = useRef<number>(0)

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const { results, isLoading } = useGlobalSearch(debouncedQuery)

  const handleResultClick = (tloType: string, id: string) => {
    const config = TLO_CONFIGS[tloType as TLOType]
    if (config) {
      navigate(`${config.route}/${id}`)
    }
    setSearchInput('')
    setDebouncedQuery('')
    setShowResults(false)
  }

  const handleBlur = () => {
    blurTimeoutRef.current = window.setTimeout(() => setShowResults(false), 200)
  }

  const handleFocus = () => {
    clearTimeout(blurTimeoutRef.current)
    if (debouncedQuery.length >= 2) {
      setShowResults(true)
    }
  }

  // Show results when we have a valid query
  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      setShowResults(true)
    } else {
      setShowResults(false)
    }
  }, [debouncedQuery])

  return (
    <header className="fixed top-0 left-0 right-0 h-14 z-50 bg-gradient-to-r from-gray-800 to-gray-900 dark:from-gray-900 dark:to-black border-b border-gray-700">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <button onClick={onMenuClick} className="lg:hidden p-2 text-gray-300 hover:text-white">
            <Menu className="h-5 w-5" />
          </button>
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-white">CRITs</span>
            <span className="hidden sm:inline text-xs text-gray-400">
              Collaborative Research Into Threats
            </span>
          </Link>
        </div>

        {/* Center section — Global search */}
        <div ref={searchRef} className="hidden md:flex relative flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search all objects..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onFocus={handleFocus}
              onBlur={handleBlur}
              className="w-full pl-10 pr-3 py-1.5 rounded-md bg-gray-700 border border-gray-600 text-gray-200 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-crits-blue focus:border-transparent"
            />
            {isLoading && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Spinner size="sm" />
              </div>
            )}
          </div>

          {/* Search results dropdown */}
          {showResults && debouncedQuery.length >= 2 && (
            <div className="absolute top-full mt-1 w-full bg-gray-800 border border-gray-600 rounded-md shadow-lg max-h-80 overflow-y-auto z-50">
              {results.length === 0 && !isLoading ? (
                <div className="px-4 py-3 text-sm text-gray-400">No results found</div>
              ) : (
                results.map((result) => {
                  const config = TLO_CONFIGS[result.tloType as TLOType]
                  if (!config) return null
                  const Icon = config.icon

                  return (
                    <button
                      key={`${result.tloType}-${result.id}`}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleResultClick(result.tloType, result.id)}
                      className="w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-700 transition-colors"
                    >
                      <Icon className={`h-4 w-4 flex-shrink-0 ${config.color}`} />
                      <span className="text-sm text-gray-200 truncate flex-1">
                        {result.displayValue}
                      </span>
                      <Badge variant="info">{config.singular}</Badge>
                    </button>
                  )
                })
              )}
            </div>
          )}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            className="text-gray-300 hover:text-white hover:bg-gray-700"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* User menu */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2 text-gray-300">
                <User className="h-4 w-4" />
                <span className="text-sm">{user.username}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-gray-300 hover:text-white hover:bg-gray-700"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
