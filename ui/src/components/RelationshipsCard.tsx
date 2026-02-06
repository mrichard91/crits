import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ArrowRightLeft, Plus, Trash2, X, Search } from 'lucide-react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Button,
  Input,
  Spinner,
} from '@/components/ui'
import { TLO_CONFIGS } from '@/lib/tloConfig'
import type { TLOType } from '@/types'
import { truncate } from '@/lib/utils'
import { gqlQuery } from '@/lib/graphql'

interface Relationship {
  objectId: string
  relType: string
  relationship: string
  relConfidence: string
  analyst: string
  displayValue?: string
}

interface RelationshipsCardProps {
  relationships: Relationship[]
  tloType: string
  tloId: string
  onRelationshipChange?: () => void
}

const ADD_RELATIONSHIP_MUTATION = `
  mutation AddRelationship($leftType: String!, $leftId: String!, $rightType: String!, $rightId: String!, $relType: String!, $relConfidence: String, $relReason: String) {
    addRelationship(leftType: $leftType, leftId: $leftId, rightType: $rightType, rightId: $rightId, relType: $relType, relConfidence: $relConfidence, relReason: $relReason) {
      success
      message
    }
  }
`

const REMOVE_RELATIONSHIP_MUTATION = `
  mutation RemoveRelationship($leftType: String!, $leftId: String!, $rightType: String!, $rightId: String!, $relType: String!) {
    removeRelationship(leftType: $leftType, leftId: $leftId, rightType: $rightType, rightId: $rightId, relType: $relType) {
      success
      message
    }
  }
`

const RELATIONSHIP_TYPES_QUERY = `
  query RelationshipTypes {
    relationshipTypes
  }
`

const SEARCH_TLOS_QUERY = `
  query SearchTLOs($tloType: String!, $searchValue: String!, $limit: Int) {
    searchTlos(tloType: $tloType, searchValue: $searchValue, limit: $limit) {
      id
      displayValue
      tloType
    }
  }
`

interface MutationResult {
  success: boolean
  message: string
}

interface TLOSearchResult {
  id: string
  displayValue: string
  tloType: string
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}

