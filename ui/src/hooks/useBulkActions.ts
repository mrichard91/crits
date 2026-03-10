import { useMutation, useQueryClient } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'
import type { TLOConfig } from '@/lib/tloConfig'

interface BulkResult {
  success: boolean
  total: number
  succeeded: number
  failed: number
  errors: string[]
}

export function useBulkActions(config: TLOConfig) {
  const queryClient = useQueryClient()

  const onSuccess = () => {
    queryClient.invalidateQueries({ queryKey: [config.gqlList] })
  }

  const updateStatus = useMutation({
    mutationFn: async ({ ids, status }: { ids: string[]; status: string }) => {
      const data = await gqlQuery<{ bulkUpdateStatus: BulkResult }>(
        `mutation($tloType: String!, $ids: [String!]!, $status: String!) {
          bulkUpdateStatus(tloType: $tloType, ids: $ids, status: $status) {
            success total succeeded failed errors
          }
        }`,
        { tloType: config.type, ids, status },
      )
      return data.bulkUpdateStatus
    },
    onSuccess,
  })

  const addToCampaign = useMutation({
    mutationFn: async ({
      ids,
      campaign,
      confidence,
    }: {
      ids: string[]
      campaign: string
      confidence?: string
    }) => {
      const data = await gqlQuery<{ bulkAddToCampaign: BulkResult }>(
        `mutation($tloType: String!, $ids: [String!]!, $campaign: String!, $confidence: String) {
          bulkAddToCampaign(tloType: $tloType, ids: $ids, campaign: $campaign, confidence: $confidence) {
            success total succeeded failed errors
          }
        }`,
        { tloType: config.type, ids, campaign, confidence: confidence ?? 'low' },
      )
      return data.bulkAddToCampaign
    },
    onSuccess,
  })

  const bulkDelete = useMutation({
    mutationFn: async ({ ids }: { ids: string[] }) => {
      const data = await gqlQuery<{ bulkDelete: BulkResult }>(
        `mutation($tloType: String!, $ids: [String!]!) {
          bulkDelete(tloType: $tloType, ids: $ids) {
            success total succeeded failed errors
          }
        }`,
        { tloType: config.type, ids },
      )
      return data.bulkDelete
    },
    onSuccess,
  })

  return { updateStatus, addToCampaign, bulkDelete }
}
