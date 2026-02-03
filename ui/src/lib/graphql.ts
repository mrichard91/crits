import { GraphQLClient } from 'graphql-request'

export const graphqlClient = new GraphQLClient('/api/graphql', {
  credentials: 'include',
})

// Helper to make typed queries
export async function query<T>(document: string, variables?: Record<string, unknown>): Promise<T> {
  return graphqlClient.request<T>(document, variables)
}

// Raw fetch helper for GraphQL queries (no external dependency)
export async function gqlQuery<T>(
  document: string,
  variables?: Record<string, unknown>,
): Promise<T> {
  const res = await fetch('/api/graphql', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: document, variables }),
  })

  if (!res.ok) {
    throw new Error(`GraphQL request failed: ${res.status} ${res.statusText}`)
  }

  const json = await res.json()

  if (json.errors?.length) {
    throw new Error(json.errors.map((e: { message: string }) => e.message).join(', '))
  }

  return json.data as T
}
