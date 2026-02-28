import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Tag, ChevronDown, ChevronRight } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { TLO_CONFIGS, TLO_NAV_ORDER } from '@/lib/tloConfig'
import { MiniTLOTable } from '@/components/MiniTLOTable'
import { Card, CardContent, Badge, Spinner } from '@/components/ui'

const TAGGED_OBJECTS_QUERY = `
  query TaggedObjects($tag: String!, $tloType: String!, $limit: Int) {
    taggedObjects(tag: $tag, tloType: $tloType, limit: $limit) {
      id
      tloType
      displayValue
      modified
      status
    }
  }
`

interface TaggedObject {
  id: string
  tloType: string
  displayValue: string
  modified: string | null
  status: string
}

function TagTypeSection({ tag, tloType }: { tag: string; tloType: string }) {
  const config = TLO_CONFIGS[tloType as keyof typeof TLO_CONFIGS]
  const [open, setOpen] = useState(true)

  const { data, isLoading } = useQuery({
    queryKey: ['taggedObjects', tag, tloType],
    queryFn: () =>
      gqlQuery<{ taggedObjects: TaggedObject[] }>(TAGGED_OBJECTS_QUERY, {
        tag,
        tloType,
        limit: 50,
      }),
  })

  const objects = data?.taggedObjects ?? []

  if (!isLoading && objects.length === 0) return null
  if (!config) return null

  // Map search results to table items using config's primaryField
  const items = objects.map((obj) => ({
    id: obj.id,
    [config.primaryField]: obj.displayValue,
    status: obj.status,
    modified: obj.modified,
  }))

  const Icon = config.icon

  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full px-4 py-3 text-left hover:bg-light-hover dark:hover:bg-dark-hover transition-colors"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0" />
        )}
        <Icon className={`h-4 w-4 shrink-0 ${config.color}`} />
        <span className="text-sm font-semibold text-light-text dark:text-dark-text flex-1">
          {config.label}
        </span>
        {isLoading ? (
          <Spinner size="sm" />
        ) : (
          <Badge variant="default" className="text-xs px-1.5 py-0">
            {objects.length}
          </Badge>
        )}
      </button>
      {open && (
        <CardContent className="p-0 border-t border-light-border dark:border-dark-border">
          {isLoading ? (
            <div className="flex justify-center py-6">
              <Spinner size="sm" />
            </div>
          ) : (
            <MiniTLOTable config={config} items={items} />
          )}
        </CardContent>
      )}
    </Card>
  )
}

export function TagDetailPage() {
  const { tagName } = useParams<{ tagName: string }>()
  const decodedTag = decodeURIComponent(tagName ?? '')

  return (
    <div className="space-y-4">
      <div>
        <Link
          to="/tags"
          className="inline-flex items-center gap-1 text-sm text-crits-blue hover:underline mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Tags
        </Link>
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
          <Tag className="h-6 w-6 text-crits-blue" />
          {decodedTag}
        </h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          Objects tagged with &ldquo;{decodedTag}&rdquo;
        </p>
      </div>

      <div className="space-y-4">
        {TLO_NAV_ORDER.map((type) => (
          <TagTypeSection key={type} tag={decodedTag} tloType={type} />
        ))}
      </div>
    </div>
  )
}
