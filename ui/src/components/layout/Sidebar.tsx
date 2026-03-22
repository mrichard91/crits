import { useState, useEffect, useCallback } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  ChevronRight,
  Tag,
  Wrench,
  X,
  MessageSquare,
  Database,
  Shield,
  Settings2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { TLO_CONFIGS } from '@/lib/tloConfig'
import type { TLOType } from '@/types'
import type { LucideIcon } from 'lucide-react'

// --- Section definitions ---

interface SectionDef {
  key: string
  label: string
  items: TLOType[]
}

const SECTIONS: SectionDef[] = [
  { key: 'observables', label: 'Observables', items: ['Domain', 'IP', 'Email', 'Target'] },
  {
    key: 'threats',
    label: 'Threats',
    items: ['Actor', 'Campaign', 'Event', 'Exploit', 'Backdoor'],
  },
  {
    key: 'data',
    label: 'Data',
    items: ['PCAP', 'RawData', 'Certificate', 'Screenshot', 'Signature'],
  },
]

interface SystemItem {
  label: string
  route: string
  icon: LucideIcon
}

const SYSTEM_ITEMS: SystemItem[] = [
  { label: 'Users', route: '/users', icon: Users },
  { label: 'Roles', route: '/roles', icon: Shield },
  { label: 'Sources', route: '/sources', icon: Database },
  { label: 'Services', route: '/services', icon: Wrench },
  { label: 'Tags', route: '/tags', icon: Tag },
  { label: 'Config', route: '/config-items', icon: Settings2 },
]

// --- localStorage helpers ---

const STORAGE_KEY = 'crits-sidebar-sections'

function loadCollapsed(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveCollapsed(state: Record<string, boolean>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

// --- Shared link styles ---

const linkBase = 'flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors'
const linkActive = 'bg-crits-blue/10 text-crits-blue font-medium'
const linkInactive =
  'text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-light-text dark:hover:text-dark-text'

// --- Sub-components ---

function SidebarLink({
  to,
  icon: Icon,
  label,
  end,
  onNavigate,
}: {
  to: string
  icon: LucideIcon
  label: string
  end?: boolean
  onNavigate: () => void
}) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) => cn(linkBase, isActive ? linkActive : linkInactive)}
    >
      <Icon className="h-4 w-4 flex-shrink-0" />
      <span>{label}</span>
    </NavLink>
  )
}

function SidebarSection({
  label,
  sectionKey,
  collapsed,
  onToggle,
  children,
}: {
  label: string
  sectionKey: string
  collapsed: boolean
  onToggle: (key: string) => void
  children: React.ReactNode
}) {
  return (
    <div>
      <button
        onClick={() => onToggle(sectionKey)}
        className="flex items-center gap-1.5 w-full px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-light-text-secondary/60 dark:text-dark-text-secondary/60 hover:text-light-text-secondary dark:hover:text-dark-text-secondary transition-colors"
      >
        <ChevronRight className={cn('h-3 w-3 transition-transform', !collapsed && 'rotate-90')} />
        {label}
      </button>
      {!collapsed && <div className="space-y-0.5">{children}</div>}
    </div>
  )
}

// --- Main sidebar ---

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation()
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    const saved = loadCollapsed()
    // Default all sections to collapsed if no saved state
    const defaults: Record<string, boolean> = {}
    for (const s of SECTIONS) defaults[s.key] = true
    defaults['system'] = true
    return { ...defaults, ...saved }
  })

  // Auto-expand section containing active route
  useEffect(() => {
    const path = location.pathname

    for (const section of SECTIONS) {
      const hasActive = section.items.some((type) => {
        const route = TLO_CONFIGS[type].route
        return path === route || path.startsWith(route + '/')
      })
      if (hasActive) {
        setCollapsed((prev) => {
          if (prev[section.key] === false) return prev
          const next = { ...prev, [section.key]: false }
          saveCollapsed(next)
          return next
        })
        return
      }
    }

    // Check system section
    const hasSystemActive = SYSTEM_ITEMS.some(
      (item) => path === item.route || path.startsWith(item.route + '/'),
    )
    if (hasSystemActive) {
      setCollapsed((prev) => {
        if (prev['system'] === false) return prev
        const next = { ...prev, system: false }
        saveCollapsed(next)
        return next
      })
    }
  }, [location.pathname])

  const toggle = useCallback((key: string) => {
    setCollapsed((prev) => {
      const next = { ...prev, [key]: !prev[key] }
      saveCollapsed(next)
      return next
    })
  }, [])

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
          {/* Top-level links */}
          <SidebarLink to="/" icon={LayoutDashboard} label="Dashboard" end onNavigate={onClose} />
          <SidebarLink
            to={TLO_CONFIGS.Sample.route}
            icon={TLO_CONFIGS.Sample.icon}
            label={TLO_CONFIGS.Sample.label}
            onNavigate={onClose}
          />
          <SidebarLink
            to={TLO_CONFIGS.Indicator.route}
            icon={TLO_CONFIGS.Indicator.icon}
            label={TLO_CONFIGS.Indicator.label}
            onNavigate={onClose}
          />
          <SidebarLink to="/chat" icon={MessageSquare} label="AI Chat" onNavigate={onClose} />

          {/* Divider */}
          <div className="pt-2" />

          {/* Collapsible TLO sections */}
          {SECTIONS.map((section) => (
            <SidebarSection
              key={section.key}
              label={section.label}
              sectionKey={section.key}
              collapsed={collapsed[section.key] ?? true}
              onToggle={toggle}
            >
              {section.items.map((type) => {
                const config = TLO_CONFIGS[type]
                return (
                  <SidebarLink
                    key={type}
                    to={config.route}
                    icon={config.icon}
                    label={config.label}
                    onNavigate={onClose}
                  />
                )
              })}
            </SidebarSection>
          ))}

          {/* System section */}
          <SidebarSection
            label="System"
            sectionKey="system"
            collapsed={collapsed['system'] ?? true}
            onToggle={toggle}
          >
            {SYSTEM_ITEMS.map((item) => (
              <SidebarLink
                key={item.route}
                to={item.route}
                icon={item.icon}
                label={item.label}
                onNavigate={onClose}
              />
            ))}
          </SidebarSection>
        </nav>
      </aside>
    </>
  )
}
