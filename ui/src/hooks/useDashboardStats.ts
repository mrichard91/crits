import { useQuery } from '@tanstack/react-query'
import { gqlQuery } from '@/lib/graphql'

const DASHBOARD_STATS_QUERY = `
  query DashboardStats {
    dashboardStats {
      totalCount
      counts { tloType count }
      recentActivity { id tloType displayValue modified analyst }
      topCampaigns { name count }
    }
  }
`

interface TLOCount {
  tloType: string
  count: number
}

interface RecentActivityItem {
  id: string
  tloType: string
  displayValue: string
  modified: string | null
  analyst: string
}

interface TopCampaign {
  name: string
  count: number
}

export interface DashboardStats {
  totalCount: number
  counts: TLOCount[]
  recentActivity: RecentActivityItem[]
  topCampaigns: TopCampaign[]
}

interface DashboardStatsData {
  dashboardStats: DashboardStats
}

export function useDashboardStats() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => gqlQuery<DashboardStatsData>(DASHBOARD_STATS_QUERY),
    staleTime: 30_000,
  })

  return {
    stats: data?.dashboardStats ?? null,
    isLoading,
    error: error as Error | null,
  }
}
