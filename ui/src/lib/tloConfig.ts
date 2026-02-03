import type { LucideIcon } from 'lucide-react'
import {
  Target,
  Globe,
  Mail,
  Server,
  FileCode,
  Users,
  Shield,
  Bug,
  HardDrive,
  Image,
  FileText,
  Network,
  Award,
  Crosshair,
  KeyRound,
} from 'lucide-react'
import type { TLOType } from '@/types'

export interface TLOColumnDef {
  key: string // GraphQL field name (camelCase)
  label: string // Display header
  type: 'text' | 'badge' | 'date' | 'mono' | 'list'
  linkToDetail?: boolean
  truncate?: number
}

export interface TLOFilterDef {
  key: string // GraphQL parameter name (camelCase)
  label: string // Display label
  type: 'text' | 'select'
  // For select filters: GQL query name that returns string[] of distinct values
  optionsQuery?: string
}

export interface TLODetailFieldDef {
  key: string
  label: string
  type: 'text' | 'badge' | 'date' | 'mono' | 'list' | 'pre'
}

export interface TLOConfig {
  // Identity
  type: TLOType
  label: string // "Indicators", "Actors", etc.
  singular: string // "Indicator", "Actor", etc.
  icon: LucideIcon
  route: string // "/indicators", "/actors", etc.
  color: string // Tailwind text color class

  // GraphQL query names (camelCase, as Strawberry outputs)
  gqlSingle: string // "indicator", "actor", etc.
  gqlList: string // "indicators", "actors", etc.
  gqlCount: string // "indicatorsCount", "actorsCount", etc.

  // What to show as the primary display field in list view
  primaryField: string // "value", "name", "domain", etc.

  // Fields to request in list queries (camelCase)
  listFields: string[]

  // Fields to request in detail queries (camelCase)
  detailQueryFields: string[]

  // Table columns for list view
  columns: TLOColumnDef[]

  // Available filters
  filters: TLOFilterDef[]

  // Detail page field groups
  detailFields: TLODetailFieldDef[]
}

const commonListFields = ['id', 'status', 'created', 'modified']
const commonDetailFields = [
  'id',
  'status',
  'created',
  'modified',
  'description',
  'analyst',
  'tlp',
  'campaigns',
  'bucketList',
  'sectors',
  'sources { name instances { method reference date analyst } }',
]

const commonDetailDisplay: TLODetailFieldDef[] = [
  { key: 'status', label: 'Status', type: 'badge' },
  { key: 'analyst', label: 'Analyst', type: 'text' },
  { key: 'tlp', label: 'TLP', type: 'badge' },
  { key: 'created', label: 'Created', type: 'date' },
  { key: 'modified', label: 'Modified', type: 'date' },
  { key: 'description', label: 'Description', type: 'pre' },
]

const statusFilter: TLOFilterDef = {
  key: 'status',
  label: 'Status',
  type: 'select',
}

const campaignFilter: TLOFilterDef = {
  key: 'campaign',
  label: 'Campaign',
  type: 'select',
  optionsQuery: 'campaignNames',
}

