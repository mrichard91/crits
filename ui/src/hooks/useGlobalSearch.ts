import { useQuery } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'

const SEARCH_QUERY = `
  query Search($query: String!, $types: [String!], $limit: Int) {
    search(query: $query, types: $types, limit: $limit) {
      id
      tloType
      displayValue
      modified
      status
    }
  }
`

export interface SearchResult {
  id: string
  tloType: string
  displayValue: string
  modified: string | null
  status: string
}

interface SearchData {
  search: SearchResult[]
}

export function useGlobalSearch(query: string, types?: string[], limit?: number) {
  const enabled = query.length >= 2

  const { data, isLoading, error } = useQuery({
    queryKey: ['global-search', query, types, limit],
    queryFn: () =>
      gqlQuery<SearchData>(SEARCH_QUERY, {
        query,
        types: types ?? null,
        limit: limit ?? 25,
      }),
    enabled,
    staleTime: 10_000,
  })

  return {
    results: data?.search ?? [],
    isLoading: enabled && isLoading,
    error: error as Error | null,
  }
}
