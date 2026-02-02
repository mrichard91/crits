import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Target,
  ArrowLeft,
  Calendar,
  User,
  Shield,
  Tag,
  Activity,
  FileText,
} from 'lucide-react'
import { graphqlClient } from '@/lib/graphql'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Spinner,
  Button,
} from '@/components/ui'
import { formatDate } from '@/lib/utils'

const INDICATOR_QUERY = `
  query Indicator($id: ID!) {
    indicator(id: $id) {
      id
      value
      indicatorType
      status
      confidence
      impact
      created
      modified
      description
      campaigns
      bucketList
      sources {
        name
        instances {
          method
          reference
          date
          analyst
        }
      }
      threatTypes
      attackTypes
    }
  }
`

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

interface IndicatorDetail {
  id: string
  value: string
  indicatorType: string
  status: string
  confidence: string
  impact: string
  created: string
  modified: string
  description: string | null
  campaigns: string[]
  bucketList: string[]
  sources: Source[]
  threatTypes: string[]
  attackTypes: string[]
}

interface IndicatorData {
  indicator: IndicatorDetail | null
}

export function IndicatorDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading, error } = useQuery({
    queryKey: ['indicator', id],
    queryFn: () =>
      graphqlClient.request<IndicatorData>(INDICATOR_QUERY, { id }),
    enabled: !!id,
  })

  const indicator = data?.indicator

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !indicator) {
    return (
      <div className="text-center py-12">
        <p className="text-status-error mb-4">
          {error ? 'Failed to load indicator' : 'Indicator not found'}
        </p>
        <Link to="/indicators">
          <Button variant="default">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Indicators
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb and header */}
      <div>
        <Link
          to="/indicators"
          className="inline-flex items-center gap-1 text-sm text-crits-blue hover:underline mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Indicators
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
              <Target className="h-6 w-6 text-crits-blue" />
              Indicator Details
            </h1>
            <p className="font-mono text-lg text-light-text-secondary dark:text-dark-text-secondary mt-1 break-all">
              {indicator.value}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="info">{indicator.indicatorType}</Badge>
            <Badge
              variant={
                indicator.status === 'Analyzed'
                  ? 'success'
                  : indicator.status === 'In Progress'
                  ? 'warning'
                  : indicator.status === 'Deprecated'
                  ? 'error'
                  : 'default'
              }
            >
              {indicator.status}
            </Badge>
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
                <div>
                  <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                    Confidence
                  </dt>
                  <dd className="text-light-text dark:text-dark-text">
                    {indicator.confidence || 'Unknown'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                    Impact
                  </dt>
                  <dd className="text-light-text dark:text-dark-text">
                    {indicator.impact || 'Unknown'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                    Created
                  </dt>
                  <dd className="text-light-text dark:text-dark-text flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(indicator.created)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted">
                    Modified
                  </dt>
                  <dd className="text-light-text dark:text-dark-text flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {formatDate(indicator.modified)}
                  </dd>
                </div>
              </dl>

              {indicator.description && (
                <div className="mt-4 pt-4 border-t border-light-border dark:border-dark-border">
                  <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                    Description
                  </dt>
                  <dd className="text-light-text dark:text-dark-text whitespace-pre-wrap">
                    {indicator.description}
                  </dd>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sources */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Sources ({indicator.sources.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {indicator.sources.length === 0 ? (
                <p className="text-light-text-muted dark:text-dark-text-muted">
                  No sources
                </p>
              ) : (
                <div className="space-y-4">
                  {indicator.sources.map((source, idx) => (
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
                          {instance.reference && (
                            <span className="ml-2">• {instance.reference}</span>
                          )}
                          <span className="ml-2">• {instance.analyst}</span>
                          <span className="ml-2">
                            • {formatDate(instance.date)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Threat/Attack Types */}
          {(indicator.threatTypes.length > 0 ||
            indicator.attackTypes.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Classification
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {indicator.threatTypes.length > 0 && (
                    <div>
                      <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                        Threat Types
                      </dt>
                      <dd className="flex flex-wrap gap-2">
                        {indicator.threatTypes.map((type) => (
                          <Badge key={type} variant="warning">
                            {type}
                          </Badge>
                        ))}
                      </dd>
                    </div>
                  )}
                  {indicator.attackTypes.length > 0 && (
                    <div>
                      <dt className="text-sm font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
                        Attack Types
                      </dt>
                      <dd className="flex flex-wrap gap-2">
                        {indicator.attackTypes.map((type) => (
                          <Badge key={type} variant="error">
                            {type}
                          </Badge>
                        ))}
                      </dd>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column - Metadata */}
        <div className="space-y-6">
          {/* Campaigns */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Campaigns ({indicator.campaigns.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {indicator.campaigns.length === 0 ? (
                <p className="text-light-text-muted dark:text-dark-text-muted">
                  No campaigns
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {indicator.campaigns.map((campaign) => (
                    <Badge key={campaign}>{campaign}</Badge>
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
                Tags ({indicator.bucketList.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {indicator.bucketList.length === 0 ? (
                <p className="text-light-text-muted dark:text-dark-text-muted">
                  No tags
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {indicator.bucketList.map((tag) => (
                    <Badge key={tag} variant="info">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
