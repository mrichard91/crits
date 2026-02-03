import { cn } from '@/lib/utils'

export interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        {
          'bg-light-bg-tertiary dark:bg-dark-bg-tertiary text-light-text-secondary dark:text-dark-text-secondary':
            variant === 'default',
          'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300':
            variant === 'success',
          'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300':
            variant === 'warning',
          'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300': variant === 'error',
          'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300': variant === 'info',
        },
        className,
      )}
    >
      {children}
    </span>
  )
}
