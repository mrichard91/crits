import { forwardRef, ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center rounded font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-crits-blue-focus focus:ring-offset-2',
          'disabled:opacity-50 disabled:pointer-events-none',
          // Variants
          {
            'border border-light-border dark:border-dark-border bg-light-bg-secondary dark:bg-dark-bg-secondary text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-tertiary dark:hover:bg-dark-bg-tertiary':
              variant === 'default',
            'bg-crits-blue text-white border border-crits-blue hover:bg-crits-blue-hover':
              variant === 'primary',
            'bg-transparent hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary':
              variant === 'ghost',
            'bg-status-error text-white border border-status-error hover:bg-red-600':
              variant === 'danger',
          },
          // Sizes
          {
            'px-2 py-1 text-xs': size === 'sm',
            'px-4 py-2 text-sm': size === 'md',
            'px-6 py-3 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
