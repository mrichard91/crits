import { useParams, Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Calendar,
  User,
  Shield,
  Tag,
  Activity,
  FileText,
  FileCode,
  Info,
} from 'lucide-react'
import { useTLODetail } from '@/hooks/useTLODetail'
import type { TLOConfig, TLODetailFieldDef } from '@/lib/tloConfig'
import { Card, CardHeader, CardTitle, CardContent, Badge, Spinner, Button } from '@/components/ui'
import { formatDate } from '@/lib/utils'
import { RelationshipsCard } from '@/components/RelationshipsCard'
import { SampleHashCard } from '@/components/SampleHashCard'
import { SampleToolsCard } from '@/components/SampleToolsCard'

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

function SourcesCard({ sources }: { sources: Source[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Sources ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sources.length === 0 ? (
          <p className="text-light-text-muted dark:text-dark-text-muted">No sources</p>
        ) : (
          <div className="space-y-4">
            {sources.map((source, idx) => (
              <div
                key={idx}
                className="p-3 rounded border border-light-border dark:border-dark-border"
              >
                <h4 className="font-medium text-light-text dark:text-dark-text mb-2">
                  {source.name}
                </h4>
                {source.instances.map((instance, iidx) => (
                  <div
                    key={iidx}
                    className="text-sm text-light-text-secondary dark:text-dark-text-secondary"
                  >
                    <span>{instance.method}</span>
                    {instance.reference && <span className="ml-2">{instance.reference}</span>}
                    <span className="ml-2">{instance.analyst}</span>
                    <span className="ml-2">{formatDate(instance.date)}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function RightColumnCards({
  campaigns,
  bucketList,
  sectors,
}: {
  campaigns: string[]
  bucketList: string[]
  sectors: string[]
}) {
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Campaigns ({campaigns.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {campaigns.length === 0 ? (
            <p className="text-light-text-muted dark:text-dark-text-muted">No campaigns</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {campaigns.map((c) => (
                <Badge key={c}>{c}</Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tag className="h-5 w-5" />
            Tags ({bucketList.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {bucketList.length === 0 ? (
            <p className="text-light-text-muted dark:text-dark-text-muted">No tags</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {bucketList.map((tag) => (
                <Badge key={tag} variant="info">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {sectors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Sectors ({sectors.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {sectors.map((s) => (
                <Badge key={s} variant="info">
                  {s}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  )
}

// Hash field keys that get their own card in sample layout
const SAMPLE_HASH_KEYS = new Set(['md5', 'sha1', 'sha256', 'ssdeep'])

export function TLODetailPage({ config }: TLODetailPageProps) {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const { item, isLoading, error } = useTLODetail(config, id ?? '')

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
  const dateSubtitle = [
    createdStr && `Created ${createdStr}`,
    modifiedStr && `Modified ${modifiedStr}`,
  ]
    .filter(Boolean)
    .join(' | ')

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
            {dateSubtitle && (
              <p className="text-xs text-light-text-muted dark:text-dark-text-muted mt-1">
                {dateSubtitle}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {status && <Badge variant={statusVariant(status)}>{status}</Badge>}
          </div>
        </div>
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
          bucketList={bucketList}
          sectors={sectors}
          tloType={config.type}
          tloId={id ?? ''}
          onRelationshipChange={() =>
            queryClient.invalidateQueries({ queryKey: [config.gqlSingle, id] })
          }
        />
      ) : (
        <DefaultLayout
          item={item}
          config={config}
          detailFieldsFiltered={detailFieldsFiltered}
          sources={sources}
          relationships={relationships}
          campaigns={campaigns}
          bucketList={bucketList}
          sectors={sectors}
          tloType={config.type}
          tloId={id ?? ''}
          onRelationshipChange={() =>
            queryClient.invalidateQueries({ queryKey: [config.gqlSingle, id] })
          }
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
  bucketList: string[]
  sectors: string[]
  tloType: string
  tloId: string
  onRelationshipChange: () => void
}

function DefaultLayout({
  item,
  detailFieldsFiltered,
  sources,
  relationships,
  campaigns,
  bucketList,
  sectors,
  tloType,
  tloId,
  onRelationshipChange,
}: LayoutProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left column - Details */}
      <div className="lg:col-span-2 space-y-6">
        <DetailFieldsCard fields={detailFieldsFiltered} item={item} />
        <SourcesCard sources={sources} />
        <RelationshipsCard
          relationships={relationships}
          tloType={tloType}
          tloId={tloId}
          onRelationshipChange={onRelationshipChange}
        />
      </div>

      {/* Right column - Metadata */}
      <div className="space-y-6">
        <RightColumnCards campaigns={campaigns} bucketList={bucketList} sectors={sectors} />
      </div>
    </div>
  )
}

function SampleLayout({
  item,
  detailFieldsFiltered,
  sources,
  relationships,
  campaigns,
  bucketList,
  sectors,
  tloType,
  tloId,
  onRelationshipChange,
}: LayoutProps) {
  const md5 = (item.md5 as string) ?? ''

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left column */}
      <div className="lg:col-span-2 space-y-6">
        {/* Compact file info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              File Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-4">
              {detailFieldsFiltered
                .filter((f) => f.type !== 'pre' && f.type !== 'list')
                .map((field) => (
                  <div key={field.key}>
                    <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                      {field.label}
                    </dt>
                    <dd className="text-light-text dark:text-dark-text mt-1">
                      <FieldValue field={field} item={item} />
                    </dd>
                  </div>
                ))}
            </dl>
            {detailFieldsFiltered
              .filter((f) => f.type === 'pre')
              .map((field) => {
                const val = getNestedValue(item, field.key)
                if (!val) return null
                return (
                  <div
                    key={field.key}
                    className="mt-4 pt-4 border-t border-light-border dark:border-dark-border"
                  >
                    <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                      {field.label}
                    </dt>
                    <dd className="text-light-text dark:text-dark-text whitespace-pre-wrap">
                      {String(val)}
                    </dd>
                  </div>
                )
              })}
          </CardContent>
        </Card>

        <SampleHashCard
          md5={item.md5 as string | undefined}
          sha1={item.sha1 as string | undefined}
          sha256={item.sha256 as string | undefined}
          ssdeep={item.ssdeep as string | undefined}
        />

        {md5 && <SampleToolsCard md5={md5} />}

        <SourcesCard sources={sources} />
        <RelationshipsCard
          relationships={relationships}
          tloType={tloType}
          tloId={tloId}
          onRelationshipChange={onRelationshipChange}
        />
      </div>

      {/* Right column */}
      <div className="space-y-6">
        <RightColumnCards campaigns={campaigns} bucketList={bucketList} sectors={sectors} />
      </div>
    </div>
  )
}

function DetailFieldsCard({
  fields,
  item,
}: {
  fields: TLODetailFieldDef[]
  item: Record<string, unknown>
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Details
        </CardTitle>
      </CardHeader>
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
                  <FieldValue field={field} item={item} />
                </dd>
              </div>
            ))}
        </dl>

        {fields
          .filter((f) => f.type === 'pre')
          .map((field) => {
            const val = getNestedValue(item, field.key)
            if (!val) return null
            return (
              <div
                key={field.key}
                className="mt-4 pt-4 border-t border-light-border dark:border-dark-border"
              >
                <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                  {field.label}
                </dt>
                <dd className="text-light-text dark:text-dark-text whitespace-pre-wrap">
                  {String(val)}
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
