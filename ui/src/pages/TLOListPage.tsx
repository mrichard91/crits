import { Link, useSearchParams } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight, Eye } from 'lucide-react'
import { useTLOList, useTLOFilterOptions, PAGE_SIZE } from '@/hooks/useTLOList'
import type { TLOConfig, TLOColumnDef, TLOFilterDef } from '@/lib/tloConfig'
import {
  Card,
  CardContent,
  Input,
  Button,
  Badge,
  Spinner,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui'
import { formatDate, truncate } from '@/lib/utils'

interface TLOListPageProps {
  config: TLOConfig
}

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split('.')
  let current: unknown = obj
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    current = (current as Record<string, unknown>)[part]
  }
  return current
}

function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'Analyzed':
      return 'success'
    case 'In Progress':
      return 'warning'
    case 'Deprecated':
      return 'error'
    default:
      return 'default'
  }
}

function CellValue({
  col,
  item,
  config,
}: {
  col: TLOColumnDef
  item: Record<string, unknown>
  config: TLOConfig
}) {
  const raw = getNestedValue(item, col.key)

  if (col.type === 'date') {
    return <span className="text-xs">{raw ? formatDate(raw as string) : '-'}</span>
  }

  if (col.type === 'badge') {
    if (!raw) return <span className="text-light-text-muted dark:text-dark-text-muted">-</span>
    const str = String(raw)
    const variant = col.key === 'status' ? statusVariant(str) : 'info'
    return <Badge variant={variant}>{str}</Badge>
  }

  if (col.type === 'list') {
    const arr = raw as string[] | undefined
    if (!arr?.length) {
      return <span className="text-light-text-muted dark:text-dark-text-muted">-</span>
    }
    return (
      <div className="flex flex-wrap gap-1">
        {arr.slice(0, 2).map((v) => (
          <Badge key={v}>{v}</Badge>
        ))}
        {arr.length > 2 && <Badge>+{arr.length - 2}</Badge>}
      </div>
    )
  }

  const str = raw != null ? String(raw) : '-'
  const display = col.truncate ? truncate(str, col.truncate) : str

  if (col.linkToDetail) {
    return (
      <Link
        to={`${config.route}/${item.id as string}`}
        className={`crits-link ${col.type === 'mono' ? 'font-mono text-sm' : ''}`}
      >
        {display}
      </Link>
    )
  }

  if (col.type === 'mono') {
    return <span className="font-mono text-sm">{display}</span>
  }

  return <>{display}</>
}

function FilterBar({
  config,
  filters,
  onFilterChange,
}: {
  config: TLOConfig
  filters: Record<string, string>
  onFilterChange: (key: string, value: string) => void
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-wrap gap-4">
          {config.filters.map((filterDef) => (
            <FilterInput
              key={filterDef.key}
              filterDef={filterDef}
              value={filters[filterDef.key] || ''}
              onChange={(val) => onFilterChange(filterDef.key, val)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function FilterInput({
  filterDef,
  value,
  onChange,
}: {
  filterDef: TLOFilterDef
  value: string
  onChange: (val: string) => void
}) {
  if (filterDef.type === 'text') {
    return (
      <div className="flex-1 min-w-[200px]">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
          <Input
            placeholder={filterDef.label + '...'}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>
    )
  }

  // Select filter
  return (
    <div className="w-44">
      <SelectFilter filterDef={filterDef} value={value} onChange={onChange} />
    </div>
  )
}

function SelectFilter({
  filterDef,
  value,
  onChange,
}: {
  filterDef: TLOFilterDef
  value: string
  onChange: (val: string) => void
}) {
  // Static options for status and active filters
  const staticOptions: Record<string, string[]> = {
    status: ['New', 'In Progress', 'Analyzed', 'Deprecated'],
    active: ['true', 'false'],
  }

  const isStatic = filterDef.key in staticOptions
  const { data: dynamicOptions } = useTLOFilterOptions(
    isStatic ? undefined : filterDef.optionsQuery,
  )

  const options = isStatic ? staticOptions[filterDef.key] : (dynamicOptions ?? [])

  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="crits-input">
      <option value="">All {filterDef.label}</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  )
}

export function TLOListPage({ config }: TLOListPageProps) {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = parseInt(searchParams.get('page') || '1', 10)

  // Build filters from search params
  const filters: Record<string, string> = {}
  for (const f of config.filters) {
    const val = searchParams.get(f.key)
    if (val) filters[f.key] = val
  }

  const { items, totalCount, isLoading, error } = useTLOList(config, { page, filters })
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE))

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set('page', '1')
    setSearchParams(params)
  }

  const goToPage = (newPage: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(newPage))
    setSearchParams(params)
  }

  const Icon = config.icon

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Icon className={`h-6 w-6 ${config.color}`} />
            {config.label}
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {totalCount.toLocaleString()} total {config.label.toLowerCase()}
          </p>
        </div>
      </div>

      {/* Filters */}
      <FilterBar config={config} filters={filters} onFilterChange={updateFilter} />

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center text-status-error py-12">
              Failed to load {config.label.toLowerCase()}
            </div>
          ) : items.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              No {config.label.toLowerCase()} found
            </div>
          ) : (
            <>
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

              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-light-border dark:border-dark-border">
                <div className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                  Page {page} of {totalPages} ({totalCount} total)
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => goToPage(page - 1)}
                    disabled={page <= 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => goToPage(page + 1)}
                    disabled={page >= totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
