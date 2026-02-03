import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Target, Globe, Server, FileCode, Users, Award, ArrowRight } from 'lucide-react'
import { gqlQuery } from '@/lib/graphql'
import { Card, CardHeader, CardTitle, CardContent, Spinner, Badge } from '@/components/ui'

const STATS_QUERY = `
  query DashboardStats {
    indicatorsCount
    domainsCount
    ipsCount
    samplesCount
    actorsCount
    campaignsCount
  }
`

interface StatsData {
  indicatorsCount: number
  domainsCount: number
  ipsCount: number
  samplesCount: number
  actorsCount: number
  campaignsCount: number
}

const RECENT_INDICATORS_QUERY = `
  query RecentIndicators {
    indicators(limit: 5) {
      id
      value
      indType
      status
      created
    }
  }
`

interface RecentIndicator {
  id: string
  value: string
  indType: string
  status: string
  created: string
}

interface RecentIndicatorsData {
  indicators: RecentIndicator[]
}

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => gqlQuery<StatsData>(STATS_QUERY),
  })

  const { data: recentData, isLoading: recentLoading } = useQuery({
    queryKey: ['recent-indicators'],
    queryFn: () => gqlQuery<RecentIndicatorsData>(RECENT_INDICATORS_QUERY),
  })

  const statCards = [
    {
      label: 'Indicators',
      value: stats?.indicatorsCount ?? 0,
      icon: Target,
      color: 'text-blue-500',
      to: '/indicators',
    },
    {
      label: 'Domains',
      value: stats?.domainsCount ?? 0,
      icon: Globe,
      color: 'text-green-500',
      to: '/domains',
    },
    {
      label: 'IPs',
      value: stats?.ipsCount ?? 0,
      icon: Server,
      color: 'text-purple-500',
      to: '/ips',
    },
    {
      label: 'Samples',
      value: stats?.samplesCount ?? 0,
      icon: FileCode,
      color: 'text-orange-500',
      to: '/samples',
    },
    {
      label: 'Actors',
      value: stats?.actorsCount ?? 0,
      icon: Users,
      color: 'text-red-500',
      to: '/actors',
    },
    {
      label: 'Campaigns',
      value: stats?.campaignsCount ?? 0,
      icon: Award,
      color: 'text-yellow-500',
      to: '/campaigns',
    },
  ]

  const recentIndicators = recentData?.indicators ?? []

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-light-text dark:text-dark-text">Dashboard</h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary">
          Overview of your threat intelligence data
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map(({ label, value, icon: Icon, color, to }) => (
          <Link key={label} to={to}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`h-5 w-5 ${color}`} />
                  {statsLoading ? (
                    <Spinner size="sm" />
                  ) : (
                    <span className="text-2xl font-bold text-light-text dark:text-dark-text">
                      {value.toLocaleString()}
                    </span>
                  )}
                </div>
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  {label}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent indicators */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Indicators</CardTitle>
            <Link
              to="/indicators"
              className="text-sm text-crits-blue hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {recentLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : recentIndicators.length === 0 ? (
            <p className="text-center text-light-text-muted dark:text-dark-text-muted py-8">
              No indicators yet
            </p>
          ) : (
            <div className="space-y-3">
              {recentIndicators.map((indicator) => (
                <Link
                  key={indicator.id}
                  to={`/indicators/${indicator.id}`}
                  className="block p-3 rounded border border-light-border dark:border-dark-border hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Target className="h-4 w-4 text-crits-blue flex-shrink-0" />
                      <span className="font-mono text-sm truncate max-w-md">{indicator.value}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="info">{indicator.indType}</Badge>
                      <Badge
                        variant={
                          indicator.status === 'Analyzed'
                            ? 'success'
                            : indicator.status === 'In Progress'
                              ? 'warning'
                              : 'default'
                        }
                      >
                        {indicator.status}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-xs text-light-text-muted dark:text-dark-text-muted mt-1 ml-7">
                    Created {new Date(indicator.created).toLocaleDateString()}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
