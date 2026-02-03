import { cn } from '@/lib/utils'

export interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn('crits-card p-4', className)}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: CardProps) {
  return (
    <div className={cn('mb-4 pb-3 border-b border-light-border dark:border-dark-border', className)}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className }: CardProps) {
  return (
    <h3 className={cn('text-lg font-semibold text-light-text dark:text-dark-text', className)}>
      {children}
    </h3>
  )
}

export function CardContent({ children, className }: CardProps) {
  return <div className={cn('', className)}>{children}</div>
}
