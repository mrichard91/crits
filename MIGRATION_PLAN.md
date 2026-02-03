# CRITs Modernization Migration Plan

## Executive Summary

This document outlines the comprehensive migration of CRITs from a Python 2.7/Django 1.x application to a modern Python 3.12+/FastAPI/React stack. The migration preserves the core functionality and visual identity while modernizing the architecture for maintainability, performance, and security.

### Original State (Pre-Migration)
- **Backend**: Python 2.7, Django 1.x, Tastypie REST API
- **Frontend**: Server-side Django templates, jQuery 1.10, jTable
- **Database**: MongoDB via MongoEngine 0.8.9 (patched)
- **Auth**: Custom CRITs auth, optional LDAP, TOTP
- **Tasks**: Celery with django-celery, thread/process pools
- **Deploy**: Single Dockerfile (dev), Apache/mod_wsgi (prod)

### Current State (Phase 1-5a Complete)
- **Backend**: Python 3.12, Django 4.2 (working), Tastypie disabled
- **API**: FastAPI + Strawberry GraphQL at `/api/graphql` ✅
- **Frontend**: Django templates (legacy) + React 18 UI at `/app/` (new) ✅
- **Database**: MongoDB 7.x via MongoEngine 0.28+, PyMongo 4.6+
- **Auth**: CRITs auth (working), shared Django sessions via Redis ✅
- **Tasks**: Celery 5.3+ with Redis broker
- **Deploy**: Docker Compose stack (nginx, web, api, ui, mongo, redis) ✅

### Target State (Incremental)
- **Backend**: Django 4.2 (legacy UI) + FastAPI (GraphQL API) running side-by-side
- **API**: Strawberry GraphQL with FastAPI, replacing Tastypie REST
- **Frontend**: React 18+ (future), consuming GraphQL API
- **Database**: MongoDB via MongoEngine (shared with Django), optimized queries
- **Auth**: Shared session/JWT between Django and FastAPI
- **Caching**: Redis with 15-minute default TTL, mutation-based invalidation
- **Deploy**: Docker Compose with nginx routing `/api/graphql` → FastAPI

### Architecture Decision: Side-by-Side Operation

**Rationale**: Rather than a "big bang" replacement, we run Django and FastAPI concurrently:

1. **nginx** routes requests:
   - `/api/graphql` → FastAPI (new GraphQL API)
   - `/app/` → React UI (new frontend)
   - `/*` → Django (existing web UI)

2. **Shared MongoEngine models**: FastAPI uses the same models as Django, no data migration needed

3. **Shared authentication**: User sessions/tokens work across both services

4. **Incremental migration**: New React UI can be built against GraphQL while Django UI remains functional

---

## Phase 1: Python 3.12 Migration & Project Modernization ✅ COMPLETE

### 1a. Create pyproject.toml and Modern Project Structure ✅
- [x] Create `pyproject.toml` with project metadata, Python 3.12+ requirement
- [x] Define dependencies with version constraints (split dev/prod)
- [x] Configure build system (hatchling or setuptools)
- [x] Add tool configurations (ruff, mypy, pytest)
- [ ] Create `src/` directory structure for new code (deferred - using existing structure)

### 1b. Set Up Development Environment ✅
- [x] Create `requirements-legacy.txt` snapshot of current deps
- [x] Add `.python-version` file for pyenv (3.12.x)
- [x] Create `Makefile` with common commands (install, lint, test, run)
- [x] Set up pre-commit hooks configuration (ruff, mypy, trailing whitespace)
- [ ] Add VS Code / PyCharm project settings (optional)

