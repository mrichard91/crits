import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Bot,
  Send,
  Square,
  Plus,
  Settings,
  Trash2,
  MessageSquare,
  Database,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAIChat, type ChatMessage, type ToolExecution } from '@/hooks/useAIChat'
import {
  useConversationList,
  useConversation,
  useCreateConversation,
  useSaveMessages,
  useDeleteConversation,
} from '@/hooks/useConversations'
import { ChatSettingsModal, loadChatSettings } from '@/components/ChatSettings'
import ReactMarkdown from 'react-markdown'

export function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [settingsOpen, setSettingsOpen] = useState(false)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const wasStreamingRef = useRef(false)

  const {
    messages,
    isStreaming,
    toolExecutions,
    sendMessage,
    stopStreaming,
    loadMessages,
    clearMessages,
  } = useAIChat()
  const { data: conversations } = useConversationList()
  const { data: activeConversation } = useConversation(id)
  const createConversation = useCreateConversation()
  const saveMessages = useSaveMessages()
  const deleteConversation = useDeleteConversation()

  // Load messages when conversation changes
  useEffect(() => {
    if (activeConversation?.messages) {
      loadMessages(
        activeConversation.messages.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })),
      )
    } else if (!id) {
      clearMessages()
    }
  }, [activeConversation, id, loadMessages, clearMessages])

  // Auto-save when streaming completes
  useEffect(() => {
    if (wasStreamingRef.current && !isStreaming && id && messages.length > 0) {
      saveMessages.mutate({
        conversationId: id,
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
      })
    }
    wasStreamingRef.current = isStreaming
  }, [isStreaming, id, messages, saveMessages])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, toolExecutions])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isStreaming) return

    const settings = loadChatSettings()
    if (!settings.apiKey) {
      setSettingsOpen(true)
      return
    }

    setInput('')

    // Auto-create conversation if needed
    let conversationId = id
    if (!conversationId) {
      try {
        const title = text.slice(0, 60)
        const result = await createConversation.mutateAsync(title)
        conversationId = result.id
        navigate(`/chat/${conversationId}`, { replace: true })
      } catch {
        return
      }
    }

    const finalMessages = await sendMessage(text)

    // Save after send completes
    if (conversationId && finalMessages.length > 0) {
      saveMessages.mutate({
        conversationId,
        messages: finalMessages.map((m) => ({ role: m.role, content: m.content })),
      })
    }
  }, [input, isStreaming, id, sendMessage, createConversation, navigate, saveMessages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    clearMessages()
    navigate('/chat')
  }

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    await deleteConversation.mutateAsync(convId)
    if (id === convId) {
      navigate('/chat')
    }
  }

  return (
    <div className="-m-4 lg:-m-6 flex h-[calc(100vh-3.5rem-2rem)]">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 border-r border-light-border dark:border-dark-border flex flex-col bg-light-bg dark:bg-dark-bg">
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded text-sm font-medium bg-crits-blue text-white hover:bg-crits-blue/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
          {conversations?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => navigate(`/chat/${conv.id}`)}
              className={cn(
                'w-full text-left px-3 py-2 rounded text-sm truncate transition-colors group flex items-center gap-2',
                id === conv.id
                  ? 'bg-crits-blue/10 text-crits-blue font-medium'
                  : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary hover:text-light-text dark:hover:text-dark-text',
              )}
            >
              <MessageSquare className="h-3.5 w-3.5 flex-shrink-0" />
              <span className="truncate flex-1">{conv.title}</span>
              <button
                onClick={(e) => handleDeleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-opacity flex-shrink-0"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </button>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <h1 className="text-lg font-semibold text-light-text dark:text-dark-text">Chat</h1>
          <button
            onClick={() => setSettingsOpen(true)}
            className="p-2 rounded text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
          >
            <Settings className="h-5 w-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-light-text-secondary dark:text-dark-text-secondary">
              <Bot className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">AI Chat</p>
              <p className="text-sm mt-1">Ask questions about your threat intelligence data</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={msg}
              isLast={i === messages.length - 1 && toolExecutions.length === 0}
              isStreaming={isStreaming}
            />
          ))}

          {/* Tool execution status */}
          {toolExecutions.length > 0 && (
            <div className="space-y-2">
              {toolExecutions.map((exec) => (
                <ToolExecutionCard key={exec.id} execution={exec} />
              ))}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-light-border dark:border-dark-border">
          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your threat intelligence data..."
              rows={1}
              className="flex-1 resize-none px-3 py-2 rounded border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm placeholder-light-text-secondary/50 dark:placeholder-dark-text-secondary/50 focus:outline-none focus:ring-1 focus:ring-crits-blue"
            />
            {isStreaming ? (
              <button
                onClick={stopStreaming}
                className="p-2 rounded bg-red-500 text-white hover:bg-red-600 transition-colors flex-shrink-0"
              >
                <Square className="h-5 w-5" />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="p-2 rounded bg-crits-blue text-white hover:bg-crits-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
              >
                <Send className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      <ChatSettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  )
}

function ToolExecutionCard({ execution }: { execution: ToolExecution }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-light-bg-secondary dark:bg-dark-bg-secondary flex items-center justify-center">
        <Database className="h-4 w-4 text-light-text-secondary dark:text-dark-text-secondary" />
      </div>
      <div className="flex-1 min-w-0">
        <button
          onClick={() => !execution.isExecuting && setExpanded(!expanded)}
          className="w-full text-left px-3 py-2 rounded-lg border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg text-sm"
        >
          <div className="flex items-center gap-2">
            {execution.isExecuting ? (
              <Loader2 className="h-3.5 w-3.5 text-crits-blue animate-spin flex-shrink-0" />
            ) : execution.error ? (
              <XCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0" />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
            )}
            <span className="text-light-text-secondary dark:text-dark-text-secondary">
              {execution.isExecuting ? 'Querying CRITs...' : 'Queried CRITs'}
            </span>
          </div>
          <code className="block mt-1 text-xs text-light-text dark:text-dark-text font-mono truncate">
            {execution.query}
          </code>
          {expanded && execution.result && (
            <pre className="mt-2 text-xs text-light-text-secondary dark:text-dark-text-secondary overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
              {execution.result}
            </pre>
          )}
          {expanded && execution.error && (
            <pre className="mt-2 text-xs text-red-500 overflow-x-auto">{execution.error}</pre>
          )}
        </button>
      </div>
    </div>
  )
}

function MessageBubble({
  message,
  isLast,
  isStreaming,
}: {
  message: ChatMessage
  isLast: boolean
  isStreaming: boolean
}) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2 rounded-2xl rounded-br-md bg-crits-blue text-white text-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-light-bg-secondary dark:bg-dark-bg-secondary flex items-center justify-center">
        <Bot className="h-4 w-4 text-light-text-secondary dark:text-dark-text-secondary" />
      </div>
      <div className="max-w-[75%] px-4 py-2 rounded-2xl rounded-bl-md bg-light-bg-secondary dark:bg-dark-bg-secondary text-light-text dark:text-dark-text text-sm">
        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0 prose-pre:my-2 prose-headings:my-2">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {isLast && isStreaming && (
          <span className="inline-block w-2 h-4 bg-crits-blue animate-pulse ml-0.5" />
        )}
      </div>
    </div>
  )
}
