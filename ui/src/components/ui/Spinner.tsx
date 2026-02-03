import { cn } from '@/lib/utils'

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={cn(
        'animate-spin rounded-full border-b-2 border-crits-blue',
        {
          'h-4 w-4': size === 'sm',
          'h-8 w-8': size === 'md',
          'h-12 w-12': size === 'lg',
        },
        className
      )}
    />
  )
}

export function LoadingOverlay() {
  return (
    <div className="absolute inset-0 bg-white/50 dark:bg-dark-bg/50 flex items-center justify-center z-10">
      <Spinner size="lg" />
    </div>
  )
}