### 1c. Python 2 to 3 Syntax Migration - Core Module ✅
- [x] Fix print statements → print() functions
- [x] Fix unicode/str handling (removed .decode() on strings)
- [x] Update dict methods (.keys(), .values(), .items() return views)
- [x] Fix integer division (// vs /)
- [x] Update exception syntax (except E as e:)
- [x] Fix imports (ConfigParser, urllib, etc.)
- [x] Replace `cgi.escape()` with `html.escape()`

### 1d. Python 2 to 3 Syntax Migration - App Modules ✅
- [x] All 27 TLO modules migrated and working with Python 3.12
- [x] Fixed `{% ifequal %}` / `{% ifnotequal %}` → `{% if %}` in templates
- [x] Fixed `is_ajax()` removal in Django 4.0+ (compatibility shim added)
- [x] Fixed `Cursor.count()` → `count_documents()` for PyMongo 4.0+
- [x] Fixed `is_safe_url()` → added `allowed_hosts` parameter

### 1e. Update Dependencies to Python 3 Compatible Versions ✅
- [x] Update MongoEngine to 0.28+ (Python 3 compatible)
- [x] Update PyMongo to 4.6+ (Python 3.12 compatible)
- [x] Update Django to 4.2 LTS
- [x] Replace pycrypto with cryptography library
- [x] Update Pillow to 10.x
- [x] Update python-magic to latest
- [x] Update lxml to latest
- [x] Update requests to latest
- [x] Update PyYAML to latest
- [x] Update celery to 5.3+
- [x] Update python-dateutil to latest
- [x] Remove/replace deprecated packages (simplejson, anyjson)

### 1f. Fix MongoEngine Compatibility Issues ✅
- [x] Update Document class definitions for new API
- [x] Fix queryset operations (no_dereference, etc.)
- [x] Update field definitions (StringField, etc.)
- [x] Fix GridFS file handling for new API
- [x] Update connection management code
- [x] Test all model save/load operations

### 1g. Validate Python 3.12 Migration ✅
- [x] Core functionality working (login, dashboard, domains, users)
- [x] Add type hints to crits_api modules (PR #17)
- [x] Configure mypy with strict mode for crits_api/
- [x] Set up pre-commit hooks (ruff lint/format, mypy, trailing whitespace)
- [x] Fix Python 2 `unicode` type references throughout codebase (PR #16)
- [ ] Comprehensive test coverage (deferred to Phase 8)

---

## Phase 2: Docker Stack Foundation ✅ COMPLETE

### 2a. Create Base Docker Infrastructure ✅
- [x] Create `docker/` directory structure
- [x] Write `docker/Dockerfile.web` (Python 3.12 Django + Gunicorn)
- [x] Write `docker/Dockerfile.api` (FastAPI - Phase 3)
- [x] Write `docker/Dockerfile.ui` (Node 20 + pnpm + nginx - Phase 5)
- [x] Create `.dockerignore` with proper exclusions
- [x] Create `docker/nginx.conf` for reverse proxy (routes `/app/` → React, `/api/` → FastAPI)

### 2b. Create Docker Compose Configuration ✅
- [x] Write `docker-compose.yml` for development
- [ ] Write `docker-compose.prod.yml` for production (deferred)
- [x] Configure MongoDB service with persistence
- [x] Configure Redis service for caching/broker
- [x] Configure nginx service (SSL deferred to production)
- [x] Add healthchecks for all services
- [x] Configure named volumes for data persistence
- [x] Set up inter-service networking

### 2c. Create Environment Configuration ✅
- [x] Document environment variables in docker-compose.yml
- [x] Configure CSRF_TRUSTED_ORIGINS for proxy setup
- [x] Configure SECURE_COOKIES for HTTP development
- [ ] Add secrets management approach (deferred to production)
- [ ] Configure MongoDB authentication (deferred to production)
- [ ] Configure Redis authentication (deferred to production)

### 2d. Database Migration Scripts (Partial)
- [x] Create MongoDB initialization via Django management commands
- [ ] Create index creation script for collections (Phase 3)
- [x] Data migration not needed (same MongoDB, same models)
- [ ] Add backup/restore utilities (deferred)
- [ ] Create seed data for development (deferred)

---

## Phase 3: FastAPI + Strawberry GraphQL API ✅ COMPLETE

> **Architecture Decision**: The GraphQL API runs alongside Django, sharing MongoEngine models.
> nginx routes `/api/graphql` to FastAPI while Django serves the legacy UI.

### 3a. FastAPI Application Structure ✅
- [x] Create `crits_api/` package in project root
- [x] Create `crits_api/main.py` with FastAPI app
- [x] Create `crits_api/config.py` with Pydantic settings
- [x] Set up CORS middleware (allow Django frontend origin)
- [x] Set up exception handling middleware
- [x] Create health check endpoint (`/api/health`)
- [x] Create `docker/Dockerfile.api` for FastAPI service
- [x] Update `docker-compose.yml` with api service
- [x] Update `docker/nginx.conf` to route `/api/graphql` → FastAPI

### 3b. Shared MongoEngine Models (No Migration) ✅

> **Key Decision**: Reuse existing MongoEngine models from `crits/` instead of creating Beanie models.
> This allows Django and FastAPI to share the same data layer without data migration.

- [x] Import MongoEngine models from `crits/` directly in resolvers
- [x] Django setup initializes MongoEngine connection for FastAPI
- [x] Verified MongoEngine works in FastAPI context (sync driver)

### 3c. Authentication & Request Context ✅

> **Key Requirement**: Share authentication with Django; populate request context with user details.

- [x] Create `crits_api/auth/` package
- [x] Create `context.py` with `GraphQLContext` class containing:
  - `user: CRITsUser` - authenticated user object
  - `acl: dict` - merged permissions from user's roles
  - `sources: list` - user's accessible sources by TLP level
  - `sources_hash: str` - hash for cache key generation
  - `request: Request` - FastAPI request object
- [x] Create `session.py` with Django session validation:
  - Read `sessionid` cookie from request
  - Load session from Redis (supports both pickle and JSON deserialization)
  - Resolve `_auth_user_id` to CRITsUser
  - Fallback to Django SessionStore for compatibility
- [x] Create `permissions.py` with permission check utilities:
  - `require_permission(acl_string)` - decorator for resolvers
  - `require_authenticated` - decorator for auth-required resolvers
  - `check_source_access(user, sources, tlp)` - source/TLP filter
  - `filter_by_sources(queryset, user)` - query-level filtering
- [x] Update Django to use Redis-backed sessions for sharing

### 3d. Permission Replication from Django ✅

> **Key Requirement**: Apply the same permission checks as Django code.

**Permission Model (from `crits/core/role.py` and `crits/core/user.py`):**

| Permission Type | Example | Check Method |
|----------------|---------|--------------|
| Interface Access | `api_interface` | `user.has_access_to(GeneralACL.API_INTERFACE)` |
| TLO Read/Write | `Sample.read` | `user.has_access_to(SampleACL.READ)` |
| Sub-object Access | `Sample.comments_add` | `user.has_access_to(SampleACL.COMMENTS_ADD)` |
| Source Access | read + TLP level | `user.check_source_tlp(object)` |
| Superuser | all | `user.is_superuser` bypasses checks |

- [x] Reuse `user.has_access_to()` via GraphQLContext
- [x] Reuse `user.filter_dict_source_tlp()` for query-level filtering
- [x] Create resolver decorators: `@require_permission`, `@require_authenticated`
- [x] Source/TLP filtering applied in indicator queries

### 3e. Redis Caching Strategy (Foundation)

> **Key Requirement**: 15-minute default TTL, mutation-based invalidation.

- [x] Create `crits_api/cache/` package structure
- [x] Create `redis_client.py` with async Redis connection
- [x] Create `keys.py` with cache key generation (includes user_sources_hash)
- [x] Create `decorators.py` with `@cached` and `@invalidates` decorators
- [ ] Implement cache invalidation on mutations (Phase 4)
- [ ] Add cache hit/miss metrics logging

### 3f. MongoDB Query Optimization (Foundation)

> **Key Requirement**: Don't assume old Django code is optimal. Optimize queries.

- [x] Create `crits_api/db/` package with connection utilities
- [x] Use `.order_by()` for consistent pagination
- [x] Implement offset-based pagination (cursor-based deferred)
- [ ] Implement DataLoader pattern for relationship resolution (Phase 4)
- [ ] Add MongoDB indexes for GraphQL query patterns (Phase 4)
- [ ] Monitor and log slow queries (>100ms)

### 3g. Architecture Summary (Phase 3)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              nginx (:8080)                               │
│  ┌────────────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
│  │ /api/ → api:8001   │  │ /app/ → ui:80    │  │ /* → web:8000       │  │
│  │ (FastAPI/GraphQL)   │  │ (React/nginx)    │  │ (Django legacy)     │  │
│  └────────────────────┘  └──────────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  FastAPI + Strawberry│  │  React 18 + Vite    │  │  Django 4.2         │
│  (:8001)            │  │  (static via nginx)  │  │  (:8000)            │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ GraphQL Schema│  │  │  │ Tailwind CSS  │  │  │  │ Views/Forms   │  │
│  └───────────────┘  │  │  │ Dark/Light    │  │  │  └───────────────┘  │
│  ┌───────────────┐  │  │  └───────────────┘  │  │  ┌───────────────┐  │
│  │ Auth Context  │◄─┼──┼──┐ fetch() w/    │  │  │  │ Sessions      │──┼─┐
│  └───────────────┘  │  │  │ credentials   │  │  │  └───────────────┘  │ │
│  ┌───────────────┐  │  │  └───────────────┘  │  │  ┌───────────────┐  │ │
│  │ Caching Layer │  │  │  ┌───────────────┐  │  │  │ Templates     │  │ │
│  └───────────────┘  │  │  │ pnpm (supply  │  │  │  └───────────────┘  │ │
└─────────┬───────────┘  │  │ chain secure) │  │  └─────────┬───────────┘ │
          │              │  └───────────────┘  │            │             │
          │              └─────────────────────┘            │             │
          │         ┌───────────────┐                       │             │
          │         │  MongoEngine  │                       │             │
          └────────►│   (shared)    │◄──────────────────────┘             │
                    └───────┬───────┘                                     │
                            │                                             │
                    ┌───────▼───────┐     ┌─────────────────────┐         │
                    │  MongoDB 7.x  │     │  Redis 7.x          │◄────────┘
                    └───────────────┘     │  - Session store    │
                                          │  - GraphQL cache    │
                                          │  - (15-min TTL)     │
                                          └─────────────────────┘
```

**Key Integration Points:**
1. **nginx** routes `/api/` to FastAPI, `/app/` to React UI, everything else to Django
2. **Session sharing**: FastAPI reads Django's `sessionid` cookie from Redis
3. **MongoEngine models**: Shared between Django and FastAPI (no duplication)
4. **Cache layer**: FastAPI uses Redis for 15-minute query caching
5. **Permission checks**: Both services use same ACL logic from `crits/core/`
6. **React UI**: Uses `fetch()` with `credentials: 'include'` to call GraphQL API via same-origin cookie auth
7. **Supply chain security**: pnpm 10.28.2 enforced for all frontend dependency management

---

## Phase 4: Strawberry GraphQL Schema Implementation ✅ COMPLETE (Core)

> **Dependencies**: Phase 3 (FastAPI foundation, auth context, caching)

### 4a. GraphQL Schema Foundation ✅
- [x] Install `strawberry-graphql[fastapi]` dependency
- [x] Create `crits_api/graphql/` package
- [x] Create `schema.py` with root `Query` and `Mutation` types
- [x] Create `context.py` with `get_context()` dependency
- [x] Mount GraphQL at `/api/graphql` on FastAPI app
- [x] Configure GraphiQL playground (dev only)
- [ ] Create `dataloaders.py` with DataLoader instances for each TLO
- [ ] Add query depth limiting (max 10 levels)
- [ ] Add query complexity limiting

### 4b. GraphQL Types - Core ✅
- [x] Create `crits_api/graphql/types/` package
- [x] Create `user.py` with `UserType` (excludes sensitive fields)
- [x] Create `common.py` with shared types:
  - `ObjectID` scalar (MongoDB ObjectId)
  - `DateTime` scalar (ISO8601)
  - `TLPLevel` enum (WHITE, GREEN, AMBER, RED)
  - `TLOType` enum (all 16 TLO types)
  - `SourceInfo` and `SourceInstance` types
  - `EmbeddedCampaignType`, `EmbeddedRelationshipType`, `EmbeddedActionType`
- [x] Create `pagination.py` with basic pagination types
- [ ] Create `role.py` with `RoleType` and `PermissionType`
- [ ] Create `comment.py` with `CommentType` (comments are in relationships currently)

### 4c. GraphQL Types - TLOs (16 Types) ✅

Each TLO type includes:
- Core fields from MongoEngine model
- Relationship resolvers (campaigns, comments, related objects)
- Permission-aware field resolvers for sensitive data
- Source/TLP filtering on nested collections

- [x] Create `actor.py` with `ActorType`
- [x] Create `backdoor.py` with `BackdoorType`
- [x] Create `campaign.py` with `CampaignType`
- [x] Create `certificate.py` with `CertificateType`
- [x] Create `domain.py` with `DomainType`
- [x] Create `email_type.py` with `EmailType` (avoid `email.py` collision)
- [x] Create `event.py` with `EventType`
- [x] Create `exploit.py` with `ExploitType`
- [x] Create `indicator.py` with `IndicatorType`
- [x] Create `ip.py` with `IPType`
- [x] Create `pcap.py` with `PCAPType`
- [x] Create `raw_data.py` with `RawDataType`
- [x] Create `sample.py` with `SampleType`
- [x] Create `screenshot.py` with `ScreenshotType`
- [x] Create `signature.py` with `SignatureType`
- [x] Create `target.py` with `TargetType`

### 4d. GraphQL Queries ✅ (Core Complete)

**Single Object Queries** (16 queries):
```graphql
actor(id: ID!): Actor
domain(id: ID!): Domain
sample(id: ID!): Sample
# ... etc for each TLO
```

**List Queries with Pagination** (16 queries):
```graphql
actors(first: Int, after: String, filter: ActorFilter): ActorConnection!
domains(first: Int, after: String, filter: DomainFilter): DomainConnection!
samples(first: Int, after: String, filter: SampleFilter): SampleConnection!
# ... etc for each TLO
```

**Special Queries**:
```graphql
# Global search across all TLOs
search(query: String!, types: [TLOType!], first: Int): SearchResultConnection!

# Dashboard statistics
dashboardStats: DashboardStats!

# Current user info
me: User!

# Relationship traversal
relatedObjects(id: ID!, type: TLOType!, depth: Int = 1): [RelatedObject!]!
```

- [x] Create `crits_api/graphql/queries/` package
- [x] Implement single-object queries with permission checks
- [x] Implement list queries with offset-based pagination
- [x] Implement filter parameters for each TLO (type, status, campaign, value search)
- [x] Implement count queries for each TLO
- [x] Implement `me` query for current user
- [ ] Implement `search` query with MongoDB text search
- [ ] Implement `dashboardStats` with aggregation pipeline
- [ ] Implement `relatedObjects` with depth limiting
- [ ] Migrate to cursor-based pagination (optional enhancement)

### 4e. GraphQL Mutations

**CRUD Mutations per TLO** (pattern for each):
```graphql
type Mutation {
  createDomain(input: CreateDomainInput!): DomainMutationResult!
  updateDomain(id: ID!, input: UpdateDomainInput!): DomainMutationResult!
  deleteDomain(id: ID!): DeleteResult!
}
```

**Relationship Mutations**:
```graphql
addRelationship(fromId: ID!, fromType: TLOType!, toId: ID!, toType: TLOType!, relType: String!): RelationshipResult!
removeRelationship(id: ID!): DeleteResult!
```

**Comment Mutations**:
```graphql
addComment(objectId: ID!, objectType: TLOType!, comment: String!): CommentResult!
editComment(id: ID!, comment: String!): CommentResult!
deleteComment(id: ID!): DeleteResult!
```

**Bulk Operations**:
```graphql
bulkAddToCampaign(ids: [ID!]!, types: [TLOType!]!, campaignId: ID!): BulkResult!
bulkUpdateStatus(ids: [ID!]!, types: [TLOType!]!, status: String!): BulkResult!
bulkDelete(ids: [ID!]!, types: [TLOType!]!): BulkResult!
```

- [ ] Create `crits_api/graphql/mutations/` package
- [ ] Implement create mutations with validation
- [ ] Implement update mutations with partial updates
- [ ] Implement delete mutations (soft delete with audit)
- [ ] Implement relationship mutations
- [ ] Implement comment mutations
- [ ] Implement bulk operations with batch processing
- [ ] All mutations invalidate relevant cache keys (Phase 3e)

### 4f. GraphQL Authorization (Integrated)

All resolvers use the permission utilities from Phase 3d:

```python
@strawberry.type
class Query:
    @strawberry.field
    @require_permission("Sample.read")
    async def sample(self, info: Info, id: ID) -> Optional[SampleType]:
        ctx = info.context
        sample = await get_sample(id)
        if not ctx.user.check_source_tlp(sample):
            return None  # User can't see this sample
        return SampleType.from_model(sample)

    @strawberry.field
    @require_permission("Sample.read")
    async def samples(self, info: Info, first: int = 20, after: str = None) -> SampleConnection:
        ctx = info.context
        # Query-level source/TLP filtering
        query = ctx.user.filter_dict_source_tlp({})
        return await paginate_samples(query, first, after)
```

- [ ] Apply `@require_permission` to all query resolvers
- [ ] Apply `@require_permission` to all mutation resolvers
- [ ] Implement field-level permissions for sensitive fields
- [ ] Implement source/TLP filtering in all list queries
- [ ] Create custom `PermissionDenied` GraphQL error type
- [ ] Test all permission combinations

### 4g. File Upload/Download (Special Handling)

Samples and other TLOs may have associated files stored in GridFS.

```graphql
type Mutation {
  uploadSample(file: Upload!, metadata: SampleMetadataInput!): SampleUploadResult!
}

type Sample {
  # File download URL (pre-signed, time-limited)
  downloadUrl: String @requirePermission("Sample.download")
}
```

- [ ] Implement multipart file upload mutation
- [ ] Implement secure download URL generation
- [ ] Implement file streaming for large files
- [ ] Add file type detection and validation
- [ ] Calculate and verify file hashes (MD5, SHA1, SHA256, SSDEEP)

---

## Phase 5: React Frontend Foundation ✅ COMPLETE (Core)

### 5a. Create React Application ✅
- [x] Initialize Vite + React + TypeScript project in `ui/`
- [x] Configure `vite.config.ts` with path aliases (@/ for src/)
- [x] Install and configure Tailwind CSS 4.x with custom CRITs theme
- [x] Configure TypeScript with strict mode
- [x] Configure path aliases (@/ for src/)
- [x] Create `docker/Dockerfile.ui` with pnpm 10 + multi-stage build
- [x] Create `docker/nginx-ui.conf` for SPA routing (no-cache on index.html)
- [x] Enforce pnpm 10.28.2 only (supply chain security via `only-allow pnpm` preinstall hook)
- [ ] Set up ESLint + Prettier configuration

### 5b. Core UI Components ✅
- [x] Create `ui/src/components/` structure
- [x] Create `ui/src/components/ui/` with reusable base components:
  - `Button` (primary, secondary, ghost, danger variants + sizes)
  - `Card`, `CardHeader`, `CardContent` (with dark mode support)
  - `Badge` (info, success, warning, danger, neutral variants)
  - `Input`, `Select` form components
  - `Modal` dialog component
  - Barrel export via `index.ts`
- [x] Create `Layout` component with Header (user dropdown, dark/light toggle)
- [x] Create loading spinners
- [ ] Create `Navigation/` with Sidebar, Breadcrumbs
- [ ] Create `Feedback/` with Toast, Alert
- [ ] Create loading skeletons

### 5c. Preserve CRITs Visual Identity ✅
- [x] Extract color palette from existing CSS
- [x] Create Tailwind theme configuration with CRITs colors (crits-blue, crits-red, crits-green, etc.)
- [x] Create CSS custom properties for light/dark themes
- [x] Implement dark/light mode toggle with system preference detection
- [x] Create ThemeContext for persistent theme state
- [x] Style login page matching CRITs branding
- [ ] Recreate sidebar navigation styling
- [ ] Recreate table styling (preserve jTable look)
- [ ] Recreate form styling
- [ ] Recreate modal/dialog styling

### 5d. Virtual Tables Implementation
- [ ] Install TanStack Table (react-table)
- [ ] Install TanStack Virtual for virtualization
- [ ] Create `VirtualTable` base component
- [ ] Implement column configuration
- [ ] Implement sorting (client and server)
- [ ] Implement filtering (client and server)
- [ ] Implement pagination with page size options
- [ ] Implement row selection
- [ ] Implement column resizing
- [ ] Implement column visibility toggle
- [ ] Create export functionality (CSV, JSON)

### 5e. Authentication UI ✅
- [x] Create login page (redirects to Django login for shared session auth)
- [x] Create `AuthContext` provider with `useAuth()` hook
- [x] Implement `checkAuth()` via raw `fetch()` to GraphQL `me` query
- [x] Use `credentials: 'include'` for same-origin cookie auth
- [x] Implement protected route wrapper (redirects to /login if unauthenticated)
- [x] Create user profile display in header
- [x] Create logout functionality (redirects to Django `/logout/`)
- [x] Handle authentication errors gracefully (catch → setUser(null))
- [ ] Create user profile dropdown with settings

### 5f. GraphQL Client Setup ✅
- [x] Create `graphqlClient` with `graphql-request` library
- [x] Configure with `credentials: 'include'` for cookie auth
- [x] Auth check uses raw `fetch()` for reliability
- [x] React Query (`@tanstack/react-query`) configured with 5-min stale time
- [ ] Create code generation for types (graphql-codegen)
- [ ] Create custom hooks for common queries
- [ ] Implement optimistic updates

### 5g. Routing ✅
- [x] React Router with `basename="/app"` for `/app/` subpath
- [x] Routes: `/login`, `/` (dashboard), `/indicators`, `/indicators/:id`
- [x] Protected routes redirect to login when unauthenticated
- [x] Django `validate_next()` updated to allow `/app/` redirects after login

---

## Phase 6: React Frontend - Feature Pages

### 6a. Dashboard Page
- [ ] Create dashboard layout with grid
- [ ] Implement statistics cards
- [ ] Implement recent activity feed
- [ ] Implement quick search
- [ ] Create customizable widget system
- [ ] Implement chart components (recharts)
- [ ] Preserve GridSter-like drag/drop

### 6b. TLO List Pages
- [ ] Create generic TLO list page template
- [ ] Implement Actors list page
- [ ] Implement Backdoors list page
- [ ] Implement Campaigns list page
- [ ] Implement Certificates list page
- [ ] Implement Domains list page
- [ ] Implement Emails list page
- [ ] Implement Events list page
- [ ] Implement Exploits list page
- [ ] Implement Indicators list page
- [ ] Implement IPs list page
- [ ] Implement PCAPs list page
- [ ] Implement Raw Data list page
- [ ] Implement Samples list page
- [ ] Implement Screenshots list page
- [ ] Implement Signatures list page
- [ ] Implement Targets list page

### 6c. TLO Detail Pages
- [ ] Create generic TLO detail page template
- [ ] Implement tabbed interface
- [ ] Implement details section
- [ ] Implement relationships section
- [ ] Implement comments section
- [ ] Implement analysis results section
- [ ] Implement activity timeline
- [ ] Implement bucket/tag management
- [ ] Implement source information
- [ ] Implement actions menu

### 6d. Search Functionality
- [ ] Create global search bar
- [ ] Implement search results page
- [ ] Create advanced search form
- [ ] Implement search filters by type
- [ ] Implement search within relationships
- [ ] Create saved searches
- [ ] Implement search history

### 6e. Admin Pages
- [ ] Create users management page
- [ ] Create roles management page
- [ ] Create sources management page
- [ ] Create system config page
- [ ] Create audit log viewer
- [ ] Create services management page

### 6f. Forms and Dialogs
- [ ] Create TLO creation forms
- [ ] Create TLO edit forms
- [ ] Create relationship add dialog
- [ ] Create comment add dialog
- [ ] Create bulk action dialogs
- [ ] Create file upload dialog
- [ ] Create confirmation dialogs

---

## Phase 7: Service/Worker Framework

### 7a. Celery Worker Setup
- [ ] Create `src/crits_worker/` package
- [ ] Configure Celery with Redis broker
- [ ] Create task base classes
- [ ] Set up task routing
- [ ] Configure result backend
- [ ] Add task monitoring (flower)
- [ ] Create worker health checks

### 7b. Analysis Service Framework
- [ ] Create service plugin architecture
- [ ] Create service base class
- [ ] Implement service discovery
- [ ] Create service configuration model
- [ ] Implement service execution pipeline
- [ ] Create result storage
- [ ] Implement triage automation

### 7c. Built-in Services Migration
- [ ] Migrate file type detection service
- [ ] Migrate hash calculation service
- [ ] Migrate YARA scanning service
- [ ] Migrate ssdeep/fuzzy hash service
- [ ] Create service result API

---

## Phase 8: Testing & Quality

### 8a. Backend Testing
- [ ] Set up pytest with async support
- [ ] Create test fixtures for MongoDB
- [ ] Create test fixtures for Redis
- [ ] Write unit tests for models
- [ ] Write unit tests for services
- [ ] Write integration tests for API endpoints
- [ ] Write integration tests for GraphQL
- [ ] Achieve 80%+ code coverage

### 8b. Frontend Testing
- [ ] Set up Vitest for unit testing
- [ ] Set up Playwright for E2E testing
- [ ] Write component unit tests
- [ ] Write hook tests
- [ ] Write E2E tests for critical flows
- [ ] Set up visual regression testing

### 8c. CI/CD Pipeline
- [ ] Create GitHub Actions workflow
- [ ] Add linting step (ruff, eslint)
- [ ] Add type checking step (mypy, tsc)
- [ ] Add unit test step
- [ ] Add integration test step
- [ ] Add Docker build step
- [ ] Add security scanning (trivy, snyk)
- [ ] Add deployment automation

---

## Phase 9: Documentation & Cleanup

### 9a. Documentation
- [ ] Update README.md with new setup instructions
- [ ] Create API documentation (auto-generated)
- [ ] Create GraphQL schema documentation
- [ ] Create deployment guide
- [ ] Create development guide
- [ ] Create migration guide from legacy
- [ ] Create architecture decision records (ADRs)

### 9b. Code Removal List

> **Note**: Django is intentionally kept running alongside FastAPI during the transition.
> Django code removal happens only AFTER React frontend fully replaces Django templates.

**Phase 3-4 (Now): Safe to Remove**
- [x] Remove `Vagrantfile` - Vagrant VM configuration
- [x] Remove `.vagrant/` directory if present
- [ ] Remove `fabfile.py` - Fabric deployment automation
- [ ] Remove `script/bootstrap` - Legacy bootstrap script
- [ ] Remove `script/server` - Legacy dev server script
- [ ] Remove `django.wsgi` - Apache mod_wsgi config
- [ ] Remove all Tastypie API files (`api.py`) - replaced by GraphQL

**Phase 6+ (After React UI): Django Code Removal**
- [ ] Remove `crits/settings.py` - Django settings
- [ ] Remove `crits/urls.py` - Django URL router
- [ ] Remove `manage.py` - Django management script
- [ ] Remove all `views.py` files
- [ ] Remove all `forms.py` files
- [ ] Remove all Django templates (`templates/` directories)
- [ ] Remove Django middleware code
- [ ] Remove `wsgi.py` - Legacy WSGI entry point

**Phase 6+ (After React UI): Legacy Frontend Removal**
- [ ] Remove `extras/www/` static files directory
- [ ] Remove jQuery and all jQuery plugins
- [ ] Remove jTable library
- [ ] Remove jQuery UI
- [ ] Remove legacy CSS files
- [ ] Remove legacy JavaScript files

**Deferred: Authentication Changes**
- [ ] LDAP authentication - keep if needed, or migrate to SAML/OIDC
- [ ] TOTP implementation - keep or reimplement with modern library
- [ ] CRITsAuthBackend - keep until React UI complete
- [ ] API key authentication - evaluate JWT replacement timeline

**Deprecated Dependencies:**
- [ ] Remove django-tastypie
- [ ] Remove django-tastypie-mongoengine
- [ ] Remove django-celery (use celery directly)
- [ ] Remove pycrypto (replaced by cryptography)
- [ ] Remove simplejson (use stdlib json)
- [ ] Remove anyjson
- [ ] Remove old MongoEngine patches

**Obsolete Files:**
- [ ] Remove `requirements.txt` (replaced by pyproject.toml)
- [ ] Remove old `Dockerfile` (replaced by new Docker setup)
- [ ] Remove `.python-version` if pinned to 2.7
- [ ] Remove Python 2 specific code/workarounds
- [ ] Clean up `contrib/` directory

**Documentation to Remove:**
- [ ] Remove outdated installation guides
- [ ] Remove Vagrant setup documentation
- [ ] Remove Apache/mod_wsgi documentation
- [ ] Remove legacy API documentation

---

## Phase 10: Production Readiness

### 10a. Security Hardening
- [ ] Implement rate limiting
- [ ] Add request size limits
- [ ] Configure HTTPS/TLS properly
- [ ] Add security headers
- [ ] Implement CSRF protection
- [ ] Add audit logging for sensitive actions
- [ ] Conduct security review

### 10b. Performance Optimization
- [ ] Add database indexes
- [ ] Optimize GraphQL queries
- [ ] Implement query complexity limits
- [ ] Add response compression
- [ ] Configure CDN for static assets
- [ ] Optimize Docker images
- [ ] Load testing with realistic data

### 10c. Monitoring & Observability
- [ ] Add structured logging (JSON)
- [ ] Integrate with log aggregation
- [ ] Add metrics collection (Prometheus)
- [ ] Create Grafana dashboards
- [ ] Set up alerting
- [ ] Add distributed tracing
- [ ] Create runbooks

### 10d. Data Migration
- [ ] Create data export from legacy system
- [ ] Create data import scripts
- [ ] Validate data integrity
- [ ] Create rollback procedures
- [ ] Test migration with production data copy
- [ ] Document migration process

---

## Appendix A: Dependency Mapping

### Python Dependencies (Legacy → Current → Target)

| Legacy | Current (Phase 1-2) | Target (Phase 3+) | Notes |
|--------|---------------------|-------------------|-------|
| Python 2.7 | Python 3.12 ✅ | Python 3.12 | Complete |
| Django 1.x | Django 4.2 ✅ | Django 4.2 + FastAPI | Side-by-side |
| MongoEngine 0.8.9 | MongoEngine 0.28+ ✅ | MongoEngine 0.28+ | **Shared between Django & FastAPI** |
| PyMongo 3.2.2 | PyMongo 4.6+ ✅ | PyMongo 4.6+ | Sync driver (adequate for our scale) |
| django-tastypie | Disabled ✅ | Strawberry GraphQL | GraphQL replaces REST |
| pycrypto | cryptography 42+ ✅ | cryptography 42+ | Complete |
| django-celery | celery 5.3+ ✅ | celery 5.3+ | Direct Celery usage |
| Pillow 3.x | Pillow 10+ ✅ | Pillow 10+ | Complete |
| N/A | N/A | Redis 5.0+ | Caching (15-min TTL) |
| N/A | N/A | strawberry-graphql | GraphQL server |

> **Note**: We chose to keep MongoEngine instead of migrating to Beanie because:
> 1. Django and FastAPI can share the same models
> 2. No data migration required
> 3. Existing code patterns still work
> 4. PyMongo sync driver is adequate for our query patterns

### Frontend Dependencies (Legacy → Modern)

| Legacy | Modern | Notes |
|--------|--------|-------|
| jQuery 1.10 | React 18 | Complete rewrite (Phase 5-6) |
| jQuery UI | Radix UI / Headless UI | Accessible components |
| jTable | TanStack Table | Virtual tables |
| jQuery GridSter | react-grid-layout | Dashboard widgets |
| Font Awesome 4 | Font Awesome 6 / Lucide | Icon library |
| Custom CSS | Tailwind CSS | Utility-first styling |

---

## Appendix B: Migration Phases Summary

| Phase | Focus | Status | Dependencies |
|-------|-------|--------|--------------|
| 1 | Python 3.12 Migration | ✅ Complete | None |
| 2 | Docker Stack | ✅ Complete | Phase 1 |
| 3 | FastAPI + GraphQL Foundation | ✅ Complete | Phase 1, 2 |
| 4 | GraphQL Schema Implementation | ✅ Complete (Core) | Phase 3 |
| 5 | React Foundation | ✅ Complete (Core) | Phase 4 |
| 6 | React Features | In Progress | Phase 5 |
| 7 | Worker Framework | Planned | Phase 3 |
| 8 | Testing | Planned | Phase 3-7 |
| 9 | Documentation | Ongoing | Low |
| 10 | Production | Phase 1-9 | Medium |

---

## Appendix C: Risk Mitigation

### High-Risk Items (Updated)

1. ~~**MongoEngine → Beanie Migration**~~: **ELIMINATED** - We keep MongoEngine
   - No data migration needed
   - Django and FastAPI share same models
   - Risk reduced to zero

2. **Permission Parity**: GraphQL API must enforce same permissions as Django
   - Mitigation: Comprehensive permission test suite
   - Mitigation: Side-by-side testing of Django vs GraphQL results
   - Mitigation: Reuse existing permission check code where possible

3. **Cache Consistency**: Stale cache could show unauthorized data
   - Mitigation: Include user's source access hash in cache keys
   - Mitigation: Aggressive cache invalidation on permission changes
   - Mitigation: Short TTL (15 minutes) limits stale data window

4. **Authentication Sharing**: Django sessions must work with FastAPI
   - Mitigation: FastAPI reads Django session cookies
   - Mitigation: Shared Redis session backend
   - Mitigation: Fallback to JWT for API-only clients

5. **Frontend Rewrite**: Feature parity gaps
   - Mitigation: Django UI remains functional throughout transition
   - Mitigation: Incremental React page rollout
   - Mitigation: Feature flags to switch between old/new UI

### Rollback Strategy

Each phase is independently deployable with rollback capability:
- **Phase 3-4**: nginx can route `/api/graphql` back to 404; Django unaffected
- **Phase 5-6**: React UI is separate container; revert nginx to serve Django
- Database unchanged throughout (no migrations needed)
- Docker images tagged by git commit for easy rollback

### Architectural Benefits of Side-by-Side Approach

1. **Zero downtime migration**: Users continue using Django UI while GraphQL is built
2. **Incremental validation**: Test GraphQL queries against Django results
3. **No data migration**: Same MongoDB, same MongoEngine models
4. **Gradual frontend migration**: Replace one page at a time with React
5. **Easy rollback**: Just change nginx routing
