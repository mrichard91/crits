import { Link } from 'react-router-dom'
import { ArrowRightLeft } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Badge } from '@/components/ui'
import { TLO_CONFIGS } from '@/lib/tloConfig'
import type { TLOType } from '@/types'
import { truncate } from '@/lib/utils'

interface Relationship {
  objectId: string
  relType: string
  relationship: string
  relConfidence: string
  analyst: string
}

interface RelationshipsCardProps {
  relationships: Relationship[]
}

export function RelationshipsCard({ relationships }: RelationshipsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowRightLeft className="h-5 w-5" />
          Relationships ({relationships.length})
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
                      title={`${rel.relType}: ${rel.objectId}`}
                    >
                      {rel.relType}: {truncate(rel.objectId, 16)}
                    </Link>
                  ) : (
                    <span className="font-mono truncate text-light-text-secondary dark:text-dark-text-secondary">
                      {rel.relType}: {truncate(rel.objectId, 16)}
                    </span>
                  )}
                  {rel.relConfidence && rel.relConfidence !== 'unknown' && (
                    <Badge variant="info" className="ml-auto shrink-0">
                      {rel.relConfidence}
                    </Badge>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
