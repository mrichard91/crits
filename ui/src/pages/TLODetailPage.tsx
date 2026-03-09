import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQueryClient, useQuery, useMutation } from '@tanstack/react-query'
import {
  ArrowLeft,
  Calendar,
  ChevronDown,
  ChevronRight,
  Clock,
  MessageSquare,
  Plus,
  User,
  Shield,
  Tag,
  Activity,
  FileText,
  FileCode,
  Info,
  Wrench,
  X,
} from 'lucide-react'
import { useTLODetail } from '@/hooks/useTLODetail'
import type { TLOConfig, TLODetailFieldDef } from '@/lib/tloConfig'
import { Card, CardContent, Badge, Spinner, Button } from '@/components/ui'
import { formatDate } from '@/lib/utils'
import { gqlQuery } from '@/lib/graphql'
import { RelationshipsCard } from '@/components/RelationshipsCard'
import { SampleHashCard } from '@/components/SampleHashCard'
import { SampleToolsCard } from '@/components/SampleToolsCard'
import { SampleServicesCard } from '@/components/SampleServicesCard'
import { EditableField } from '@/components/EditableField'
import { CommentsSection } from '@/components/CommentsSection'
import { ActivityTimeline } from '@/components/ActivityTimeline'

interface TLODetailPageProps {
  config: TLOConfig
}

function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split('.')
  let current: unknown = obj
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    current = (current as Record<string, unknown>)[part]
  }
  return current
}

function statusVariant(status: string): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'Analyzed':
      return 'success'
    case 'In Progress':
      return 'warning'
    case 'Deprecated':
      return 'error'
    default:
      return 'default'
  }
}

function FieldValue({ field, item }: { field: TLODetailFieldDef; item: Record<string, unknown> }) {
  const raw = getNestedValue(item, field.key)

  if (raw == null || raw === '') {
    return (
      <span className="text-light-text-muted dark:text-dark-text-muted">
        {field.type === 'list' ? 'None' : '-'}
      </span>
    )
  }

  switch (field.type) {
    case 'date':
      return (
        <span className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          {formatDate(raw as string)}
        </span>
      )
    case 'badge': {
      const str = String(raw)
      const variant = field.key === 'status' ? statusVariant(str) : 'info'
      return <Badge variant={variant}>{str}</Badge>
    }
    case 'mono':
      return <span className="font-mono text-sm break-all">{String(raw)}</span>
    case 'pre':
      return <p className="whitespace-pre-wrap">{String(raw)}</p>
    case 'list': {
      const arr = raw as string[]
      if (!arr.length) {
        return <span className="text-light-text-muted dark:text-dark-text-muted">None</span>
      }
      return (
        <div className="flex flex-wrap gap-2">
          {arr.map((v) => (
            <Badge key={v} variant="info">
              {v}
            </Badge>
          ))}
        </div>
      )
    }
    default:
      return <>{String(raw)}</>
  }
}

interface SourceInstance {
  method: string
  reference: string
  date: string
  analyst: string
}

interface Source {
  name: string
  instances: SourceInstance[]
}

interface Relationship {
  objectId: string
  relType: string
  relationship: string
  relConfidence: string
  analyst: string
  displayValue?: string
}

function formatCompactDate(dateStr: string | undefined | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

/* ── Collapsible sidebar section ─────────────────────────────────── */

function SidebarSection({
  icon: IconComponent,
  label,
  count,
  defaultOpen,
  children,
  onAdd,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  count: number
  defaultOpen?: boolean
  children: React.ReactNode
  onAdd?: () => void
}) {
  const [open, setOpen] = useState(defaultOpen ?? count > 0)

  return (
    <div className="border-b border-light-border dark:border-dark-border last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full py-2.5 px-3 text-sm font-medium text-light-text dark:text-dark-text hover:bg-light-hover dark:hover:bg-dark-hover transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        )}
        <IconComponent className="h-4 w-4 shrink-0" />
        <span className="flex-1 text-left">{label}</span>
        <span className="flex items-center gap-1 shrink-0">
          {onAdd && (
            <span
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation()
                onAdd()
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.stopPropagation()
                  onAdd()
                }
              }}
              className="inline-flex items-center justify-center h-5 w-5 rounded hover:bg-light-border dark:hover:bg-dark-border text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text transition-colors"
              title={`Add ${label.toLowerCase()}`}
            >
              <Plus className="h-3.5 w-3.5" />
            </span>
          )}
          <Badge variant="default" className="text-xs px-1.5 py-0">
            {count}
          </Badge>
        </span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  )
}

