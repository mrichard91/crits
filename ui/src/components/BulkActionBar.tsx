import { useState, useEffect, useCallback } from 'react'
import { X, Trash2, Tag, RefreshCw } from 'lucide-react'
import { useBulkActions } from '@/hooks/useBulkActions'
import { useTLOFilterOptions } from '@/hooks/useTLOList'
import type { TLOConfig } from '@/lib/tloConfig'
import { Button, Badge, Spinner } from '@/components/ui'

interface BulkActionBarProps {
  config: TLOConfig
  selectedIds: Set<string>
  onClearSelection: () => void
}

interface FeedbackMessage {
  type: 'success' | 'error'
  text: string
}

type DialogType = 'status' | 'campaign' | 'delete' | null

export function BulkActionBar({ config, selectedIds, onClearSelection }: BulkActionBarProps) {
  const [openDialog, setOpenDialog] = useState<DialogType>(null)
  const [feedback, setFeedback] = useState<FeedbackMessage | null>(null)
  const mutations = useBulkActions(config)

  // Auto-dismiss feedback after 4s
  useEffect(() => {
    if (!feedback) return
    const timer = setTimeout(() => setFeedback(null), 4000)
    return () => clearTimeout(timer)
  }, [feedback])

  const handleResult = useCallback(
    (result: { success: boolean; succeeded: number; failed: number; errors: string[] }) => {
      if (result.success) {
        setFeedback({
          type: 'success',
          text: `Updated ${result.succeeded} ${config.label.toLowerCase()}`,
        })
      } else {
        const detail = result.errors[0] ? `: ${result.errors[0]}` : ''
        setFeedback({
          type: 'error',
          text: `${result.succeeded} succeeded, ${result.failed} failed${detail}`,
        })
      }
      setOpenDialog(null)
      onClearSelection()
    },
    [config.label, onClearSelection],
  )

  if (selectedIds.size === 0) return null

  const ids = Array.from(selectedIds)
  const count = selectedIds.size
  const label = count === 1 ? config.singular : config.label

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-accent-blue/10 border border-accent-blue/20">
        <Badge variant="info">{count} selected</Badge>
        <Button variant="default" size="sm" onClick={() => setOpenDialog('status')}>
          <RefreshCw className="h-3.5 w-3.5 mr-1" />
          Update Status
        </Button>
        <Button variant="default" size="sm" onClick={() => setOpenDialog('campaign')}>
          <Tag className="h-3.5 w-3.5 mr-1" />
          Add to Campaign
        </Button>
        <Button variant="danger" size="sm" onClick={() => setOpenDialog('delete')}>
          <Trash2 className="h-3.5 w-3.5 mr-1" />
          Delete
        </Button>
        <button
          onClick={onClearSelection}
          className="ml-auto text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {feedback && (
        <div
          className={`text-sm px-4 py-2 rounded ${
            feedback.type === 'success'
              ? 'text-status-success bg-green-50 dark:bg-green-900/20'
              : 'text-status-error bg-red-50 dark:bg-red-900/20'
          }`}
        >
          {feedback.text}
        </div>
      )}

      {openDialog === 'status' && (
        <StatusDialog
          count={count}
          label={label}
          isPending={mutations.updateStatus.isPending}
          onClose={() => setOpenDialog(null)}
          onApply={async (status) => {
            const result = await mutations.updateStatus.mutateAsync({ ids, status })
            handleResult(result)
          }}
        />
      )}

      {openDialog === 'campaign' && (
        <CampaignDialog
          count={count}
          label={label}
          isPending={mutations.addToCampaign.isPending}
          onClose={() => setOpenDialog(null)}
          onApply={async (campaign, confidence) => {
            const result = await mutations.addToCampaign.mutateAsync({ ids, campaign, confidence })
            handleResult(result)
          }}
        />
      )}

      {openDialog === 'delete' && (
        <DeleteDialog
          count={count}
          label={label}
          isPending={mutations.bulkDelete.isPending}
          onClose={() => setOpenDialog(null)}
          onConfirm={async () => {
            const result = await mutations.bulkDelete.mutateAsync({ ids })
            handleResult(result)
          }}
        />
      )}
    </div>
  )
}

// --- Status Dialog ---

function StatusDialog({
  count,
  label,
  isPending,
  onClose,
  onApply,
}: {
  count: number
  label: string
  isPending: boolean
  onClose: () => void
  onApply: (status: string) => Promise<void>
}) {
  const [status, setStatus] = useState('')
  const statuses = ['New', 'In Progress', 'Analyzed', 'Deprecated']

  return (
    <DialogShell title={`Update Status for ${count} ${label}`} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
            New Status
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="crits-input w-full"
          >
            <option value="">Select status...</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="default" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button variant="primary" disabled={!status || isPending} onClick={() => onApply(status)}>
            {isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Applying...
              </>
            ) : (
              'Apply'
            )}
          </Button>
        </div>
      </div>
    </DialogShell>
  )
}

// --- Campaign Dialog ---

function CampaignDialog({
  count,
  label,
  isPending,
  onClose,
  onApply,
}: {
  count: number
  label: string
  isPending: boolean
  onClose: () => void
  onApply: (campaign: string, confidence: string) => Promise<void>
}) {
  const [campaign, setCampaign] = useState('')
  const [confidence, setConfidence] = useState('low')
  const { data: campaigns } = useTLOFilterOptions('campaignNames')

  return (
    <DialogShell title={`Add ${count} ${label} to Campaign`} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
            Campaign
          </label>
          <select
            value={campaign}
            onChange={(e) => setCampaign(e.target.value)}
            className="crits-input w-full"
          >
            <option value="">Select campaign...</option>
            {(campaigns ?? []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
            Confidence
          </label>
          <select
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
            className="crits-input w-full"
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="default" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!campaign || isPending}
            onClick={() => onApply(campaign, confidence)}
          >
            {isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Applying...
              </>
            ) : (
              'Apply'
            )}
          </Button>
        </div>
      </div>
    </DialogShell>
  )
}

// --- Delete Dialog ---

function DeleteDialog({
  count,
  label,
  isPending,
  onClose,
  onConfirm,
}: {
  count: number
  label: string
  isPending: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
}) {
  return (
    <DialogShell title={`Delete ${count} ${label}`} onClose={onClose}>
      <div className="space-y-4">
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
          Are you sure you want to delete {count} {label.toLowerCase()}? This cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="default" onClick={onClose} disabled={isPending}>
            Cancel
          </Button>
          <Button variant="danger" disabled={isPending} onClick={onConfirm}>
            {isPending ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </Button>
        </div>
      </div>
    </DialogShell>
  )
}

// --- Shared dialog shell (matches AddTLODialog pattern) ---

function DialogShell({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b border-light-border dark:border-dark-border">
          <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">{title}</h2>
          <button
            onClick={onClose}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}