function TLOSearchInput({
  targetType,
  selectedId,
  selectedDisplay,
  onSelect,
}: {
  targetType: string
  selectedId: string
  selectedDisplay: string
  onSelect: (id: string, display: string) => void
}) {
  const [searchValue, setSearchValue] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const debouncedSearch = useDebounce(searchValue, 300)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: searchData, isFetching } = useQuery({
    queryKey: ['searchTlos', targetType, debouncedSearch],
    queryFn: () =>
      gqlQuery<{ searchTlos: TLOSearchResult[] }>(SEARCH_TLOS_QUERY, {
        tloType: targetType,
        searchValue: debouncedSearch,
        limit: 10,
      }),
    enabled: !!targetType && debouncedSearch.length >= 2,
  })

  const results = searchData?.searchTlos ?? []

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: globalThis.MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as globalThis.Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Reset search when target type changes
  const prevTargetType = useRef(targetType)
  useEffect(() => {
    if (prevTargetType.current !== targetType) {
      setSearchValue('')
      onSelect('', '')
      prevTargetType.current = targetType
    }
  }, [targetType, onSelect])

  const handleSelect = (result: TLOSearchResult) => {
    onSelect(result.id, result.displayValue)
    setSearchValue('')
    setIsOpen(false)
  }

  const handleClear = () => {
    onSelect('', '')
    setSearchValue('')
  }

  if (!targetType) {
    return (
      <div>
        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
          Target <span className="text-status-error">*</span>
        </label>
        <input
          type="text"
          disabled
          placeholder="Select a TLO type first"
          className="crits-input w-full opacity-50"
        />
      </div>
    )
  }

  if (selectedId) {
    return (
      <div>
        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
          Target <span className="text-status-error">*</span>
        </label>
        <div className="crits-input w-full flex items-center gap-2">
          <span className="truncate flex-1 font-mono text-sm">{selectedDisplay}</span>
          <button
            type="button"
            onClick={handleClear}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative">
      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
        Target <span className="text-status-error">*</span>
      </label>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
        <input
          type="text"
          value={searchValue}
          onChange={(e) => {
            setSearchValue(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={`Search ${TLO_CONFIGS[targetType as TLOType]?.label ?? targetType}...`}
          className="crits-input w-full pl-9"
        />
        {isFetching && <Spinner size="sm" className="absolute right-3 top-1/2 -translate-y-1/2" />}
      </div>

      {isOpen && debouncedSearch.length >= 2 && (
        <div className="absolute z-10 w-full mt-1 bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-md shadow-lg max-h-60 overflow-y-auto">
          {results.length === 0 && !isFetching ? (
            <div className="p-3 text-sm text-light-text-muted dark:text-dark-text-muted">
              No results found
            </div>
          ) : (
            results.map((result) => (
              <button
                key={result.id}
                type="button"
                onClick={() => handleSelect(result)}
                className="w-full text-left px-3 py-2 hover:bg-light-hover dark:hover:bg-dark-hover text-sm font-mono truncate"
              >
                {result.displayValue}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

function AddRelationshipDialog({
  open,
  onClose,
  tloType,
  tloId,
  onSuccess,
}: {
  open: boolean
  onClose: () => void
  tloType: string
  tloId: string
  onSuccess: () => void
}) {
  const [targetType, setTargetType] = useState('')
  const [targetId, setTargetId] = useState('')
  const [targetDisplay, setTargetDisplay] = useState('')
  const [relType, setRelType] = useState('')
  const [confidence, setConfidence] = useState('unknown')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { data: relationshipTypesData } = useQuery({
    queryKey: ['relationshipTypes'],
    queryFn: () => gqlQuery<{ relationshipTypes: string[] }>(RELATIONSHIP_TYPES_QUERY),
    enabled: open,
  })

  const relationshipTypes = relationshipTypesData?.relationshipTypes ?? []

  const addMutation = useMutation({
    mutationFn: (variables: Record<string, string>) =>
      gqlQuery<{ addRelationship: MutationResult }>(ADD_RELATIONSHIP_MUTATION, variables),
    onSuccess: (data) => {
      if (data.addRelationship.success) {
        onSuccess()
        handleClose()
      } else {
        setError(data.addRelationship.message)
      }
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'An error occurred')
    },
  })

  const handleClose = () => {
    setTargetType('')
    setTargetId('')
    setTargetDisplay('')
    setRelType('')
    setConfidence('unknown')
    setReason('')
    setError(null)
    onClose()
  }

  const handleTargetSelect = (id: string, display: string) => {
    setTargetId(id)
    setTargetDisplay(display)
    setError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!targetType) {
      setError('Target TLO Type is required')
      return
    }
    if (!targetId) {
      setError('Please search and select a target')
      return
    }
    if (!relType) {
      setError('Relationship Type is required')
      return
    }

    addMutation.mutate({
      leftType: tloType,
      leftId: tloId,
      rightType: targetType,
      rightId: targetId,
      relType,
      relConfidence: confidence,
      relReason: reason,
    })
  }

  if (!open) return null

  const tloTypeOptions = Object.keys(TLO_CONFIGS)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />
      <div className="relative bg-light-bg dark:bg-dark-bg border border-light-border dark:border-dark-border rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-light-border dark:border-dark-border">
          <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
            Add Relationship
          </h2>
          <button
            onClick={handleClose}
            className="text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
              Target TLO Type <span className="text-status-error">*</span>
            </label>
            <select
              value={targetType}
              onChange={(e) => setTargetType(e.target.value)}
              className="crits-input w-full"
            >
              <option value="">Select type...</option>
              {tloTypeOptions.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <TLOSearchInput
            targetType={targetType}
            selectedId={targetId}
            selectedDisplay={targetDisplay}
            onSelect={handleTargetSelect}
          />

          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-1">
              Relationship Type <span className="text-status-error">*</span>
            </label>
            <select
              value={relType}
              onChange={(e) => setRelType(e.target.value)}
              className="crits-input w-full"
            >
              <option value="">Select relationship type...</option>
              {relationshipTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
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
              <option value="unknown">unknown</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>
          </div>

          <Input
            label="Reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Optional reason for relationship"
          />

          {error && (
            <div className="text-sm text-status-error bg-red-50 dark:bg-red-900/20 p-3 rounded">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="default" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={addMutation.isPending}>
              {addMutation.isPending ? (
                <>
                  <Spinner size="sm" className="mr-2" />
                  Adding...
                </>
              ) : (
                'Add Relationship'
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function RelationshipsCard({
  relationships,
  tloType,
  tloId,
  onRelationshipChange,
}: RelationshipsCardProps) {
  const [dialogOpen, setDialogOpen] = useState(false)

  const removeMutation = useMutation({
    mutationFn: (variables: Record<string, string>) =>
      gqlQuery<{ removeRelationship: MutationResult }>(REMOVE_RELATIONSHIP_MUTATION, variables),
    onSuccess: (data) => {
      if (data.removeRelationship.success) {
        onRelationshipChange?.()
      }
    },
  })

  const handleDelete = (rel: Relationship) => {
    if (!window.confirm(`Remove relationship "${rel.relationship}" to ${rel.relType}?`)) {
      return
    }

    removeMutation.mutate({
      leftType: tloType,
      leftId: tloId,
      rightType: rel.relType,
      rightId: rel.objectId,
      relType: rel.relationship,
    })
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowRightLeft className="h-5 w-5" />
            Relationships ({relationships.length})
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto"
              onClick={() => setDialogOpen(true)}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {relationships.length === 0 ? (
            <p className="text-light-text-muted dark:text-dark-text-muted">No relationships</p>
          ) : (
            <div className="space-y-2">
              {relationships.map((rel, idx) => {
                const cfg = TLO_CONFIGS[rel.relType as TLOType]
                const Icon = cfg?.icon
                const route = cfg?.route
                const href = route ? `${route}/${rel.objectId}` : undefined

                return (
                  <div
                    key={idx}
                    className="flex items-center gap-2 p-2 rounded border border-light-border dark:border-dark-border text-sm"
                  >
                    {Icon && <Icon className={`h-4 w-4 shrink-0 ${cfg.color}`} />}
                    <Badge variant="default" className="shrink-0">
                      {rel.relationship}
                    </Badge>
                    {href ? (
                      <Link
                        to={href}
                        className="text-crits-blue hover:underline font-mono truncate"
                        title={`${rel.relType}: ${rel.displayValue || rel.objectId}`}
                      >
                        {truncate(rel.displayValue || rel.objectId, 40)}
                      </Link>
                    ) : (
                      <span className="font-mono truncate text-light-text-secondary dark:text-dark-text-secondary">
                        {truncate(rel.displayValue || rel.objectId, 40)}
                      </span>
                    )}
                    {rel.relConfidence && rel.relConfidence !== 'unknown' && (
                      <Badge variant="info" className="shrink-0">
                        {rel.relConfidence}
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-auto shrink-0 text-light-text-muted dark:text-dark-text-muted hover:text-status-error"
                      onClick={() => handleDelete(rel)}
                      disabled={removeMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <AddRelationshipDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        tloType={tloType}
        tloId={tloId}
        onSuccess={() => onRelationshipChange?.()}
      />
    </>
  )
}
