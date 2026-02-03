import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { X } from 'lucide-react'
import { useTLOCreate } from '@/hooks/useTLOCreate'
import { useTLOFilterOptions } from '@/hooks/useTLOList'
import type { TLOConfig, TLOCreateFieldDef } from '@/lib/tloConfig'
import { Button, Input, Spinner } from '@/components/ui'

interface AddTLODialogProps {
  config: TLOConfig
  open: boolean
  onClose: () => void
}

function CreateFieldInput({
  field,
  value,
  onChange,
}: {
  field: TLOCreateFieldDef
  value: string
  onChange: (val: string) => void
}) {
  if (field.type === 'textarea') {
    return (
      <div>
        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
          {field.label}
          {field.required && <span className="text-status-error ml-1">*</span>}
        </label>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          rows={3}
          className="crits-input w-full"
        />
      </div>
    )
  }

  if (field.type === 'select') {
    return <SelectFieldInput field={field} value={value} onChange={onChange} />
  }

  return (
    <div>
      <Input
        label={field.required ? `${field.label} *` : field.label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder}
      />
    </div>
  )
}

function SelectFieldInput({
  field,
  value,
  onChange,
}: {
  field: TLOCreateFieldDef
  value: string
  onChange: (val: string) => void
}) {
  const { data: options } = useTLOFilterOptions(field.optionsQuery)

  return (
    <div>
      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
        {field.label}
        {field.required && <span className="text-status-error ml-1">*</span>}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="crits-input w-full"
      >
        <option value="">Select {field.label}...</option>
        {(options ?? []).map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  )
}

export function AddTLODialog({ config, open, onClose }: AddTLODialogProps) {
  const navigate = useNavigate()
  const createMutation = useTLOCreate(config)
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  const handleFieldChange = useCallback((key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
    setError(null)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate required fields
    const missingFields = (config.createFields ?? [])
      .filter((f) => f.required && !formData[f.key]?.trim())
      .map((f) => f.label)

    if (missingFields.length > 0) {
      setError(`Required fields: ${missingFields.join(', ')}`)
      return
    }

    // Filter out empty values
    const variables: Record<string, string> = {}
    for (const [key, val] of Object.entries(formData)) {
      if (val.trim()) variables[key] = val.trim()
    }

    try {
      const result = await createMutation.mutateAsync(variables)
      if (result.id) {
        onClose()
        setFormData({})
        navigate(`${config.route}/${result.id}`)
      } else {
        onClose()
        setFormData({})
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const handleClose = () => {
    setFormData({})
    setError(null)
    onClose()
  }

  if (!open || !config.createFields) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />

      {/* Dialog */}
      <div className="relative bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-light-border dark:border-dark-border">
          <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
            Add {config.singular}
          </h2>
          <button
            onClick={handleClose}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {config.createFields.map((field) => (
            <CreateFieldInput
              key={field.key}
              field={field}
              value={formData[field.key] || ''}
              onChange={(val) => handleFieldChange(field.key, val)}
            />
          ))}

          {/* Error */}
          {error && (
            <div className="text-sm text-status-error bg-red-50 dark:bg-red-900/20 p-3 rounded">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="default" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Creating...
                </>
              ) : (
                `Create ${config.singular}`
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
