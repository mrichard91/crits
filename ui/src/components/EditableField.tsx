import { useState, useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Check, X } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import type { TLODetailFieldDef } from '@/lib/tloConfig'
import { Button } from '@/components/ui'

const STATUS_OPTIONS = ['New', 'In Progress', 'Analyzed', 'Deprecated']

interface EditableFieldProps {
  field: TLODetailFieldDef
  value: unknown
  gqlUpdate: string
  tloId: string
  queryKey: unknown[]
  children: React.ReactNode
}

export function EditableField({
  field,
  value,
  gqlUpdate,
  tloId,
  queryKey,
  children,
}: EditableFieldProps) {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  // eslint-disable-next-line no-undef
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const selectRef = useRef<HTMLSelectElement>(null)
  const queryClient = useQueryClient()

  const editKey = field.editKey ?? field.key
  const editType = field.editType ?? 'text'

  // Fetch options for select fields
  const { data: optionsData } = useQuery({
    queryKey: ['editOptions', field.editOptionsQuery],
    queryFn: () => gqlQuery<Record<string, string[]>>(`query { ${field.editOptionsQuery} }`),
    enabled: editType === 'select' && !!field.editOptionsQuery,
    staleTime: 60_000,
  })

  const options =
    editType === 'select'
      ? field.editOptionsQuery && optionsData
        ? (optionsData[field.editOptionsQuery] ?? [])
        : field.key === 'status'
          ? STATUS_OPTIONS
          : []
      : []

  const mutation = useMutation({
    mutationFn: (newValue: string) => {
      const query = `mutation($id: String!, $value: String!) { ${gqlUpdate}(id: $id, ${editKey}: $value) { success message } }`
      return gqlQuery<Record<string, { success: boolean; message: string }>>(query, {
        id: tloId,
        value: newValue,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setEditing(false)
    },
  })

  const startEditing = () => {
    setEditValue(value != null ? String(value) : '')
    setEditing(true)
  }

  useEffect(() => {
    if (editing) {
      if (editType === 'textarea') textareaRef.current?.focus()
      else if (editType === 'select') selectRef.current?.focus()
      else inputRef.current?.focus()
    }
  }, [editing, editType])

  const handleSave = () => {
    if (editValue !== String(value ?? '')) {
      mutation.mutate(editValue)
    } else {
      setEditing(false)
    }
  }

  const handleCancel = () => {
    setEditing(false)
    mutation.reset()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel()
    } else if (e.key === 'Enter' && editType !== 'textarea') {
      handleSave()
    }
  }

  if (editing) {
    return (
      <div className="space-y-2">
        {editType === 'textarea' ? (
          <textarea
            ref={textareaRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={4}
            className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-crits-blue focus:border-crits-blue"
          />
        ) : editType === 'select' ? (
          <select
            ref={selectRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-crits-blue focus:border-crits-blue"
          >
            {options.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ) : (
          <input
            ref={inputRef}
            type="text"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-crits-blue focus:border-crits-blue"
          />
        )}
        <div className="flex items-center gap-1.5">
          <Button variant="primary" size="sm" onClick={handleSave} disabled={mutation.isPending}>
            <Check className="h-3.5 w-3.5 mr-1" />
            Save
          </Button>
          <Button variant="default" size="sm" onClick={handleCancel}>
            <X className="h-3.5 w-3.5 mr-1" />
            Cancel
          </Button>
          {mutation.isError && (
            <span className="text-xs text-status-error ml-2">
              {mutation.error instanceof Error ? mutation.error.message : 'Save failed'}
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="group/editable flex items-start gap-1.5 cursor-pointer" onClick={startEditing}>
      <div className="flex-1">{children}</div>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          startEditing()
        }}
        className="opacity-0 group-hover/editable:opacity-100 transition-opacity shrink-0 mt-0.5 p-0.5 rounded hover:bg-light-hover dark:hover:bg-dark-hover text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
        title={`Edit ${field.label}`}
      >
        <Pencil className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}
