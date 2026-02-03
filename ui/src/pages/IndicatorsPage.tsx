import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Target, Search, ChevronLeft, ChevronRight, Eye } from 'lucide-react'
import { graphqlClient } from '@/lib/graphql'
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

const INDICATORS_QUERY = `
  query Indicators($first: Int!, $offset: Int, $indicatorType: String, $status: String) {
    indicators(first: $first, offset: $offset, indicatorType: $indicatorType, status: $status) {
      edges {
        node {
          id
          value
          indicatorType
          status
          confidence
          impact
          created
          modified
          campaigns
        }
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        totalCount
      }
    }
  }
`

interface IndicatorNode {
  id: string
  value: string
  indicatorType: string
  status: string
  confidence: string
  impact: string
  created: string
  modified: string
  campaigns: string[]
}

interface IndicatorsData {
  indicators: {
    edges: Array<{ node: IndicatorNode }>
    pageInfo: {
      hasNextPage: boolean
      hasPreviousPage: boolean
      totalCount: number
    }
  }
}

const PAGE_SIZE = 25

const STATUS_OPTIONS = ['', 'New', 'In Progress', 'Analyzed', 'Deprecated']
const TYPE_OPTIONS = [
  '',
  'Address - ipv4-addr',
  'Address - ipv6-addr',
  'URI - Domain Name',
  'URI - URL',
  'Email Address',
  'Hash - MD5',
  'Hash - SHA1',
  'Hash - SHA256',
]

export function IndicatorsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchValue, setSearchValue] = useState('')

  const page = parseInt(searchParams.get('page') || '1', 10)
  const status = searchParams.get('status') || ''
  const indicatorType = searchParams.get('type') || ''

  const { data, isLoading, error } = useQuery({
    queryKey: ['indicators', page, status, indicatorType],
    queryFn: () =>
      graphqlClient.request<IndicatorsData>(INDICATORS_QUERY, {
        first: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
        status: status || undefined,
        indicatorType: indicatorType || undefined,
      }),
  })

  const totalPages = Math.ceil((data?.indicators.pageInfo.totalCount || 0) / PAGE_SIZE)

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams)
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set('page', '1') // Reset to first page on filter change
    setSearchParams(params)
  }

  const goToPage = (newPage: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', String(newPage))
    setSearchParams(params)
  }

  return (
    <div className="space-y-4">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
            <Target className="h-6 w-6 text-crits-blue" />
            Indicators
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {data?.indicators.pageInfo.totalCount.toLocaleString() || 0} total indicators
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
                <Input
                  placeholder="Search indicators..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Type filter */}
            <div className="w-48">
              <select
                value={indicatorType}
                onChange={(e) => updateFilter('type', e.target.value)}
                className="crits-input"
              >
                <option value="">All Types</option>
                {TYPE_OPTIONS.slice(1).map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Status filter */}
            <div className="w-36">
              <select
                value={status}
                onChange={(e) => updateFilter('status', e.target.value)}
                className="crits-input"
              >
                <option value="">All Status</option>
                {STATUS_OPTIONS.slice(1).map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center text-status-error py-12">
              Failed to load indicators
            </div>
          ) : data?.indicators.edges.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              No indicators found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Value</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Impact</TableHead>
                    <TableHead>Campaigns</TableHead>
                    <TableHead>Modified</TableHead>
                    <TableHead className="w-16">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.indicators.edges.map(({ node }) => (
                    <TableRow key={node.id}>
                      <TableCell>
                        <Link
                          to={`/indicators/${node.id}`}
                          className="crits-link font-mono text-sm"
                        >
                          {truncate(node.value, 50)}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="info">{node.indicatorType}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            node.status === 'Analyzed'
                              ? 'success'
                              : node.status === 'In Progress'
                              ? 'warning'
                              : node.status === 'Deprecated'
                              ? 'error'
                              : 'default'
                          }
                        >
                          {node.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{node.confidence}</TableCell>
                      <TableCell>{node.impact}</TableCell>
                      <TableCell>
                        {node.campaigns.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {node.campaigns.slice(0, 2).map((c) => (
                              <Badge key={c}>{c}</Badge>
                            ))}
                            {node.campaigns.length > 2 && (
                              <Badge>+{node.campaigns.length - 2}</Badge>
                            )}
                          </div>
                        ) : (
                          <span className="text-light-text-muted dark:text-dark-text-muted">
                            -
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs">
                        {formatDate(node.modified)}
                      </TableCell>
                      <TableCell>
                        <Link to={`/indicators/${node.id}`}>
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
                  Page {page} of {totalPages} ({data?.indicators.pageInfo.totalCount} total)
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => goToPage(page - 1)}
                    disabled={!data?.indicators.pageInfo.hasPreviousPage}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => goToPage(page + 1)}
                    disabled={!data?.indicators.pageInfo.hasNextPage}
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
