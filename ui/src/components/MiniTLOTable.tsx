import { Link } from 'react-router-dom'
import { Eye } from 'lucide-react'
import type { TLOConfig } from '@/lib/tloConfig'
import { CellValue } from '@/pages/TLOListPage'
import {
  Button,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui'

interface MiniTLOTableProps {
  config: TLOConfig
  items: Record<string, unknown>[]
}

export function MiniTLOTable({ config, items }: MiniTLOTableProps) {
  if (items.length === 0) return null

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {config.columns.map((col) => (
            <TableHead key={col.key}>{col.label}</TableHead>
          ))}
          <TableHead className="w-16">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id as string}>
            {config.columns.map((col) => (
              <TableCell key={col.key}>
                <CellValue col={col} item={item} config={config} />
              </TableCell>
            ))}
            <TableCell>
              <Link to={`${config.route}/${item.id as string}`}>
                <Button variant="ghost" size="sm">
                  <Eye className="h-4 w-4" />
                </Button>
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
