# React UI Architecture

This document covers the React frontend architecture, the config-driven TLO system, GraphQL integration, and how to modify or extend the UI.

---

## Directory Structure

```
ui/src/
├── App.tsx                    # Routes (auto-generated from TLO config)
├── main.tsx                   # React entry point
├── components/
│   ├── layout/
│   │   ├── Layout.tsx         # App shell (header + sidebar + outlet)
│   │   ├── Header.tsx         # Top nav bar
│   │   └── Sidebar.tsx        # Left nav (auto-generated from TLO config)
│   └── ui/                    # Reusable UI primitives
│       ├── Badge.tsx          # Status/tag badges (variants: default, success, warning, error, info)
│       ├── Button.tsx         # Buttons (variants: default, primary, ghost, danger; sizes: sm, md, lg)
│       ├── Card.tsx           # Card, CardHeader, CardTitle, CardContent
│       ├── Input.tsx          # Form input with label/error support
│       ├── Spinner.tsx        # Loading spinner (sizes: sm, md, lg) + LoadingOverlay
│       ├── Table.tsx          # Table, TableHeader, TableBody, TableRow, TableHead, TableCell
│       └── index.ts           # Barrel export
├── contexts/
│   ├── AuthContext.tsx         # Authentication state (session-based, Django backend)
│   └── ThemeContext.tsx        # Dark/light mode toggle
├── hooks/
│   ├── useTLOList.ts          # Generic list data fetching hook
│   └── useTLODetail.ts        # Generic detail data fetching hook
├── lib/
│   ├── graphql.ts             # GraphQL client (graphql-request + raw fetch helper)
│   ├── tloConfig.ts           # TLO configuration registry (central config for all 16 types)
│   └── utils.ts               # Utilities: cn(), formatDate(), truncate()
├── pages/
│   ├── DashboardPage.tsx      # Overview with stat cards + recent indicators
│   ├── LoginPage.tsx          # Authentication page
│   ├── TLOListPage.tsx        # Generic list page (driven by TLOConfig)
│   └── TLODetailPage.tsx      # Generic detail page (driven by TLOConfig)
└── types/
    └── index.ts               # Shared TypeScript types (TLOType, Status, etc.)
```

---

## Config-Driven TLO System

All 16 TLO types are managed through a single configuration registry in `ui/src/lib/tloConfig.ts`. This means there is **one list page component** and **one detail page component** that render differently based on the config passed to them.

### TLOConfig Interface

Each TLO type has a config object with:

| Field | Purpose |
|-------|---------|
| `type` | TypeScript TLOType enum value (`'Indicator'`, `'Actor'`, etc.) |
| `label` / `singular` | Display names (`'Indicators'` / `'Indicator'`) |
| `icon` | Lucide icon component |
| `route` | URL path (`'/indicators'`, `'/actors'`) |
| `color` | Tailwind text color class |
| `gqlSingle` / `gqlList` / `gqlCount` | GraphQL query names (camelCase) |
| `primaryField` | Main display field (`'value'`, `'name'`, `'domain'`, etc.) |
| `listFields` | Fields to request in list queries |
| `detailQueryFields` | Fields to request in detail queries |
| `columns` | Table column definitions for list view |
| `filters` | Filter definitions (text search + select dropdowns) |
| `detailFields` | Field definitions for detail page |

### Adding a New TLO Type

1. Add the type to `TLOType` union in `ui/src/types/index.ts`
2. Add a config entry in `TLO_CONFIGS` in `ui/src/lib/tloConfig.ts`
3. Add the type to `TLO_NAV_ORDER` for sidebar ordering

That's it. The routing (`App.tsx`), sidebar (`Sidebar.tsx`), list page, and detail page all derive from the config automatically.

### Modifying an Existing TLO Type

To change what columns appear in a list view, edit the `columns` array in that type's config. To change filters, edit `filters`. To change what shows on the detail page, edit `detailFields` and `detailQueryFields`.

---

## GraphQL Integration

### API Pattern

The backend (Strawberry GraphQL) uses a consistent pattern for all TLO types:

```graphql
# List query - flat array with offset/limit pagination
query {
  indicators(limit: 25, offset: 0, indType: "Address - ipv4-addr", status: "New") {
    id
    value
    indType
    status
    created
    modified
  }
}

# Count query - returns integer (accepts same filters as list)
query {
  indicatorsCount(indType: "Address - ipv4-addr", status: "New")
}

# Single item query
query {
  indicator(id: "abc123") {
    id
    value
    indType
    # ... all fields
  }
}
```

**Important naming conventions:**
- Strawberry auto-converts Python `snake_case` to GraphQL `camelCase`
- `indicators_count` in Python becomes `indicatorsCount` in GraphQL
- `ind_type` becomes `indType`
- `bucket_list` becomes `bucketList`
- `raw_data_list` becomes `rawDataList` (special case for RawData)

### Available Helper Queries (for filter dropdowns)

These queries return `[String]` arrays of distinct values:

