import { GraphQLClient } from 'graphql-request'

export const graphqlClient = new GraphQLClient('/api/graphql', {
  credentials: 'include',
})

// Helper to make typed queries
export async function query<T>(
  document: string,
  variables?: Record<string, unknown>
): Promise<T> {
  return graphqlClient.request<T>(document, variables)
}
