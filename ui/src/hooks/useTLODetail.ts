import { useQuery } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'
import type { TLOConfig } from '@/lib/tloConfig'

function buildDetailQuery(config: TLOConfig): string {
  const fields = config.detailQueryFields.join('\n      ')

  return `
    query ${config.gqlSingle}Detail($id: String!) {
      ${config.gqlSingle}(id: $id) {
        ${fields}
      }
    }
  `
}

export interface UseTLODetailResult {
  item: Record<string, unknown> | null
  isLoading: boolean
  error: Error | null
}

export function useTLODetail(config: TLOConfig, id: string): UseTLODetailResult {
  const query = buildDetailQuery(config)

  const { data, isLoading, error } = useQuery({
    queryKey: [config.gqlSingle, id],
    queryFn: () => gqlQuery<Record<string, unknown>>(query, { id }),
    enabled: !!id,
  })

  const item = (data?.[config.gqlSingle] as Record<string, unknown> | undefined) ?? null

  return {
    item,
    isLoading,
    error: error as Error | null,
  }
}
