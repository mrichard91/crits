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

// Multipart file upload following the GraphQL multipart request spec
// https://github.com/jaydenseric/graphql-multipart-request-spec
export async function gqlUploadMutation<T>(
  document: string,
  variables: Record<string, unknown>,
  files: Record<string, File>,
): Promise<T> {
  // Build the operations JSON with null placeholders for files
  const operationVariables = { ...variables }
  const map: Record<string, string[]> = {}
  let fileIndex = 0

  for (const key of Object.keys(files)) {
    operationVariables[key] = null
    map[String(fileIndex)] = [`variables.${key}`]
    fileIndex++
  }

  const formData = new FormData()
  formData.append('operations', JSON.stringify({ query: document, variables: operationVariables }))
  formData.append('map', JSON.stringify(map))

  let idx = 0
  for (const file of Object.values(files)) {
    formData.append(String(idx), file)
    idx++
  }

  // Do NOT set Content-Type — browser sets it with the correct multipart boundary
  const res = await fetch('/api/graphql', {
    method: 'POST',
    credentials: 'include',
    body: formData,
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