/* ── Tag management ──────────────────────────────────────────────── */

const UPDATE_TAGS_MUTATION = `
  mutation UpdateBucketList($tloType: String!, $tloId: String!, $tags: [String!]!) {
    updateBucketList(tloType: $tloType, tloId: $tloId, tags: $tags) {
      success
      message
    }
  }
`

const TAG_NAMES_QUERY = `query { tagNames }`

function TagsSection({
  tags,
  tloType,
  tloId,
  onTagsChange,
}: {
  tags: string[]
  tloType: string
  tloId: string
  onTagsChange: () => void
}) {
  const [inputValue, setInputValue] = useState('')
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: tagNamesData } = useQuery({
    queryKey: ['tagNames'],
    queryFn: () => gqlQuery<{ tagNames: string[] }>(TAG_NAMES_QUERY),
    staleTime: 60_000,
  })
  const allTagNames = tagNamesData?.tagNames ?? []

  const mutation = useMutation({
    mutationFn: (newTags: string[]) =>
      gqlQuery<{ updateBucketList: { success: boolean; message: string } }>(UPDATE_TAGS_MUTATION, {
        tloType,
        tloId,
        tags: newTags,
      }),
    onSuccess: () => onTagsChange(),
    onError: (err) => console.error('Failed to update tags:', err),
  })

  // Filter suggestions: match input, exclude already-applied tags
  const suggestions =
    inputValue.trim().length > 0
      ? allTagNames.filter(
          (name) => name.toLowerCase().includes(inputValue.toLowerCase()) && !tags.includes(name),
        )
      : []

  const addTag = (tag: string) => {
    const trimmed = tag.trim()
    if (!trimmed || tags.includes(trimmed)) return
    mutation.mutate([...tags, trimmed])
    setInputValue('')
    setHighlightIndex(-1)
    setDropdownOpen(false)
  }

  const removeTag = (tag: string) => {
    mutation.mutate(tags.filter((t) => t !== tag))
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!dropdownOpen) return
    function handleClickOutside(event: globalThis.MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as globalThis.Node)) {
        setDropdownOpen(false)
        setHighlightIndex(-1)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [dropdownOpen])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex((prev) => Math.min(prev + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex((prev) => Math.max(prev - 1, -1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (highlightIndex >= 0 && highlightIndex < suggestions.length) {
        addTag(suggestions[highlightIndex])
      } else {
        addTag(inputValue)
      }
    } else if (e.key === 'Escape') {
      setDropdownOpen(false)
      setHighlightIndex(-1)
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <div
        className="flex flex-wrap items-center gap-1.5 rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface px-2 py-1.5 focus-within:ring-1 focus-within:ring-crits-blue focus-within:border-crits-blue transition-colors cursor-text"
        onClick={() => inputRef.current?.focus()}
      >
        <Tag className="h-3.5 w-3.5 shrink-0 text-light-text-muted dark:text-dark-text-muted" />
        {tags.map((tag) => (
          <Link
            key={tag}
            to={`/tags/${encodeURIComponent(tag)}`}
            className="inline-flex items-center gap-1 rounded-full bg-crits-blue/10 text-crits-blue px-2 py-0.5 text-xs font-medium hover:bg-crits-blue/20 transition-colors"
          >
            {tag}
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                removeTag(tag)
              }}
              className="inline-flex items-center justify-center h-3.5 w-3.5 rounded-full hover:bg-crits-blue/30 transition-colors"
              title={`Remove tag "${tag}"`}
            >
              <X className="h-2.5 w-2.5" />
            </button>
          </Link>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value)
            setHighlightIndex(-1)
            setDropdownOpen(true)
          }}
          onFocus={() => setDropdownOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={tags.length === 0 ? 'Add tags…' : ''}
          className="flex-1 min-w-[60px] bg-transparent text-xs text-light-text dark:text-dark-text placeholder:text-light-text-muted dark:placeholder:text-dark-text-muted outline-none py-0.5"
        />
      </div>
      {dropdownOpen && suggestions.length > 0 && (
        <div className="absolute z-10 left-0 right-0 mt-1 max-h-40 overflow-y-auto rounded-md border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface shadow-lg">
          {suggestions.map((name, idx) => (
            <button
              key={name}
              type="button"
              onClick={() => addTag(name)}
              className={`w-full text-left px-3 py-1.5 text-xs transition-colors ${
                idx === highlightIndex
                  ? 'bg-crits-blue/10 text-crits-blue'
                  : 'text-light-text dark:text-dark-text hover:bg-light-hover dark:hover:bg-dark-hover'
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Metadata Sidebar ────────────────────────────────────────────── */

function MetadataSidebar({
  sources,
  campaigns,
  sectors,
  relationships,
  tloType,
  tloId,
  onRelationshipChange,
}: {
  sources: Source[]
  campaigns: string[]
  sectors: string[]
  relationships: Relationship[]
  tloType: string
  tloId: string
  onRelationshipChange: () => void
}) {
  return (
    <>
      <Card className="overflow-hidden">
        <div className="px-3 py-2.5 border-b border-light-border dark:border-dark-border">
          <h3 className="text-sm font-semibold text-light-text dark:text-dark-text">Metadata</h3>
        </div>

        {/* Sources */}
        <SidebarSection icon={User} label="Sources" count={sources.length}>
          {sources.length === 0 ? (
            <p className="text-xs text-light-text-muted dark:text-dark-text-muted">No sources</p>
          ) : (
            <div className="space-y-2">
              {sources.map((source, idx) => (
                <div key={idx}>
                  <span className="text-sm font-medium text-light-text dark:text-dark-text">
                    {source.name}
                  </span>
                  {source.instances.map((inst, iidx) => (
                    <div
                      key={iidx}
                      className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5 ml-2"
                    >
                      {inst.method && <span>{inst.method}</span>}
                      {inst.reference && <span className="ml-1">{inst.reference}</span>}
                      {inst.date && <span className="ml-1">{formatCompactDate(inst.date)}</span>}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </SidebarSection>

        {/* Campaigns */}
        <SidebarSection icon={Shield} label="Campaigns" count={campaigns.length}>
          {campaigns.length === 0 ? (
            <p className="text-xs text-light-text-muted dark:text-dark-text-muted">No campaigns</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {campaigns.map((c) => (
                <Badge key={c} className="text-xs">
                  {c}
                </Badge>
              ))}
            </div>
          )}
        </SidebarSection>

        {/* Sectors — only if non-empty */}
        {sectors.length > 0 && (
          <SidebarSection icon={Activity} label="Sectors" count={sectors.length}>
            <div className="flex flex-wrap gap-1.5">
              {sectors.map((s) => (
                <Badge key={s} variant="info" className="text-xs">
                  {s}
                </Badge>
              ))}
            </div>
          </SidebarSection>
        )}
      </Card>

      <RelationshipsCard
        relationships={relationships}
        tloType={tloType}
        tloId={tloId}
        onRelationshipChange={onRelationshipChange}
      />
    </>
  )
}

// Hash field keys that get their own card in sample layout
const SAMPLE_HASH_KEYS = new Set(['md5', 'sha1', 'sha256', 'ssdeep'])

export function TLODetailPage({ config }: TLODetailPageProps) {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { item, isLoading, error } = useTLODetail(config, id ?? '')

  const { data: meData } = useQuery({
    queryKey: ['me'],
    queryFn: () => gqlQuery<{ me: { username: string } }>('query { me { username } }'),
    staleTime: 300_000,
  })
  const currentUser = meData?.me?.username ?? ''

  const Icon = config.icon
  const isSampleLayout = config.customLayout === 'sample'

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !item) {
    return (
      <div className="text-center py-12">
        <p className="text-status-error mb-4">
          {error
            ? `Failed to load ${config.singular.toLowerCase()}`
            : `${config.singular} not found`}
        </p>
        <Link to={config.route}>
          <Button variant="default">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to {config.label}
          </Button>
        </Link>
      </div>
    )
  }

  const primaryValue = String(item[config.primaryField] ?? '')
  const status = item.status as string | undefined
  const campaigns = (item.campaigns as string[]) ?? []
  const bucketList = (item.bucketList as string[]) ?? []
  const sources = (item.sources as Source[]) ?? []
  const relationships = (item.relationships as Relationship[]) ?? []
  const sectors = (item.sectors as string[]) ?? []
  const created = item.created as string | undefined
  const modified = item.modified as string | undefined

  // For sample layout: alternate filenames
  const filenames = isSampleLayout ? ((item.filenames as string[]) ?? []) : []
  const altFilenames = filenames.filter((f) => f !== primaryValue)

  // Filter detail fields: skip status (shown in header), and for sample layout also skip hash fields
  const detailFieldsFiltered = config.detailFields.filter((f) => {
    if (f.key === 'status') return false
    if (isSampleLayout && SAMPLE_HASH_KEYS.has(f.key)) return false
    if (isSampleLayout && f.key === 'filenames') return false
    return true
  })

  const createdStr = formatCompactDate(created)
  const modifiedStr = formatCompactDate(modified)
  const invalidateDetail = () => queryClient.invalidateQueries({ queryKey: [config.gqlSingle, id] })

  return (
    <div className="space-y-6">
      {/* Breadcrumb and header */}
      <div>
        <Link
          to={config.route}
          className="inline-flex items-center gap-1 text-sm text-crits-blue hover:underline mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to {config.label}
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
              {isSampleLayout ? (
                <FileCode className={`h-6 w-6 ${config.color}`} />
              ) : (
                <Icon className={`h-6 w-6 ${config.color}`} />
              )}
              {isSampleLayout ? primaryValue : `${config.singular} Details`}
            </h1>
            {!isSampleLayout && (
              <p className="font-mono text-lg text-light-text-secondary dark:text-dark-text-secondary mt-1 break-all">
                {primaryValue}
              </p>
            )}
            {isSampleLayout && altFilenames.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-1">
                {altFilenames.map((f) => (
                  <Badge key={f} variant="default" className="text-xs">
                    {f}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {status && config.gqlUpdate ? (
              <EditableField
                field={{
                  key: 'status',
                  label: 'Status',
                  type: 'badge',
                  editable: true,
                  editType: 'select',
                }}
                value={status}
                gqlUpdate={config.gqlUpdate}
                tloId={id ?? ''}
                queryKey={[config.gqlSingle, id]}
              >
                <Badge variant={statusVariant(status)} className="cursor-pointer">
                  {status}
                </Badge>
              </EditableField>
            ) : (
              status && <Badge variant={statusVariant(status)}>{status}</Badge>
            )}
          </div>
        </div>
      </div>

      {/* Dates + Tags */}
      <div className="space-y-3">
        {(createdStr || modifiedStr) && (
          <div className="flex items-center gap-4 text-xs text-light-text-muted dark:text-dark-text-muted">
            {createdStr && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                Created {createdStr}
              </span>
            )}
            {modifiedStr && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                Modified {modifiedStr}
              </span>
            )}
          </div>
        )}
        <TagsSection
          tags={bucketList}
          tloType={config.type}
          tloId={id ?? ''}
          onTagsChange={invalidateDetail}
        />
      </div>

      {/* Main content grid */}
      {isSampleLayout ? (
        <SampleLayout
          item={item}
          config={config}
          detailFieldsFiltered={detailFieldsFiltered}
          sources={sources}
          relationships={relationships}
          campaigns={campaigns}
          sectors={sectors}
          tloType={config.type}
          tloId={id ?? ''}
          currentUser={currentUser}
          onRelationshipChange={invalidateDetail}
        />
      ) : (
        <DefaultLayout
          item={item}
          config={config}
          detailFieldsFiltered={detailFieldsFiltered}
          sources={sources}
          relationships={relationships}
          campaigns={campaigns}
          sectors={sectors}
          tloType={config.type}
          tloId={id ?? ''}
          currentUser={currentUser}
          onRelationshipChange={invalidateDetail}
        />
      )}
    </div>
  )
}

interface LayoutProps {
  item: Record<string, unknown>
  config: TLOConfig
  detailFieldsFiltered: TLODetailFieldDef[]
  sources: Source[]
  relationships: Relationship[]
  campaigns: string[]
  sectors: string[]
  tloType: string
  tloId: string
  currentUser: string
  onRelationshipChange: () => void
}

function DefaultLayout({
  item,
  config,
  detailFieldsFiltered,
  sources,
  relationships,
  campaigns,
  sectors,
  tloType,
  tloId,
  currentUser,
  onRelationshipChange,
}: LayoutProps) {
  const [bottomTab, setBottomTab] = useState<'comments' | 'timeline'>('comments')

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left column - Detail content */}
      <div className="lg:col-span-3 space-y-6">
        <DetailFieldsCard fields={detailFieldsFiltered} item={item} config={config} tloId={tloId} />

        {/* Comments / Timeline tabs */}
        <Card className="p-0">
          <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-light-border dark:border-dark-border">
            <button
              onClick={() => setBottomTab('comments')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                bottomTab === 'comments'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Comments
            </button>
            <button
              onClick={() => setBottomTab('timeline')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                bottomTab === 'timeline'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <Clock className="h-4 w-4" />
              Timeline
            </button>
          </div>
          <CardContent className="p-4">
            {bottomTab === 'comments' && (
              <CommentsSection objType={tloType} objId={tloId} currentUser={currentUser} />
            )}
            {bottomTab === 'timeline' && (
              <ActivityTimeline item={item} objType={tloType} objId={tloId} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right column - Metadata sidebar */}
      <div className="lg:col-span-1 space-y-6">
        <MetadataSidebar
          sources={sources}
          campaigns={campaigns}
          sectors={sectors}
          relationships={relationships}
          tloType={tloType}
          tloId={tloId}
          onRelationshipChange={onRelationshipChange}
        />
      </div>
    </div>
  )
}

function SampleLayout({
  item,
  config,
  detailFieldsFiltered,
  sources,
  relationships,
  campaigns,
  sectors,
  tloType,
  tloId,
  currentUser,
  onRelationshipChange,
}: LayoutProps) {
  const md5 = (item.md5 as string) ?? ''
  const [sampleTab, setSampleTab] = useState<'details' | 'tools' | 'services'>('details')
  const [bottomTab, setBottomTab] = useState<'comments' | 'timeline'>('comments')

  const renderFieldWithEdit = (field: TLODetailFieldDef) => {
    const content = <FieldValue field={field} item={item} />
    if (field.editable && config.gqlUpdate) {
      return (
        <EditableField
          field={field}
          value={getNestedValue(item, field.key)}
          gqlUpdate={config.gqlUpdate}
          tloId={tloId}
          queryKey={[config.gqlSingle, tloId]}
        >
          {content}
        </EditableField>
      )
    }
    return content
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left column - Detail content */}
      <div className="lg:col-span-3 space-y-6">
        {/* Tabbed card: Details / Tools */}
        <Card className="p-0">
          <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-light-border dark:border-dark-border">
            <button
              onClick={() => setSampleTab('details')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                sampleTab === 'details'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <Info className="h-4 w-4" />
              Details
            </button>
            {md5 && (
              <button
                onClick={() => setSampleTab('tools')}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  sampleTab === 'tools'
                    ? 'border-crits-blue text-crits-blue'
                    : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
                }`}
              >
                <Wrench className="h-4 w-4" />
                Tools
              </button>
            )}
            <button
              onClick={() => setSampleTab('services')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                sampleTab === 'services'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <Activity className="h-4 w-4" />
              Services
            </button>
          </div>
          <CardContent className="p-4">
            {sampleTab === 'details' && (
              <div>
                <dl className="grid grid-cols-2 gap-4">
                  {detailFieldsFiltered
                    .filter((f) => f.type !== 'pre' && f.type !== 'list')
                    .map((field) => (
                      <div key={field.key}>
                        <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                          {field.label}
                        </dt>
                        <dd className="text-light-text dark:text-dark-text mt-1">
                          {renderFieldWithEdit(field)}
                        </dd>
                      </div>
                    ))}
                </dl>
                {detailFieldsFiltered
                  .filter((f) => f.type === 'pre')
                  .map((field) => {
                    const val = getNestedValue(item, field.key)
                    if (!val && !field.editable) return null
                    return (
                      <div
                        key={field.key}
                        className="mt-4 pt-4 border-t border-light-border dark:border-dark-border"
                      >
                        <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                          {field.label}
                        </dt>
                        <dd className="text-light-text dark:text-dark-text">
                          {renderFieldWithEdit(field)}
                        </dd>
                      </div>
                    )
                  })}
                <div className="mt-4 pt-4 border-t border-light-border dark:border-dark-border">
                  <SampleHashCard
                    md5={item.md5 as string | undefined}
                    sha1={item.sha1 as string | undefined}
                    sha256={item.sha256 as string | undefined}
                    ssdeep={item.ssdeep as string | undefined}
                    bare
                  />
                </div>
              </div>
            )}
            {sampleTab === 'tools' && md5 && <SampleToolsCard md5={md5} bare />}
            {sampleTab === 'services' && (
              <SampleServicesCard objType={tloType} objId={tloId} bare />
            )}
          </CardContent>
        </Card>

        {/* Comments / Timeline tabs */}
        <Card className="p-0">
          <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b border-light-border dark:border-dark-border">
            <button
              onClick={() => setBottomTab('comments')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                bottomTab === 'comments'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Comments
            </button>
            <button
              onClick={() => setBottomTab('timeline')}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                bottomTab === 'timeline'
                  ? 'border-crits-blue text-crits-blue'
                  : 'border-transparent text-light-text-muted dark:text-dark-text-muted hover:text-light-text dark:hover:text-dark-text'
              }`}
            >
              <Clock className="h-4 w-4" />
              Timeline
            </button>
          </div>
          <CardContent className="p-4">
            {bottomTab === 'comments' && (
              <CommentsSection objType={tloType} objId={tloId} currentUser={currentUser} />
            )}
            {bottomTab === 'timeline' && (
              <ActivityTimeline item={item} objType={tloType} objId={tloId} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right column - Metadata sidebar */}
      <div className="lg:col-span-1 space-y-6">
        <MetadataSidebar
          sources={sources}
          campaigns={campaigns}
          sectors={sectors}
          relationships={relationships}
          tloType={tloType}
          tloId={tloId}
          onRelationshipChange={onRelationshipChange}
        />
      </div>
    </div>
  )
}

function DetailFieldsCard({
  fields,
  item,
  config,
  tloId,
}: {
  fields: TLODetailFieldDef[]
  item: Record<string, unknown>
  config?: TLOConfig
  tloId?: string
}) {
  const renderFieldWithEdit = (field: TLODetailFieldDef) => {
    const content = <FieldValue field={field} item={item} />
    if (field.editable && config?.gqlUpdate && tloId) {
      return (
        <EditableField
          field={field}
          value={getNestedValue(item, field.key)}
          gqlUpdate={config.gqlUpdate}
          tloId={tloId}
          queryKey={[config.gqlSingle, tloId]}
        >
          {content}
        </EditableField>
      )
    }
    return content
  }

  return (
    <Card>
      <div className="px-6 pt-4 pb-2">
        <h3 className="text-base font-semibold text-light-text dark:text-dark-text flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Details
        </h3>
      </div>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4">
          {fields
            .filter((f) => f.type !== 'pre' && f.type !== 'list')
            .map((field) => (
              <div key={field.key}>
                <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                  {field.label}
                </dt>
                <dd className="text-light-text dark:text-dark-text mt-1">
                  {renderFieldWithEdit(field)}
                </dd>
              </div>
            ))}
        </dl>

        {fields
          .filter((f) => f.type === 'pre')
          .map((field) => {
            const val = getNestedValue(item, field.key)
            if (!val && !field.editable) return null
            return (
              <div
                key={field.key}
                className="mt-4 pt-4 border-t border-light-border dark:border-dark-border"
              >
                <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                  {field.label}
                </dt>
                <dd className="text-light-text dark:text-dark-text">
                  {renderFieldWithEdit(field)}
                </dd>
              </div>
            )
          })}

        {fields
          .filter((f) => f.type === 'list')
          .map((field) => {
            const arr = getNestedValue(item, field.key) as string[] | undefined
            if (!arr?.length) return null
            return (
              <div
                key={field.key}
                className="mt-4 pt-4 border-t border-light-border dark:border-dark-border"
              >
                <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                  {field.label}
                </dt>
                <dd className="flex flex-wrap gap-2">
                  {arr.map((v) => (
                    <Badge key={v} variant="info">
                      {v}
                    </Badge>
                  ))}
                </dd>
              </div>
            )
          })}
      </CardContent>
    </Card>
  )
}
