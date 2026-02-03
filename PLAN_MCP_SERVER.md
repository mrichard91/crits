# Plan: CRITs MCP Server

## Overview

Create an MCP (Model Context Protocol) server that exposes CRUD operations for all 16 CRITs TLO types as tools. This allows LLM-based agents (Claude, etc.) to query and create threat intelligence objects directly.

## Scope

- **List** (with filters/pagination) for all 16 TLO types
- **Get** (by ID) for all 16 TLO types
- **Count** (with filters) for all 16 TLO types
- **Create** for the 15 types that support it (all except Screenshot)
- **Source names** query (needed for create operations)
- No auth/admin endpoints — the server authenticates via a configured API session/token

## Architecture

### Transport & Auth
- Runs as a **stdio MCP server** (local process, launched by the MCP client)
- Communicates with the CRITs GraphQL API over HTTP (same as the UI does)
- Auth: uses a configured session cookie or API token passed via environment variable

### Tech Stack
- Python (matches existing backend)
- `mcp` SDK (`pip install mcp`)
- `httpx` for GraphQL HTTP calls
- Reuses the same GraphQL queries/mutations the UI uses

### Tool Design

Each TLO type gets up to 4 tools. Naming convention: `crits_{operation}_{type}`

**Example for Indicators:**
- `crits_list_indicators` — params: filters (valueContains, indType, status, campaign), offset, limit
- `crits_get_indicator` — params: id
- `crits_count_indicators` — params: same filters as list
- `crits_create_indicator` — params: value, indType, source, threatType?, attackType?, description?, campaign?

**For file-upload types (Sample, PCAP, Certificate):**
- Create tools accept a `file_path` param (local path) — the MCP server reads the file and performs the multipart upload

**Total: ~64 tools** (16 types x 4 ops, minus Screenshot create)

### File Structure

```
crits_mcp/
  __init__.py
  server.py          # MCP server entry point, tool registration
  client.py          # GraphQL HTTP client (gqlQuery, gqlUploadMutation)
  tools/
    __init__.py
    queries.py        # Generic list/get/count tool builders
    mutations.py      # Generic create tool builders
  config.py           # TLO type definitions (fields, filters, mutations) — similar to tloConfig.ts
  README.md           # Setup instructions
```

### Config-Driven Approach

Like the frontend's `tloConfig.ts`, define each TLO type's fields/filters/create params in a Python dict. Tool registration loops over this config to generate all tools, avoiding 64 hand-written tool definitions.

## Implementation Phases

### Phase 1: Core infrastructure
- MCP server scaffold with `mcp` SDK
- GraphQL client with session auth
- Config structure for TLO types

### Phase 2: Read tools
- Generic list/get/count tool factory
- Register tools for all 16 types
- Test with Claude Desktop or MCP inspector

### Phase 3: Create tools (text-based)
- Generic create tool factory for text-only types (12 types)
- Register tools for Indicator, Actor, Backdoor, Campaign, Domain, Email, Event, Exploit, IP, Target, RawData, Signature

### Phase 4: Create tools (file upload)
- Multipart upload support in GraphQL client
- Create tools for Sample, PCAP, Certificate (accept file_path, read file, upload)

## Status: NOT STARTED
