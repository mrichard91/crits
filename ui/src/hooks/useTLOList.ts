import { useQuery } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'
import type { TLOConfig } from '@/lib/tloConfig'

export const PAGE_SIZE = 25

function buildListQuery(config: TLOConfig, filterKeys: string[]): string {
  const params = ['$limit: Int!', '$offset: Int!']
  const args = ['limit: $limit', 'offset: $offset']

  for (const f of config.filters) {
    if (filterKeys.includes(f.key)) {
      params.push(`$${f.key}: String`)
      args.push(`${f.key}: $${f.key}`)
    }
  }

  const fields = config.listFields.join('\n      ')

  return `
    query ${config.gqlList}List(${params.join(', ')}) {
      ${config.gqlList}(${args.join(', ')}) {
        ${fields}
      }
      ${countCall(config, filterKeys)}
    }
  `
}

function countCall(config: TLOConfig, filterKeys: string[]): string {
  const args: string[] = []
  for (const f of config.filters) {
    if (filterKeys.includes(f.key)) {
      args.push(`${f.key}: $${f.key}`)
    }
  }
  if (args.length === 0) return config.gqlCount
  return `${config.gqlCount}(${args.join(', ')})`
}

export interface UseTLOListParams {
  page: number
  filters: Record<string, string>
}

export interface UseTLOListResult {
  items: Record<string, unknown>[]
  totalCount: number
  isLoading: boolean
  error: Error | null
}

export function useTLOList(config: TLOConfig, params: UseTLOListParams): UseTLOListResult {
  // Only include filters that have values
  const activeFilters: Record<string, string> = {}
  for (const [key, value] of Object.entries(params.filters)) {
    if (value) activeFilters[key] = value
  }

  const activeFilterKeys = Object.keys(activeFilters)
  const query = buildListQuery(config, activeFilterKeys)

  const variables: Record<string, unknown> = {
    limit: PAGE_SIZE,
    offset: (params.page - 1) * PAGE_SIZE,
    ...activeFilters,
  }

  const { data, isLoading, error } = useQuery({
    queryKey: [config.gqlList, params.page, activeFilters],
    queryFn: () => gqlQuery<Record<string, unknown>>(query, variables),
  })

  const items = (data?.[config.gqlList] as Record<string, unknown>[] | undefined) ?? []
  const totalCount = (data?.[config.gqlCount] as number | undefined) ?? 0

  return {
    items,
    totalCount,
    isLoading,
    error: error as Error | null,
  }
}

export function useTLOFilterOptions(queryName: string | undefined) {
  const query = queryName ? `query { ${queryName} }` : ''

  return useQuery({
    queryKey: ['filter-options', queryName],
    queryFn: () => gqlQuery<Record<string, string[]>>(query),
    select: (data) => (queryName ? (data[queryName] ?? []) : []),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    enabled: !!queryName,
  })
}
