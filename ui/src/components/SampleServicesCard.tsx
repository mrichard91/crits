import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Spinner } from '@/components/ui'
import { gqlQuery } from '@/lib/graphql'

interface SampleServicesCardProps {
  objType: string
  objId: string
  bare?: boolean
}

/* ── GraphQL documents ────────────────────────────────────────────── */

const ANALYSIS_RESULTS_QUERY = `
  query AnalysisResults($objType: String!, $objId: String!) {
    analysisResults(objType: $objType, objId: $objId) {
      id
      analysisId
      serviceName
      version
      status
      analyst
      startDate
      finishDate
      results
      log {
        message
        level
        datetime
      }
    }
  }
`

const LIST_SERVICES_QUERY = `
  query ListServices {
    listServices {
      name
      description
      enabled
      runOnTriage
      supportedTypes
    }
  }
`

const RUN_SERVICE_MUTATION = `
  mutation RunService($serviceName: String!, $objType: String!, $objId: String!) {
    runService(serviceName: $serviceName, objType: $objType, objId: $objId) {
      success
      message
      analysisId
    }
  }
`

const RUN_TRIAGE_MUTATION = `
  mutation RunTriage($objType: String!, $objId: String!) {
    runTriage(objType: $objType, objId: $objId) {
      success
      message
    }
  }
`

/* ── Types ────────────────────────────────────────────────────────── */

interface AnalysisLogEntry {
  message: string
  level: string
  datetime: string
}

interface AnalysisResult {
  id: string
  analysisId: string
  serviceName: string
  version: string
  status: string
  analyst: string
  startDate: string
  finishDate: string
  results: Record<string, unknown>[]
  log: AnalysisLogEntry[]
}

interface ServiceInfo {
  name: string
  description: string
  enabled: boolean
  runOnTriage: boolean
  supportedTypes: string[]
}

/* ── Helpers ──────────────────────────────────────────────────────── */

function statusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-status-success" />
    case 'error':
      return <XCircle className="h-4 w-4 text-status-error" />
    case 'started':
    case 'running':
      return <Loader2 className="h-4 w-4 text-crits-blue animate-spin" />
    default:
      return <Clock className="h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
  }
}

function statusBadgeVariant(status: string): 'success' | 'error' | 'warning' | 'default' {
  switch (status) {
    case 'completed':
      return 'success'
    case 'error':
      return 'error'
    case 'started':
    case 'running':
      return 'warning'
    default:
      return 'default'
  }
}

function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/* ── Result row (collapsible) ─────────────────────────────────────── */

