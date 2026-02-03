import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Target,
  Globe,
  Mail,
  Server,
  FileCode,
  Users,
  Shield,
  Bug,
  HardDrive,
  Image,
  FileText,
  Network,
  Award,
  Crosshair,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/indicators', label: 'Indicators', icon: Target },
  { to: '/domains', label: 'Domains', icon: Globe, disabled: true },
  { to: '/ips', label: 'IPs', icon: Server, disabled: true },
  { to: '/emails', label: 'Emails', icon: Mail, disabled: true },
  { to: '/samples', label: 'Samples', icon: FileCode, disabled: true },
  { to: '/actors', label: 'Actors', icon: Users, disabled: true },
  { to: '/campaigns', label: 'Campaigns', icon: Award, disabled: true },
  { to: '/events', label: 'Events', icon: Shield, disabled: true },
  { to: '/exploits', label: 'Exploits', icon: Bug, disabled: true },
  { to: '/backdoors', label: 'Backdoors', icon: HardDrive, disabled: true },
  { to: '/pcaps', label: 'PCAPs', icon: Network, disabled: true },
  { to: '/raw-data', label: 'Raw Data', icon: FileText, disabled: true },
  { to: '/screenshots', label: 'Screenshots', icon: Image, disabled: true },
  { to: '/signatures', label: 'Signatures', icon: Crosshair, disabled: true },
  { to: '/targets', label: 'Targets', icon: Target, disabled: true },
]

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
          {navItems.map(({ to, label, icon: Icon, disabled }) => (
            <NavLink
              key={to}
              to={disabled ? '#' : to}
              onClick={(e) => {
                if (disabled) e.preventDefault()
                else onClose()
              }}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors',
                  disabled && 'opacity-50 cursor-not-allowed',
                  isActive && !disabled
                    ? 'bg-crits-blue/10 text-crits-blue font-medium'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-light-text dark:hover:text-dark-text',
                )
              }
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span>{label}</span>
              {disabled && (
                <span className="ml-auto text-xs text-light-text-muted dark:text-dark-text-muted">
                  Soon
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
