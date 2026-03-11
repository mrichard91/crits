import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'

interface ConversationSummary {
  id: string
  title: string
  modified: string
}

interface ChatMessage {
  role: string
  content: string
  created?: string
}

interface Conversation {
  id: string
  title: string
  analyst: string
  provider: string
  model: string
  messages: ChatMessage[]
  created: string
  modified: string
}

interface MutationResult {
  success: boolean
  message: string
  id: string
}

export function useConversationList() {
  return useQuery({
    queryKey: ['chatConversations'],
    queryFn: () =>
      gqlQuery<{ chatConversations: ConversationSummary[] }>(
        `query { chatConversations { id title modified } }`,
      ),
    select: (data) => data.chatConversations,
  })
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: ['chatConversation', id],
    queryFn: () =>
      gqlQuery<{ chatConversation: Conversation | null }>(
        `query($id: String!) {
          chatConversation(id: $id) {
            id title analyst provider model
            messages { role content created }
            created modified
          }
        }`,
        { id },
      ),
    select: (data) => data.chatConversation,
    enabled: !!id,
  })
}

export function useCreateConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (title?: string) => {
      const data = await gqlQuery<{ createChatConversation: MutationResult }>(
        `mutation($title: String) {
          createChatConversation(title: $title) { success message id }
        }`,
        { title },
      )
      if (!data.createChatConversation.success) {
        throw new Error(data.createChatConversation.message)
      }
      return data.createChatConversation
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chatConversations'] }),
  })
}

export function useSaveMessages() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({
      conversationId,
      messages,
    }: {
      conversationId: string
      messages: { role: string; content: string }[]
    }) => {
      const data = await gqlQuery<{ saveChatMessages: MutationResult }>(
        `mutation($conversationId: String!, $messages: [ChatMessageInput!]!) {
          saveChatMessages(conversationId: $conversationId, messages: $messages) {
            success message id
          }
        }`,
        { conversationId, messages },
      )
      if (!data.saveChatMessages.success) {
        throw new Error(data.saveChatMessages.message)
      }
      return data.saveChatMessages
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chatConversations'] }),
  })
}

export function useRenameConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, title }: { id: string; title: string }) => {
      const data = await gqlQuery<{ renameChatConversation: MutationResult }>(
        `mutation($id: String!, $title: String!) {
          renameChatConversation(id: $id, title: $title) { success message id }
        }`,
        { id, title },
      )
      if (!data.renameChatConversation.success) {
        throw new Error(data.renameChatConversation.message)
      }
      return data.renameChatConversation
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chatConversations'] }),
  })
}

export function useDeleteConversation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const data = await gqlQuery<{ deleteChatConversation: MutationResult }>(
        `mutation($id: String!) {
          deleteChatConversation(id: $id) { success message id }
        }`,
        { id },
      )
      if (!data.deleteChatConversation.success) {
        throw new Error(data.deleteChatConversation.message)
      }
      return data.deleteChatConversation
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chatConversations'] }),
  })
}