function ResultRow({ result }: { result: AnalysisResult }) {
  const [expanded, setExpanded] = useState(false)
  const hasDetails = result.results.length > 0 || result.log.length > 0

  return (
    <div className="border border-light-border dark:border-dark-border rounded">
      <button
        type="button"
        onClick={() => hasDetails && setExpanded(!expanded)}
        className={`flex items-center gap-2 w-full px-3 py-2 text-sm text-left ${
          hasDetails
            ? 'cursor-pointer hover:bg-light-hover dark:hover:bg-dark-hover'
            : 'cursor-default'
        } transition-colors`}
      >
        {statusIcon(result.status)}
        <span className="font-medium text-light-text dark:text-dark-text flex-1">
          {result.serviceName}
          {result.version && (
            <span className="text-xs text-light-text-muted dark:text-dark-text-muted ml-1">
              v{result.version}
            </span>
          )}
        </span>
        <Badge variant={statusBadgeVariant(result.status)} className="text-xs">
          {result.status}
        </Badge>
        {result.finishDate && (
          <span className="text-xs text-light-text-muted dark:text-dark-text-muted">
            {formatDate(result.finishDate)}
          </span>
        )}
        {hasDetails &&
          (expanded ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-light-text-muted dark:text-dark-text-muted" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-light-text-muted dark:text-dark-text-muted" />
          ))}
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t border-light-border dark:border-dark-border">
          {/* Results */}
          {result.results.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-1">
                Results
              </p>
              <pre className="text-xs font-mono bg-light-surface dark:bg-dark-surface p-2 rounded overflow-auto max-h-64 whitespace-pre-wrap">
                {JSON.stringify(result.results, null, 2)}
              </pre>
            </div>
          )}
          {/* Log */}
          {result.log.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-1">
                Log
              </p>
              <div className="text-xs font-mono bg-light-surface dark:bg-dark-surface p-2 rounded overflow-auto max-h-48 space-y-0.5">
                {result.log.map((entry, i) => (
                  <div key={i} className="flex gap-2">
                    <span
                      className={
                        entry.level === 'error'
                          ? 'text-status-error'
                          : entry.level === 'warning'
                            ? 'text-status-warning'
                            : 'text-light-text-muted dark:text-dark-text-muted'
                      }
                    >
                      [{entry.level}]
                    </span>
                    <span className="text-light-text dark:text-dark-text">{entry.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Metadata */}
          <div className="mt-2 flex gap-4 text-xs text-light-text-muted dark:text-dark-text-muted">
            {result.analyst && <span>Analyst: {result.analyst}</span>}
            {result.startDate && <span>Started: {formatDate(result.startDate)}</span>}
            {result.finishDate && <span>Finished: {formatDate(result.finishDate)}</span>}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Main component ───────────────────────────────────────────────── */

export function SampleServicesCard({ objType, objId, bare }: SampleServicesCardProps) {
  const queryClient = useQueryClient()

  // Fetch analysis results
  const results = useQuery({
    queryKey: ['analysisResults', objType, objId],
    queryFn: () =>
      gqlQuery<{ analysisResults: AnalysisResult[] }>(ANALYSIS_RESULTS_QUERY, {
        objType,
        objId,
      }),
  })

  // Fetch available services
  const services = useQuery({
    queryKey: ['listServices'],
    queryFn: () => gqlQuery<{ listServices: ServiceInfo[] }>(LIST_SERVICES_QUERY),
  })

  const invalidateResults = () => {
    queryClient.invalidateQueries({ queryKey: ['analysisResults', objType, objId] })
  }

  // Run single service
  const runService = useMutation({
    mutationFn: (serviceName: string) =>
      gqlQuery<{ runService: { success: boolean; message: string; analysisId: string } }>(
        RUN_SERVICE_MUTATION,
        { serviceName, objType, objId },
      ),
    onSuccess: () => {
      // Delay refetch slightly to give the worker time to create the record
      setTimeout(invalidateResults, 1500)
    },
  })

  // Run triage
  const runTriage = useMutation({
    mutationFn: () =>
      gqlQuery<{ runTriage: { success: boolean; message: string } }>(RUN_TRIAGE_MUTATION, {
        objType,
        objId,
      }),
    onSuccess: () => {
      setTimeout(invalidateResults, 2000)
    },
  })

  // Filter services to those supporting this object type
  const availableServices = (services.data?.listServices ?? []).filter(
    (s) => s.enabled && (s.supportedTypes.length === 0 || s.supportedTypes.includes(objType)),
  )

  const analysisResults = results.data?.analysisResults ?? []

  const content = (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          size="sm"
          variant="primary"
          onClick={() => runTriage.mutate()}
          disabled={runTriage.isPending}
        >
          {runTriage.isPending ? (
            <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5 mr-1" />
          )}
          Run Triage
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => results.refetch()}
          disabled={results.isFetching}
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1 ${results.isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
        {runTriage.isSuccess && (
          <span className="text-xs text-status-success">Triage dispatched</span>
        )}
        {runTriage.isError && (
          <span className="text-xs text-status-error">{(runTriage.error as Error).message}</span>
        )}
      </div>

      {/* Available services */}
      {availableServices.length > 0 && (
        <div>
          <p className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
            Available Services
          </p>
          <div className="flex flex-wrap gap-2">
            {availableServices.map((svc) => (
              <Button
                key={svc.name}
                size="sm"
                variant="ghost"
                onClick={() => runService.mutate(svc.name)}
                disabled={runService.isPending}
                title={svc.description || svc.name}
              >
                <Play className="h-3 w-3 mr-1" />
                {svc.name}
                {svc.runOnTriage && (
                  <Badge variant="default" className="text-[10px] ml-1 px-1 py-0">
                    triage
                  </Badge>
                )}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Results list */}
      <div>
        <p className="text-xs font-medium text-light-text-muted dark:text-dark-text-muted mb-2">
          Results ({analysisResults.length})
        </p>
        {results.isLoading ? (
          <div className="flex justify-center py-4">
            <Spinner size="sm" />
          </div>
        ) : analysisResults.length === 0 ? (
          <p className="text-sm text-light-text-muted dark:text-dark-text-muted py-2">
            No analysis results yet. Run triage or an individual service to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {analysisResults.map((ar) => (
              <ResultRow key={ar.id} result={ar} />
            ))}
          </div>
        )}
      </div>
    </div>
  )

  if (bare) {
    return content
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play className="h-5 w-5" />
          Services
        </CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  )
}
