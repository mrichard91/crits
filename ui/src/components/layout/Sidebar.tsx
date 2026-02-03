import { NavLink } from 'react-router-dom'
import { LayoutDashboard, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TLO_CONFIGS, TLO_NAV_ORDER } from '@/lib/tloConfig'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onClose} />}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-14 bottom-0 left-0 z-40 w-56',
          'bg-light-bg dark:bg-dark-bg border-r border-light-border dark:border-dark-border',
          'transition-transform duration-200 ease-in-out',
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="absolute top-2 right-2 p-1 lg:hidden text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Navigation */}
        <nav className="p-4 pt-8 lg:pt-4 space-y-1 overflow-y-auto h-full">
          {/* Dashboard link */}
          <NavLink
            to="/"
            end
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors',
                isActive
                  ? 'bg-crits-blue/10 text-crits-blue font-medium'
                  : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-light-text dark:hover:text-dark-text',
              )
            }
          >
            <LayoutDashboard className="h-4 w-4 flex-shrink-0" />
            <span>Dashboard</span>
          </NavLink>

          {/* TLO type links */}
          {TLO_NAV_ORDER.map((type) => {
            const config = TLO_CONFIGS[type]
            const Icon = config.icon
            return (
              <NavLink
                key={config.type}
                to={config.route}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors',
                    isActive
                      ? 'bg-crits-blue/10 text-crits-blue font-medium'
                      : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-light-text dark:hover:text-dark-text',
                  )
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{config.label}</span>
              </NavLink>
            )
          })}
        </nav>
      </aside>
    </>
  )
}
