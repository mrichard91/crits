import { cn } from '@/lib/utils'

export interface TableProps {
  children: React.ReactNode
  className?: string
}

export function Table({ children, className }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className={cn('crits-table', className)}>{children}</table>
    </div>
  )
}

export function TableHeader({ children, className }: TableProps) {
  return <thead className={cn('', className)}>{children}</thead>
}

export function TableBody({ children, className }: TableProps) {
  return <tbody className={cn('', className)}>{children}</tbody>
}

export function TableRow({ children, className }: TableProps) {
  return <tr className={cn('', className)}>{children}</tr>
}

export function TableHead({ children, className }: TableProps) {
  return <th className={cn('', className)}>{children}</th>
}

export function TableCell({ children, className }: TableProps) {
  return <td className={cn('', className)}>{children}</td>
}
