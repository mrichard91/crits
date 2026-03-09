import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, Zap, MessageSquare } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'

interface Comment {
  comment: string
  analyst: string
  created: string
}

interface Action {
  actionType: string
  analyst: string
  performedDate: string | null
  active: string
  reason: string
  date: string | null
}

interface TimelineEntry {
  type: 'creation' | 'action' | 'comment'
  date: string
  analyst: string
  description: string
}

const COMMENTS_QUERY = `
  query Comments($objType: String!, $objId: String!) {
    comments(objType: $objType, objId: $objId) {
      comment analyst created
    }
  }
`

function formatTimelineDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

interface ActivityTimelineProps {
  item: Record<string, unknown>
  objType: string
  objId: string
}

export function ActivityTimeline({ item, objType, objId }: ActivityTimelineProps) {
  const { data: commentsData } = useQuery({
    queryKey: ['comments', objType, objId],
    queryFn: () => gqlQuery<{ comments: Comment[] }>(COMMENTS_QUERY, { objType, objId }),
  })

  const entries = useMemo(() => {
    const timeline: TimelineEntry[] = []

    // 1. Creation event
    const created = item.created as string | undefined
    if (created) {
      timeline.push({
        type: 'creation',
        date: created,
        analyst: (item.analyst as string) ?? '',
        description: 'Created',
      })
    }

    // 2. Actions from the TLO
    const actions = (item.actions as Action[]) ?? []
    for (const action of actions) {
      const actionDate = action.performedDate ?? action.date
      if (!actionDate) continue
      const parts = [action.actionType]
      if (action.reason) parts.push(`- ${action.reason}`)
      timeline.push({
        type: 'action',
        date: actionDate,
        analyst: action.analyst,
        description: parts.join(' '),
      })
    }

    // 3. Comments
    const comments = commentsData?.comments ?? []
    for (const comment of comments) {
      timeline.push({
        type: 'comment',
        date: comment.created,
        analyst: comment.analyst,
        description: `Commented: ${truncate(comment.comment, 80)}`,
      })
    }

    // Sort reverse-chronological
    timeline.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    return timeline
  }, [item, commentsData])

  if (entries.length === 0) {
    return (
      <p className="text-sm text-light-text-muted dark:text-dark-text-muted py-4">
        No activity recorded.
      </p>
    )
  }

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-3 top-2 bottom-2 w-px bg-light-border dark:bg-dark-border" />

      <div className="space-y-0">
        {entries.map((entry, idx) => {
          const Icon =
            entry.type === 'creation' ? Calendar : entry.type === 'action' ? Zap : MessageSquare

          const iconColor =
            entry.type === 'creation'
              ? 'text-status-success'
              : entry.type === 'action'
                ? 'text-amber-500'
                : 'text-crits-blue'

          return (
            <div key={idx} className="relative flex items-start gap-3 py-2.5 pl-0">
              <div
                className={`relative z-10 flex items-center justify-center w-6 h-6 rounded-full bg-light-surface dark:bg-dark-surface border border-light-border dark:border-dark-border ${iconColor}`}
              >
                <Icon className="h-3 w-3" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-light-text dark:text-dark-text">{entry.description}</p>
                <div className="flex items-center gap-2 text-xs text-light-text-muted dark:text-dark-text-muted mt-0.5">
                  {entry.analyst && <span>{entry.analyst}</span>}
                  <span>{formatTimelineDate(entry.date)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
