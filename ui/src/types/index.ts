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

// Generic list result (flat list with offset/limit pagination)
export interface ListResult<T> {
  items: T[]
  totalCount: number
}