| Query | Returns |
|-------|---------|
| `indicatorTypes` | Distinct indicator type strings |
| `ipTypes` | Distinct IP type strings |
| `domainRecordTypes` | Distinct domain record type strings |
| `eventTypes` | Distinct event type strings |
| `sampleFiletypes` | Distinct sample filetype strings |
| `signatureDataTypes` | Distinct signature data type strings |
| `rawDataTypes` | Distinct raw data type strings |
| `campaignNames` | All campaign name strings |
| `targetDepartments` | Distinct target department strings |
| `targetDivisions` | Distinct target division strings |

### GraphQL Client

Two methods available in `ui/src/lib/graphql.ts`:

1. **`graphqlClient`** - `graphql-request` client (used by older code)
2. **`gqlQuery<T>(query, variables?)`** - Raw fetch helper (preferred for new code). Uses `credentials: 'include'` for session auth.

### Data Hooks

**`useTLOList(config, { page, filters })`** - Dynamically builds a GraphQL query from the config, fetches the list + count, returns `{ items, totalCount, isLoading, error }`.

**`useTLODetail(config, id)`** - Builds a detail query from config, returns `{ item, isLoading, error }`.

**`useTLOFilterOptions(queryName)`** - Fetches distinct values for select filter dropdowns.

---

## TLO Type Reference

| Type | Route | gqlList | gqlCount | gqlSingle | Primary Field | Key Filters |
|------|-------|---------|----------|-----------|---------------|-------------|
| Indicator | `/indicators` | `indicators` | `indicatorsCount` | `indicator` | `value` | `valueContains`, `indType`, `status`, `campaign` |
| Actor | `/actors` | `actors` | `actorsCount` | `actor` | `name` | `nameContains`, `status`, `campaign` |
| Backdoor | `/backdoors` | `backdoors` | `backdoorsCount` | `backdoor` | `name` | `nameContains`, `status`, `campaign` |
| Campaign | `/campaigns` | `campaigns` | `campaignsCount` | `campaign` | `name` | `nameContains`, `active`, `status` |
| Certificate | `/certificates` | `certificates` | `certificatesCount` | `certificate` | `filename` | `filenameContains`, `md5`, `status`, `campaign` |
| Domain | `/domains` | `domains` | `domainsCount` | `domain` | `domain` | `domainContains`, `recordType`, `status`, `campaign` |
| Email | `/emails` | `emails` | `emailsCount` | `email` | `subject` | `subjectContains`, `fromAddress`, `status`, `campaign` |
| Event | `/events` | `events` | `eventsCount` | `event` | `title` | `titleContains`, `eventType`, `status`, `campaign` |
| Exploit | `/exploits` | `exploits` | `exploitsCount` | `exploit` | `name` | `nameContains`, `cve`, `status`, `campaign` |
| IP | `/ips` | `ips` | `ipsCount` | `ip` | `ip` | `ipContains`, `ipType`, `status`, `campaign` |
| PCAP | `/pcaps` | `pcaps` | `pcapsCount` | `pcap` | `filename` | `filenameContains`, `md5`, `status`, `campaign` |
| RawData | `/raw-data` | `rawDataList` | `rawDataCount` | `rawData` | `title` | `titleContains`, `dataType`, `status`, `campaign` |
| Sample | `/samples` | `samples` | `samplesCount` | `sample` | `filename` | `filenameContains`, `filetype`, `md5`, `sha256`, `status`, `campaign` |
| Screenshot | `/screenshots` | `screenshots` | `screenshotsCount` | `screenshot` | `filename` | `filenameContains` |
| Signature | `/signatures` | `signatures` | `signaturesCount` | `signature` | `title` | `titleContains`, `dataType`, `status`, `campaign` |
| Target | `/targets` | `targets` | `targetsCount` | `target` | `emailAddress` | `emailContains`, `department`, `division`, `status`, `campaign` |

---

## Common Fields (All TLO Types)

All types share these fields from the backend:

```
id, description, analyst, status, tlp, created, modified,
campaigns, bucketList, sectors,
sources { name instances { method reference date analyst } },
relationships, actions, tickets
```

Type-specific fields are documented in each config's `listFields` and `detailQueryFields`.

---

## UI Components

### Badge Variants

| Variant | Use Case | Color |
|---------|----------|-------|
| `default` | General tags, New status | Gray |
| `success` | Analyzed status | Green |
| `warning` | In Progress status | Yellow |
| `error` | Deprecated status | Red |
| `info` | Type badges, tags | Blue |

### Pagination

List pages use offset/limit pagination (not cursor-based). The API enforces a max of 100 items per request. Default page size is 25.

### Filter System

Filters are URL-driven via `useSearchParams`. Two filter types:
- **text**: Free-text search input (maps to `*Contains` API params)
- **select**: Dropdown populated from either static values (`status`, `active`) or a dynamic GraphQL helper query (`optionsQuery` field in filter config)

---

## Build & Lint

```bash
cd ui
pnpm type-check    # TypeScript compilation check
pnpm lint          # ESLint + Prettier
pnpm lint --fix    # Auto-fix formatting
pnpm build         # Production build (tsc + vite)
pnpm dev           # Dev server (port 5173)
```
