import { useState, useRef, useCallback } from 'react'
import { gqlQuery } from '@/lib/graphql'
import { buildSystemPrompt, buildToolDefinition } from '@/lib/chatSystemPrompt'
import { loadChatSettings } from '@/components/ChatSettings'

/** Messages exposed to the UI and persisted */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/** Tool execution info shown in the UI */
export interface ToolExecution {
  id: string
  query: string
  variables?: Record<string, unknown>
  result?: string
  error?: string
  isExecuting: boolean
}

/**
 * Input items sent to the proxy — matches the OpenAI Responses API input format.
 * The proxy converts to Anthropic format when needed.
 */
type InputItem =
  | { role: string; content: string }
  | {
      type: 'function_call'
      call_id: string
      name: string
      arguments: string
      [k: string]: unknown
    }
  | { type: 'function_call_output'; call_id: string; output: string }
  | { type: 'message'; role: string; content: { type: string; text: string }[] }

interface SSEEvent {
  type: 'text' | 'tool_use' | 'done' | 'error'
  content?: string
  call_id?: string
  name?: string
  input?: Record<string, unknown>
  stop_reason?: string
  output_items?: Record<string, unknown>[]
  message?: string
}

interface ChatSettings {
  provider: string
  model: string
  apiKey: string
}

export function useAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [toolExecutions, setToolExecutions] = useState<ToolExecution[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const loadMessages = useCallback((msgs: ChatMessage[]) => {
    setMessages(msgs)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setToolExecutions([])
  }, [])

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
    setToolExecutions([])
  }, [])

  const sendMessage = useCallback(
    async (userMessage: string): Promise<ChatMessage[]> => {
      const settings = loadChatSettings()
      if (!settings.apiKey) {
        throw new Error('Please configure your API key in Settings')
      }

      const userMsg: ChatMessage = { role: 'user', content: userMessage }
      const newMessages = [...messages, userMsg]
      setMessages([...newMessages, { role: 'assistant', content: '' }])
      setIsStreaming(true)
      setToolExecutions([])

      // Build input items from existing chat messages
      const inputItems: InputItem[] = newMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      try {
        const { displayMessages } = await streamCompletion(
          inputItems,
          settings,
          (text) => {
            setMessages((prev) => {
              const updated = [...prev]
              updated[updated.length - 1] = {
                role: 'assistant',
                content: (updated[updated.length - 1]?.content || '') + text,
              }
              return updated
            })
          },
          (execs) => setToolExecutions(execs),
          abortRef,
        )

        setMessages(displayMessages)
        setIsStreaming(false)
        setToolExecutions([])
        return displayMessages
      } catch (err) {
        setIsStreaming(false)
        setToolExecutions([])
        if ((err as Error).name === 'AbortError') {
          return messages
        }
        const errorMsg: ChatMessage = {
          role: 'assistant',
          content: `Error: ${(err as Error).message}`,
        }
        const withError = [...newMessages, errorMsg]
        setMessages(withError)
        return withError
      }
    },
    [messages],
  )

  return {
    messages,
    isStreaming,
    toolExecutions,
    sendMessage,
    stopStreaming,
    loadMessages,
    clearMessages,
  }
}

interface StreamResult {
  inputItems: InputItem[] // Full input history for potential continuation
  displayMessages: ChatMessage[] // User/assistant messages for display + persistence
}

async function streamCompletion(
  inputItems: InputItem[],
  settings: ChatSettings,
  onText: (text: string) => void,
  onToolExecutions: (execs: ToolExecution[]) => void,
  abortRef: React.MutableRefObject<AbortController | null>,
  depth = 0,
): Promise<StreamResult> {
  if (depth > 10) {
    const display = inputItemsToDisplay(inputItems)
    display.push({ role: 'assistant', content: 'Reached maximum tool call depth.' })
    return { inputItems, displayMessages: display }
  }

  const controller = new AbortController()
  abortRef.current = controller

  const systemPrompt = buildSystemPrompt()
  const tools = [buildToolDefinition()]

  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider: settings.provider,
      apiKey: settings.apiKey,
      model: settings.model,
      input: inputItems,
      systemPrompt,
      tools,
    }),
    signal: controller.signal,
  })

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let assistantText = ''

  // Tool calls collected from tool_use events
  const toolCalls: { call_id: string; name: string; input: Record<string, unknown> }[] = []
  let outputItems: Record<string, unknown>[] = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const raw = line.slice(6)
      let event: SSEEvent
      try {
        event = JSON.parse(raw)
      } catch {
        continue
      }

      if (event.type === 'text' && event.content) {
        assistantText += event.content
        onText(event.content)
      } else if (event.type === 'tool_use') {
        toolCalls.push({
          call_id: event.call_id!,
          name: event.name!,
          input: event.input || {},
        })
      } else if (event.type === 'done') {
        outputItems = event.output_items || []
      } else if (event.type === 'error') {
        throw new Error(event.message || 'Stream error')
      }
    }
  }

  // Tool use: extract function_call items from outputItems (authoritative source)
  const functionCalls = outputItems
    .filter((item) => item.type === 'function_call')
    .map((item) => {
      const fc = item as { call_id: string; name: string; arguments: string }
      let parsedInput: Record<string, unknown> = {}
      try {
        parsedInput = JSON.parse(fc.arguments || '{}')
      } catch {
        /* ignore */
      }
      return { call_id: fc.call_id, name: fc.name, input: parsedInput }
    })

  if (functionCalls.length > 0) {
    // Append the model's output items to input (as the Responses API expects)
    const updatedInput: InputItem[] = [...inputItems, ...(outputItems as InputItem[])]

    // Show tool executions in UI
    const executions: ToolExecution[] = functionCalls.map((fc) => ({
      id: fc.call_id,
      query: (fc.input?.query as string) || '',
      variables: fc.input?.variables as Record<string, unknown> | undefined,
      isExecuting: true,
    }))
    onToolExecutions(executions)

    // Execute each function call and append function_call_output items
    for (let i = 0; i < functionCalls.length; i++) {
      const fc = functionCalls[i]
      const query = (fc.input?.query as string) || ''
      const variables = (fc.input?.variables as Record<string, unknown>) || undefined

      let resultText: string
      try {
        const result = await gqlQuery<Record<string, unknown>>(query, variables)
        resultText = JSON.stringify(result, null, 2)
        executions[i] = { ...executions[i], result: resultText, isExecuting: false }
      } catch (err) {
        resultText = `GraphQL Error: ${(err as Error).message}`
        executions[i] = { ...executions[i], error: resultText, isExecuting: false }
      }
      onToolExecutions([...executions])

      // Append tool result in Responses API format
      updatedInput.push({
        type: 'function_call_output',
        call_id: fc.call_id,
        output: resultText,
      })
    }

    // Recurse with updated input
    return streamCompletion(updatedInput, settings, onText, onToolExecutions, abortRef, depth + 1)
  }

  // Normal completion — extract displayable messages
  const displayMessages = inputItemsToDisplay(inputItems)
  displayMessages.push({ role: 'assistant', content: assistantText })

  return { inputItems: [...inputItems, ...(outputItems as InputItem[])], displayMessages }
}

/** Extract user/assistant text messages from the input items for display + persistence */
function inputItemsToDisplay(items: InputItem[]): ChatMessage[] {
  const result: ChatMessage[] = []
  for (const item of items) {
    if (
      'role' in item &&
      (item.role === 'user' || item.role === 'assistant') &&
      'content' in item &&
      typeof item.content === 'string'
    ) {
      result.push({ role: item.role as 'user' | 'assistant', content: item.content })
    }
  }
  return result
}
