// TLO Types
export type TLOType =
  | 'Actor'
  | 'Backdoor'
  | 'Campaign'
  | 'Certificate'
  | 'Domain'
  | 'Email'
  | 'Event'
  | 'Exploit'
  | 'Indicator'
  | 'IP'
  | 'PCAP'
  | 'RawData'
  | 'Sample'
  | 'Screenshot'
  | 'Signature'
  | 'Target'

// Status enum
export type Status = 'New' | 'In Progress' | 'Analyzed' | 'Deprecated'

// TLP levels
export type TLPLevel = 'WHITE' | 'GREEN' | 'AMBER' | 'RED'

// Source info
export interface SourceInfo {
  name: string
  instances: SourceInstance[]
}

export interface SourceInstance {
  method: string
  reference: string
  date: string
  analyst: string
  tlp?: TLPLevel
}

// Indicator type
export interface Indicator {
  id: string
  value: string
  indicatorType: string
  status: Status
  confidence: string
  impact: string
  created: string
  modified: string
  sources: SourceInfo[]
  campaigns: string[]
  bucketList: string[]
}

// Pagination
export interface PageInfo {
  hasNextPage: boolean
  hasPreviousPage: boolean
  startCursor?: string
  endCursor?: string
  totalCount: number
}

export interface Connection<T> {
  edges: Array<{
    node: T
    cursor: string
  }>
  pageInfo: PageInfo
  totalCount: number
}
