import { Link } from 'react-router-dom'
import { Moon, Sun, User, LogOut, Menu } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()

  return (
    <header className="fixed top-0 left-0 right-0 h-14 z-50 bg-gradient-to-r from-gray-800 to-gray-900 dark:from-gray-900 dark:to-black border-b border-gray-700">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 text-gray-300 hover:text-white"
          >
            <Menu className="h-5 w-5" />
          </button>
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-white">CRITs</span>
            <span className="hidden sm:inline text-xs text-gray-400">
              Collaborative Research Into Threats
            </span>
          </Link>
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
            {theme === 'dark' ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
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