export const TLO_CONFIGS: Record<TLOType, TLOConfig> = {
  Indicator: {
    type: 'Indicator',
    label: 'Indicators',
    singular: 'Indicator',
    icon: Target,
    route: '/indicators',
    color: 'text-blue-500',
    gqlSingle: 'indicator',
    gqlList: 'indicators',
    gqlCount: 'indicatorsCount',
    primaryField: 'value',
    listFields: [
      ...commonListFields,
      'value',
      'indType',
      'confidence { rating }',
      'impact { rating }',
      'campaigns',
    ],
    detailQueryFields: [
      ...commonDetailFields,
      'value',
      'indType',
      'confidence { rating analyst }',
      'impact { rating analyst }',
      'threatTypes',
      'attackTypes',
    ],
    columns: [
      { key: 'value', label: 'Value', type: 'mono', linkToDetail: true, truncate: 50 },
      { key: 'indType', label: 'Type', type: 'badge' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'confidence.rating', label: 'Confidence', type: 'text' },
      { key: 'impact.rating', label: 'Impact', type: 'text' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'valueContains', label: 'Search values', type: 'text' },
      { key: 'indType', label: 'Type', type: 'select', optionsQuery: 'indicatorTypes' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'indType', label: 'Indicator Type', type: 'badge' },
      { key: 'confidence.rating', label: 'Confidence', type: 'text' },
      { key: 'impact.rating', label: 'Impact', type: 'text' },
      { key: 'threatTypes', label: 'Threat Types', type: 'list' },
      { key: 'attackTypes', label: 'Attack Types', type: 'list' },
    ],
  },

  Actor: {
    type: 'Actor',
    label: 'Actors',
    singular: 'Actor',
    icon: Users,
    route: '/actors',
    color: 'text-red-500',
    gqlSingle: 'actor',
    gqlList: 'actors',
    gqlCount: 'actorsCount',
    primaryField: 'name',
    listFields: [...commonListFields, 'name', 'aliases', 'campaigns'],
    detailQueryFields: [
      ...commonDetailFields,
      'name',
      'aliases',
      'intendedEffects',
      'motivations',
      'sophistications',
      'threatTypes',
    ],
    columns: [
      { key: 'name', label: 'Name', type: 'text', linkToDetail: true },
      { key: 'aliases', label: 'Aliases', type: 'list' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'nameContains', label: 'Search names', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'aliases', label: 'Aliases', type: 'list' },
      { key: 'intendedEffects', label: 'Intended Effects', type: 'list' },
      { key: 'motivations', label: 'Motivations', type: 'list' },
      { key: 'sophistications', label: 'Sophistications', type: 'list' },
      { key: 'threatTypes', label: 'Threat Types', type: 'list' },
    ],
  },

  Backdoor: {
    type: 'Backdoor',
    label: 'Backdoors',
    singular: 'Backdoor',
    icon: HardDrive,
    route: '/backdoors',
    color: 'text-gray-500',
    gqlSingle: 'backdoor',
    gqlList: 'backdoors',
    gqlCount: 'backdoorsCount',
    primaryField: 'name',
    listFields: [...commonListFields, 'name', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'name'],
    columns: [
      { key: 'name', label: 'Name', type: 'text', linkToDetail: true },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'nameContains', label: 'Search names', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [...commonDetailDisplay],
  },

  Campaign: {
    type: 'Campaign',
    label: 'Campaigns',
    singular: 'Campaign',
    icon: Award,
    route: '/campaigns',
    color: 'text-yellow-500',
    gqlSingle: 'campaign',
    gqlList: 'campaigns',
    gqlCount: 'campaignsCount',
    primaryField: 'name',
    listFields: [...commonListFields, 'name', 'aliases', 'active'],
    detailQueryFields: [...commonDetailFields, 'name', 'aliases', 'active'],
    columns: [
      { key: 'name', label: 'Name', type: 'text', linkToDetail: true },
      { key: 'aliases', label: 'Aliases', type: 'list' },
      { key: 'active', label: 'Active', type: 'badge' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'nameContains', label: 'Search names', type: 'text' },
      { key: 'active', label: 'Active', type: 'select' },
      statusFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'active', label: 'Active', type: 'badge' },
      { key: 'aliases', label: 'Aliases', type: 'list' },
    ],
  },

  Certificate: {
    type: 'Certificate',
    label: 'Certificates',
    singular: 'Certificate',
    icon: KeyRound,
    route: '/certificates',
    color: 'text-teal-500',
    gqlSingle: 'certificate',
    gqlList: 'certificates',
    gqlCount: 'certificatesCount',
    primaryField: 'filename',
    listFields: [...commonListFields, 'filename', 'md5', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'filename', 'md5'],
    columns: [
      { key: 'filename', label: 'Filename', type: 'text', linkToDetail: true, truncate: 40 },
      { key: 'md5', label: 'MD5', type: 'mono', truncate: 16 },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'filenameContains', label: 'Search filenames', type: 'text' },
      { key: 'md5', label: 'MD5', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [...commonDetailDisplay, { key: 'md5', label: 'MD5', type: 'mono' }],
  },

  Domain: {
    type: 'Domain',
    label: 'Domains',
    singular: 'Domain',
    icon: Globe,
    route: '/domains',
    color: 'text-green-500',
    gqlSingle: 'domain',
    gqlList: 'domains',
    gqlCount: 'domainsCount',
    primaryField: 'domain',
    listFields: [...commonListFields, 'domain', 'recordType', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'domain', 'recordType', 'watchlistEnabled'],
    columns: [
      { key: 'domain', label: 'Domain', type: 'mono', linkToDetail: true, truncate: 50 },
      { key: 'recordType', label: 'Record Type', type: 'badge' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'domainContains', label: 'Search domains', type: 'text' },
      {
        key: 'recordType',
        label: 'Record Type',
        type: 'select',
        optionsQuery: 'domainRecordTypes',
      },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'recordType', label: 'Record Type', type: 'badge' },
      { key: 'watchlistEnabled', label: 'Watchlist', type: 'text' },
    ],
  },

  Email: {
    type: 'Email',
    label: 'Emails',
    singular: 'Email',
    icon: Mail,
    route: '/emails',
    color: 'text-cyan-500',
    gqlSingle: 'email',
    gqlList: 'emails',
    gqlCount: 'emailsCount',
    primaryField: 'subject',
    listFields: [...commonListFields, 'subject', 'fromAddress', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'subject', 'fromAddress'],
    columns: [
      { key: 'subject', label: 'Subject', type: 'text', linkToDetail: true, truncate: 50 },
      { key: 'fromAddress', label: 'From', type: 'mono', truncate: 30 },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'subjectContains', label: 'Search subjects', type: 'text' },
      { key: 'fromAddress', label: 'From address', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'fromAddress', label: 'From Address', type: 'mono' },
    ],
  },

  Event: {
    type: 'Event',
    label: 'Events',
    singular: 'Event',
    icon: Shield,
    route: '/events',
    color: 'text-indigo-500',
    gqlSingle: 'event',
    gqlList: 'events',
    gqlCount: 'eventsCount',
    primaryField: 'title',
    listFields: [...commonListFields, 'title', 'eventType', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'title', 'eventType', 'eventId'],
    columns: [
      { key: 'title', label: 'Title', type: 'text', linkToDetail: true, truncate: 50 },
      { key: 'eventType', label: 'Event Type', type: 'badge' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'titleContains', label: 'Search titles', type: 'text' },
      { key: 'eventType', label: 'Event Type', type: 'select', optionsQuery: 'eventTypes' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'eventType', label: 'Event Type', type: 'badge' },
      { key: 'eventId', label: 'Event ID', type: 'mono' },
    ],
  },

  Exploit: {
    type: 'Exploit',
    label: 'Exploits',
    singular: 'Exploit',
    icon: Bug,
    route: '/exploits',
    color: 'text-rose-500',
    gqlSingle: 'exploit',
    gqlList: 'exploits',
    gqlCount: 'exploitsCount',
    primaryField: 'name',
    listFields: [...commonListFields, 'name', 'cve', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'name', 'cve'],
    columns: [
      { key: 'name', label: 'Name', type: 'text', linkToDetail: true },
      { key: 'cve', label: 'CVE', type: 'mono' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'nameContains', label: 'Search names', type: 'text' },
      { key: 'cve', label: 'CVE', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [...commonDetailDisplay, { key: 'cve', label: 'CVE', type: 'mono' }],
  },

  IP: {
    type: 'IP',
    label: 'IPs',
    singular: 'IP',
    icon: Server,
    route: '/ips',
    color: 'text-purple-500',
    gqlSingle: 'ip',
    gqlList: 'ips',
    gqlCount: 'ipsCount',
    primaryField: 'ip',
    listFields: [...commonListFields, 'ip', 'ipType', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'ip', 'ipType'],
    columns: [
      { key: 'ip', label: 'IP Address', type: 'mono', linkToDetail: true },
      { key: 'ipType', label: 'Type', type: 'badge' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'ipContains', label: 'Search IPs', type: 'text' },
      { key: 'ipType', label: 'Type', type: 'select', optionsQuery: 'ipTypes' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [...commonDetailDisplay, { key: 'ipType', label: 'IP Type', type: 'badge' }],
  },

  PCAP: {
    type: 'PCAP',
    label: 'PCAPs',
    singular: 'PCAP',
    icon: Network,
    route: '/pcaps',
    color: 'text-amber-500',
    gqlSingle: 'pcap',
    gqlList: 'pcaps',
    gqlCount: 'pcapsCount',
    primaryField: 'filename',
    listFields: [...commonListFields, 'filename', 'md5', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'filename', 'md5'],
    columns: [
      { key: 'filename', label: 'Filename', type: 'text', linkToDetail: true, truncate: 40 },
      { key: 'md5', label: 'MD5', type: 'mono', truncate: 16 },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'filenameContains', label: 'Search filenames', type: 'text' },
      { key: 'md5', label: 'MD5', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [...commonDetailDisplay, { key: 'md5', label: 'MD5', type: 'mono' }],
  },

  RawData: {
    type: 'RawData',
    label: 'Raw Data',
    singular: 'Raw Data',
    icon: FileText,
    route: '/raw-data',
    color: 'text-stone-500',
    gqlSingle: 'rawData',
    gqlList: 'rawDataList',
    gqlCount: 'rawDataCount',
    primaryField: 'title',
    listFields: [...commonListFields, 'title', 'dataType', 'version', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'title', 'dataType', 'data', 'md5', 'version'],
    columns: [
      { key: 'title', label: 'Title', type: 'text', linkToDetail: true, truncate: 50 },
      { key: 'dataType', label: 'Data Type', type: 'badge' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'titleContains', label: 'Search titles', type: 'text' },
      { key: 'dataType', label: 'Data Type', type: 'select', optionsQuery: 'rawDataTypes' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'dataType', label: 'Data Type', type: 'badge' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'md5', label: 'MD5', type: 'mono' },
    ],
  },

  Sample: {
    type: 'Sample',
    label: 'Samples',
    singular: 'Sample',
    icon: FileCode,
    route: '/samples',
    color: 'text-orange-500',
    gqlSingle: 'sample',
    gqlList: 'samples',
    gqlCount: 'samplesCount',
    primaryField: 'filename',
    listFields: [...commonListFields, 'filename', 'filetype', 'md5', 'size', 'campaigns'],
    detailQueryFields: [
      ...commonDetailFields,
      'filename',
      'filenames',
      'filetype',
      'mimetype',
      'size',
      'md5',
      'sha1',
      'sha256',
      'ssdeep',
    ],
    columns: [
      { key: 'filename', label: 'Filename', type: 'text', linkToDetail: true, truncate: 40 },
      { key: 'filetype', label: 'File Type', type: 'badge' },
      { key: 'md5', label: 'MD5', type: 'mono', truncate: 16 },
      { key: 'size', label: 'Size', type: 'text' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'filenameContains', label: 'Search filenames', type: 'text' },
      { key: 'filetype', label: 'File Type', type: 'select', optionsQuery: 'sampleFiletypes' },
      { key: 'md5', label: 'MD5', type: 'text' },
      { key: 'sha256', label: 'SHA256', type: 'text' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'filetype', label: 'File Type', type: 'badge' },
      { key: 'mimetype', label: 'MIME Type', type: 'text' },
      { key: 'size', label: 'Size', type: 'text' },
      { key: 'md5', label: 'MD5', type: 'mono' },
      { key: 'sha1', label: 'SHA1', type: 'mono' },
      { key: 'sha256', label: 'SHA256', type: 'mono' },
      { key: 'ssdeep', label: 'SSDeep', type: 'mono' },
      { key: 'filenames', label: 'Filenames', type: 'list' },
    ],
  },

  Screenshot: {
    type: 'Screenshot',
    label: 'Screenshots',
    singular: 'Screenshot',
    icon: Image,
    route: '/screenshots',
    color: 'text-pink-500',
    gqlSingle: 'screenshot',
    gqlList: 'screenshots',
    gqlCount: 'screenshotsCount',
    primaryField: 'filename',
    listFields: [...commonListFields, 'filename'],
    detailQueryFields: [...commonDetailFields, 'filename'],
    columns: [
      { key: 'filename', label: 'Filename', type: 'text', linkToDetail: true, truncate: 50 },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [{ key: 'filenameContains', label: 'Search filenames', type: 'text' }],
    detailFields: [...commonDetailDisplay],
  },

  Signature: {
    type: 'Signature',
    label: 'Signatures',
    singular: 'Signature',
    icon: Crosshair,
    route: '/signatures',
    color: 'text-lime-500',
    gqlSingle: 'signature',
    gqlList: 'signatures',
    gqlCount: 'signaturesCount',
    primaryField: 'title',
    listFields: [...commonListFields, 'title', 'dataType', 'version', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'title', 'dataType', 'data', 'md5', 'version'],
    columns: [
      { key: 'title', label: 'Title', type: 'text', linkToDetail: true, truncate: 50 },
      { key: 'dataType', label: 'Data Type', type: 'badge' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'titleContains', label: 'Search titles', type: 'text' },
      { key: 'dataType', label: 'Data Type', type: 'select', optionsQuery: 'signatureDataTypes' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'dataType', label: 'Data Type', type: 'badge' },
      { key: 'version', label: 'Version', type: 'text' },
      { key: 'md5', label: 'MD5', type: 'mono' },
    ],
  },

  Target: {
    type: 'Target',
    label: 'Targets',
    singular: 'Target',
    icon: Target,
    route: '/targets',
    color: 'text-emerald-500',
    gqlSingle: 'target',
    gqlList: 'targets',
    gqlCount: 'targetsCount',
    primaryField: 'emailAddress',
    listFields: [...commonListFields, 'emailAddress', 'department', 'division', 'campaigns'],
    detailQueryFields: [...commonDetailFields, 'emailAddress', 'department', 'division'],
    columns: [
      { key: 'emailAddress', label: 'Email', type: 'mono', linkToDetail: true, truncate: 40 },
      { key: 'department', label: 'Department', type: 'text' },
      { key: 'division', label: 'Division', type: 'text' },
      { key: 'status', label: 'Status', type: 'badge' },
      { key: 'campaigns', label: 'Campaigns', type: 'list' },
      { key: 'modified', label: 'Modified', type: 'date' },
    ],
    filters: [
      { key: 'emailContains', label: 'Search emails', type: 'text' },
      { key: 'department', label: 'Department', type: 'select', optionsQuery: 'targetDepartments' },
      { key: 'division', label: 'Division', type: 'select', optionsQuery: 'targetDivisions' },
      statusFilter,
      campaignFilter,
    ],
    detailFields: [
      ...commonDetailDisplay,
      { key: 'department', label: 'Department', type: 'text' },
      { key: 'division', label: 'Division', type: 'text' },
    ],
  },
}

// Ordered list for sidebar navigation
export const TLO_NAV_ORDER: TLOType[] = [
  'Indicator',
  'Domain',
  'IP',
  'Email',
  'Sample',
  'Actor',
  'Campaign',
  'Event',
  'Exploit',
  'Backdoor',
  'PCAP',
  'RawData',
  'Certificate',
  'Screenshot',
  'Signature',
  'Target',
]

// Helper to get config by route path
export function getConfigByRoute(path: string): TLOConfig | undefined {
  return Object.values(TLO_CONFIGS).find((c) => c.route === path)
}
