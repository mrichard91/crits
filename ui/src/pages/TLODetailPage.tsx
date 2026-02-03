import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Calendar, User, Shield, Tag, Activity, FileText } from 'lucide-react'
import { useTLODetail } from '@/hooks/useTLODetail'
import type { TLOConfig, TLODetailFieldDef } from '@/lib/tloConfig'
import { Card, CardHeader, CardTitle, CardContent, Badge, Spinner, Button } from '@/components/ui'
import { formatDate } from '@/lib/utils'

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

export function TLODetailPage({ config }: TLODetailPageProps) {
  const { id } = useParams<{ id: string }>()
  const { item, isLoading, error } = useTLODetail(config, id ?? '')

  const Icon = config.icon

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

  // Split detail fields: common ones in left column, skip status (shown in header)
  const detailFieldsFiltered = config.detailFields.filter((f) => f.key !== 'status')

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
              <Icon className={`h-6 w-6 ${config.color}`} />
              {config.singular} Details
            </h1>
            <p className="font-mono text-lg text-light-text-secondary dark:text-dark-text-secondary mt-1 break-all">
              {primaryValue}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {status && <Badge variant={statusVariant(status)}>{status}</Badge>}
          </div>
        </div>
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Details
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

              {/* Description / pre fields */}
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

              {/* List fields (threat types, attack types, aliases, etc.) */}
              {detailFieldsFiltered
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

          {/* Sources */}
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
        </div>

        {/* Right column - Metadata */}
        <div className="space-y-6">
          {/* Campaigns */}
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

          {/* Bucket List (Tags) */}
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

          {/* Sectors */}
          {(item.sectors as string[] | undefined)?.length ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Sectors ({(item.sectors as string[]).length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {(item.sectors as string[]).map((s) => (
                    <Badge key={s} variant="info">
                      {s}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  )
}
