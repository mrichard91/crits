import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Tag, Search } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Card, CardContent, Input, Spinner } from '@/components/ui'

const TAG_SUMMARY_QUERY = `
  query {
    tagSummary {
      name
      total
    }
  }
`

interface TagSummaryItem {
  name: string
  total: number
}

export function TagsPage() {
  const [filter, setFilter] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['tagSummary'],
    queryFn: () => gqlQuery<{ tagSummary: TagSummaryItem[] }>(TAG_SUMMARY_QUERY),
  })

  const tags = data?.tagSummary ?? []
  const filtered = filter
    ? tags.filter((t) => t.name.toLowerCase().includes(filter.toLowerCase()))
    : tags

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text flex items-center gap-2">
          <Tag className="h-6 w-6 text-crits-blue" />
          Tags
        </h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          {tags.length} tags across all objects
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-light-text-muted dark:text-dark-text-muted" />
            <Input
              placeholder="Filter tags..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center text-status-error py-12">Failed to load tags</div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-light-text-muted dark:text-dark-text-muted py-12">
              {filter ? 'No tags match your filter' : 'No tags found'}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-px bg-light-border dark:bg-dark-border">
              {filtered.map((tag) => (
                <Link
                  key={tag.name}
                  to={`/tags/${encodeURIComponent(tag.name)}`}
                  className="flex items-center justify-between px-4 py-3 bg-light-surface dark:bg-dark-surface hover:bg-light-hover dark:hover:bg-dark-hover transition-colors"
                >
                  <span className="flex items-center gap-2 text-sm font-medium text-light-text dark:text-dark-text min-w-0">
                    <Tag className="h-3.5 w-3.5 text-crits-blue shrink-0" />
                    <span className="truncate">{tag.name}</span>
                  </span>
                  <span className="ml-2 shrink-0 inline-flex items-center justify-center rounded-full bg-crits-blue/10 text-crits-blue text-xs font-medium px-2 py-0.5">
                    {tag.total}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
