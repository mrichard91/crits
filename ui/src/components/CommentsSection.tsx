import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Reply, Pencil, Trash2, Send } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Button } from '@/components/ui'

interface Comment {
  id: string
  comment: string
  analyst: string
  created: string
  editDate: string
  parentDate: string | null
  parentAnalyst: string | null
}

const COMMENTS_QUERY = `
  query Comments($objType: String!, $objId: String!) {
    comments(objType: $objType, objId: $objId) {
      id comment analyst created editDate parentDate parentAnalyst
    }
  }
`

const ADD_COMMENT = `
  mutation AddComment($objType: String!, $objId: String!, $comment: String!, $parentDate: String, $parentAnalyst: String) {
    addComment(objType: $objType, objId: $objId, comment: $comment, parentDate: $parentDate, parentAnalyst: $parentAnalyst) {
      success message
    }
  }
`

const EDIT_COMMENT = `
  mutation EditComment($objType: String!, $objId: String!, $commentDate: String!, $comment: String!) {
    editComment(objType: $objType, objId: $objId, commentDate: $commentDate, comment: $comment) {
      success message
    }
  }
`

const DELETE_COMMENT = `
  mutation DeleteComment($objId: String!, $commentDate: String!) {
    deleteComment(objId: $objId, commentDate: $commentDate) {
      success message
    }
  }
`

function formatCommentDate(iso: string): string {
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

function CommentInput({
  onSubmit,
  isPending,
  placeholder,
  autoFocus,
  onCancel,
}: {
  onSubmit: (text: string) => void
  isPending: boolean
  placeholder: string
  autoFocus?: boolean
  onCancel?: () => void
}) {
  const [text, setText] = useState('')

  const handleSubmit = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSubmit(trimmed)
    setText('')
  }

  return (
    <div className="space-y-2">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        rows={3}
        className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-crits-blue focus:border-crits-blue placeholder:text-light-text-muted dark:placeholder:text-dark-text-muted"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
        }}
      />
      <div className="flex items-center gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={handleSubmit}
          disabled={!text.trim() || isPending}
        >
          <Send className="h-3.5 w-3.5 mr-1" />
          {isPending ? 'Sending...' : 'Comment'}
        </Button>
        {onCancel && (
          <Button variant="default" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </div>
  )
}

interface CommentsSectionProps {
  objType: string
  objId: string
  currentUser: string
}

