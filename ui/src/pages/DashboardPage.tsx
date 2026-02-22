import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useDashboardStats } from '@/hooks/useDashboardStats'
import { TLO_CONFIGS, TLO_NAV_ORDER } from '@/lib/tloConfig'
import type { TLOType } from '@/types'
import { Card, CardHeader, CardTitle, CardContent, Spinner, Badge } from '@/components/ui'
import { formatDate } from '@/lib/utils'

function getCountForType(counts: { tloType: string; count: number }[], type: string): number {
  return counts.find((c) => c.tloType === type)?.count ?? 0
}

export function DashboardPage() {
  const { stats, isLoading, error } = useDashboardStats()

  if (error) {
    return <div className="text-center text-status-error py-12">Failed to load dashboard data</div>
  }

  const counts = stats?.counts ?? []
  const recentActivity = stats?.recentActivity ?? []
  const topCampaigns = stats?.topCampaigns ?? []
  const maxCampaignCount = topCampaigns.length > 0 ? topCampaigns[0].count : 1

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text">Dashboard</h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          Overview of your threat intelligence data
          {stats && (
            <span className="ml-2 font-medium">
              — {stats.totalCount.toLocaleString()} total objects
            </span>
          )}
        </p>
      </div>

      {/* TLO Count Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {TLO_NAV_ORDER.map((type) => {
          const config = TLO_CONFIGS[type as TLOType]
          const Icon = config.icon
          const count = getCountForType(counts, type)

          return (
            <Link key={type} to={config.route}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Icon className={`h-5 w-5 ${config.color}`} />
                    {isLoading ? (
                      <Spinner size="sm" />
                    ) : (
                      <span className="text-2xl font-bold text-light-text dark:text-dark-text">
                        {count.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    {config.label}
                  </p>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Recent Activity + Top Campaigns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity — spans 2 cols */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : recentActivity.length === 0 ? (
              <p className="text-center text-light-text-muted dark:text-dark-text-muted py-8">
                No recent activity
              </p>
            ) : (
              <div className="space-y-2">
                {recentActivity.map((item) => {
                  const config = TLO_CONFIGS[item.tloType as TLOType]
                  if (!config) return null
                  const Icon = config.icon

                  return (
                    <Link
                      key={`${item.tloType}-${item.id}`}
                      to={`${config.route}/${item.id}`}
                      className="flex items-center gap-3 p-3 rounded border border-light-border dark:border-dark-border hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                    >
                      <Icon className={`h-4 w-4 flex-shrink-0 ${config.color}`} />
                      <span className="font-mono text-sm truncate flex-1">{item.displayValue}</span>
                      <Badge variant="info">{config.singular}</Badge>
                      {item.analyst && (
                        <span className="text-xs text-light-text-muted dark:text-dark-text-muted hidden sm:inline">
                          {item.analyst}
                        </span>
                      )}
                      {item.modified && (
                        <span className="text-xs text-light-text-muted dark:text-dark-text-muted hidden sm:inline">
                          {formatDate(item.modified)}
                        </span>
                      )}
                    </Link>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Campaigns — 1 col */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Top Campaigns</CardTitle>
              <Link
                to="/campaigns"
                className="text-sm text-crits-blue hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : topCampaigns.length === 0 ? (
              <p className="text-center text-light-text-muted dark:text-dark-text-muted py-8">
                No campaigns yet
              </p>
            ) : (
              <div className="space-y-3">
                {topCampaigns.map((campaign) => (
                  <div key={campaign.name}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                        {campaign.name}
                      </span>
                      <span className="text-xs text-light-text-muted dark:text-dark-text-muted ml-2">
                        {campaign.count} objects
                      </span>
                    </div>
                    <div className="w-full bg-light-bg-secondary dark:bg-dark-bg-secondary rounded-full h-2">
                      <div
                        className="bg-crits-blue h-2 rounded-full transition-all"
                        style={{ width: `${(campaign.count / maxCampaignCount) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
