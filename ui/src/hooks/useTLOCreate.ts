import { useMutation, useQueryClient } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'
import type { TLOConfig } from '@/lib/tloConfig'

interface MutationResultData {
  success: boolean
  message: string
  id: string
}

function buildCreateMutation(config: TLOConfig): string {
  if (!config.gqlCreate || !config.createFields) return ''

  const params = config.createFields.map((f) => {
    const gqlType = f.required ? 'String!' : 'String'
    return `$${f.key}: ${gqlType}`
  })

  const args = config.createFields.map((f) => `${f.key}: $${f.key}`)

  return `
    mutation ${config.gqlCreate}(${params.join(', ')}) {
      ${config.gqlCreate}(${args.join(', ')}) {
        success
        message
        id
      }
    }
  `
}

export function useTLOCreate(config: TLOConfig) {
  const queryClient = useQueryClient()
  const mutation = buildCreateMutation(config)

  return useMutation({
    mutationFn: async (variables: Record<string, string>) => {
      if (!config.gqlCreate) throw new Error('Create not supported for this type')
      const data = await gqlQuery<Record<string, MutationResultData>>(mutation, variables)
      const result = data[config.gqlCreate]
      if (!result.success) {
        throw new Error(result.message || 'Creation failed')
      }
      return result
    },
    onSuccess: () => {
      // Invalidate list queries so the new item appears
      queryClient.invalidateQueries({ queryKey: [config.gqlList] })
    },
  })
}