export function CommentsSection({ objType, objId, currentUser }: CommentsSectionProps) {
  const queryClient = useQueryClient()
  const queryKey = ['comments', objType, objId]

  const [replyingTo, setReplyingTo] = useState<Comment | null>(null)
  const [editingComment, setEditingComment] = useState<Comment | null>(null)
  const [editText, setEditText] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => gqlQuery<{ comments: Comment[] }>(COMMENTS_QUERY, { objType, objId }),
  })

  const comments = data?.comments ?? []

  const invalidate = () => queryClient.invalidateQueries({ queryKey })

  const addMutation = useMutation({
    mutationFn: (vars: { comment: string; parentDate?: string; parentAnalyst?: string }) =>
      gqlQuery<{ addComment: { success: boolean; message: string } }>(ADD_COMMENT, {
        objType,
        objId,
        ...vars,
      }),
    onSuccess: () => {
      invalidate()
      setReplyingTo(null)
    },
  })

  const editMutation = useMutation({
    mutationFn: (vars: { commentDate: string; comment: string }) =>
      gqlQuery<{ editComment: { success: boolean; message: string } }>(EDIT_COMMENT, {
        objType,
        objId,
        ...vars,
      }),
    onSuccess: () => {
      invalidate()
      setEditingComment(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (commentDate: string) =>
      gqlQuery<{ deleteComment: { success: boolean; message: string } }>(DELETE_COMMENT, {
        objId,
        commentDate,
      }),
    onSuccess: () => {
      invalidate()
      setDeleteConfirm(null)
    },
  })

  // Build a tree: top-level comments + replies grouped by parent
  const topLevel = comments.filter((c) => !c.parentDate)
  const replies = comments.filter((c) => c.parentDate)

  const getReplies = (comment: Comment): Comment[] =>
    replies.filter((r) => r.parentDate === comment.created && r.parentAnalyst === comment.analyst)

  const renderComment = (comment: Comment, isReply = false) => {
    const isOwn = comment.analyst === currentUser
    const isEditing = editingComment?.created === comment.created
    const isConfirmingDelete = deleteConfirm === comment.created
    const commentReplies = getReplies(comment)

    return (
      <div
        key={comment.created + comment.analyst}
        className={
          isReply ? 'ml-6 border-l-2 border-light-border dark:border-dark-border pl-4' : ''
        }
      >
        <div className="py-3">
          <div className="flex items-center gap-2 text-xs text-light-text-muted dark:text-dark-text-muted mb-1">
            <span className="font-medium text-light-text dark:text-dark-text">
              {comment.analyst}
            </span>
            <span>{formatCommentDate(comment.created)}</span>
            {comment.editDate !== comment.created && <span className="italic">(edited)</span>}
          </div>

          {isEditing ? (
            <div className="space-y-2">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={3}
                autoFocus
                className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-crits-blue focus:border-crits-blue"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    editMutation.mutate({ commentDate: comment.created, comment: editText })
                  }
                }}
              />
              <div className="flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() =>
                    editMutation.mutate({ commentDate: comment.created, comment: editText })
                  }
                  disabled={!editText.trim() || editMutation.isPending}
                >
                  Save
                </Button>
                <Button variant="default" size="sm" onClick={() => setEditingComment(null)}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-light-text dark:text-dark-text whitespace-pre-wrap">
              {comment.comment}
            </p>
          )}

          {!isEditing && (
            <div className="flex items-center gap-2 mt-1.5">
              <button
                type="button"
                onClick={() => setReplyingTo(comment)}
                className="flex items-center gap-1 text-xs text-light-text-muted dark:text-dark-text-muted hover:text-crits-blue transition-colors"
              >
                <Reply className="h-3 w-3" />
                Reply
              </button>
              {isOwn && (
                <>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingComment(comment)
                      setEditText(comment.comment)
                    }}
                    className="flex items-center gap-1 text-xs text-light-text-muted dark:text-dark-text-muted hover:text-crits-blue transition-colors"
                  >
                    <Pencil className="h-3 w-3" />
                    Edit
                  </button>
                  {isConfirmingDelete ? (
                    <span className="flex items-center gap-1.5 text-xs">
                      <span className="text-status-error">Delete?</span>
                      <button
                        type="button"
                        onClick={() => deleteMutation.mutate(comment.created)}
                        className="text-status-error hover:underline font-medium"
                        disabled={deleteMutation.isPending}
                      >
                        Yes
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteConfirm(null)}
                        className="text-light-text-muted dark:text-dark-text-muted hover:underline"
                      >
                        No
                      </button>
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setDeleteConfirm(comment.created)}
                      className="flex items-center gap-1 text-xs text-light-text-muted dark:text-dark-text-muted hover:text-status-error transition-colors"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </button>
                  )}
                </>
              )}
            </div>
          )}

          {replyingTo?.created === comment.created && (
            <div className="mt-3">
              <CommentInput
                onSubmit={(text) =>
                  addMutation.mutate({
                    comment: text,
                    parentDate: comment.created,
                    parentAnalyst: comment.analyst,
                  })
                }
                isPending={addMutation.isPending}
                placeholder="Write a reply..."
                autoFocus
                onCancel={() => setReplyingTo(null)}
              />
            </div>
          )}
        </div>

        {commentReplies.map((r) => renderComment(r, true))}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-light-text-muted dark:text-dark-text-muted">
        <MessageSquare className="h-4 w-4" />
        Loading comments...
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {topLevel.length === 0 && (
        <p className="text-sm text-light-text-muted dark:text-dark-text-muted py-4">
          No comments yet. Be the first to add one.
        </p>
      )}

      <div className="divide-y divide-light-border dark:divide-dark-border">
        {topLevel.map((c) => renderComment(c))}
      </div>

      <div className="pt-4 border-t border-light-border dark:border-dark-border">
        <CommentInput
          onSubmit={(text) => addMutation.mutate({ comment: text })}
          isPending={addMutation.isPending}
          placeholder="Add a comment..."
        />
      </div>
    </div>
  )
}
