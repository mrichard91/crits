# CRITs Modernization Migration Plan

## Executive Summary

This document outlines the comprehensive migration of CRITs from a Python 2.7/Django 1.x application to a modern Python 3.12+/FastAPI/React stack. The migration preserves the core functionality and visual identity while modernizing the architecture for maintainability, performance, and security.

### Current State
- **Backend**: Python 2.7, Django 1.x, Tastypie REST API
- **Frontend**: Server-side Django templates, jQuery 1.10, jTable
- **Database**: MongoDB via MongoEngine 0.8.9 (patched)
- **Auth**: Custom CRITs auth, optional LDAP, TOTP
- **Tasks**: Celery with django-celery, thread/process pools
- **Deploy**: Single Dockerfile (dev), Apache/mod_wsgi (prod)

### Target State
- **Backend**: Python 3.12+, FastAPI, Strawberry GraphQL
- **Frontend**: React 18+, Tailwind CSS, TanStack components
- **Database**: MongoDB via Beanie ODM (async), Pydantic models
- **Auth**: GitHub OAuth via authlib, JWT sessions
- **Tasks**: Celery 5+ with Redis broker, async workers
- **Deploy**: Docker Compose stack (nginx, api, ui, worker, mongo, redis)

---

## Phase 1: Python 3.12 Migration & Project Modernization

### 1a. Create pyproject.toml and Modern Project Structure
- [ ] Create `pyproject.toml` with project metadata, Python 3.12+ requirement
- [ ] Define dependencies with version constraints (split dev/prod)
- [ ] Configure build system (hatchling or setuptools)
- [ ] Add tool configurations (ruff, mypy, pytest)
- [ ] Create `src/` directory structure for new code

### 1b. Set Up Development Environment
- [ ] Create `requirements-legacy.txt` snapshot of current deps
- [ ] Add `.python-version` file for pyenv (3.12.x)
- [ ] Create `Makefile` with common commands (install, lint, test, run)
- [ ] Set up pre-commit hooks configuration
- [ ] Add VS Code / PyCharm project settings

### 1c. Python 2 to 3 Syntax Migration - Core Module
- [ ] Run `2to3` tool on `crits/core/` directory
- [ ] Fix print statements → print() functions
- [ ] Fix unicode/str handling (u"" prefixes, encode/decode)
- [ ] Update dict methods (.keys(), .values(), .items() return views)
- [ ] Fix integer division (// vs /)
- [ ] Update exception syntax (except E as e:)
- [ ] Fix imports (ConfigParser, urllib, etc.)

### 1d. Python 2 to 3 Syntax Migration - App Modules
- [ ] Migrate `crits/actors/` module
- [ ] Migrate `crits/backdoors/` module
- [ ] Migrate `crits/campaigns/` module
- [ ] Migrate `crits/certificates/` module
- [ ] Migrate `crits/comments/` module
- [ ] Migrate `crits/dashboards/` module
- [ ] Migrate `crits/domains/` module
- [ ] Migrate `crits/emails/` module
- [ ] Migrate `crits/events/` module
- [ ] Migrate `crits/exploits/` module
- [ ] Migrate `crits/indicators/` module
- [ ] Migrate `crits/ips/` module
- [ ] Migrate `crits/locations/` module
- [ ] Migrate `crits/notifications/` module
- [ ] Migrate `crits/objects/` module
- [ ] Migrate `crits/pcaps/` module
- [ ] Migrate `crits/raw_data/` module
- [ ] Migrate `crits/relationships/` module
- [ ] Migrate `crits/samples/` module
- [ ] Migrate `crits/screenshots/` module
- [ ] Migrate `crits/services/` module
- [ ] Migrate `crits/signatures/` module
- [ ] Migrate `crits/stats/` module
- [ ] Migrate `crits/targets/` module
- [ ] Migrate `crits/vocabulary/` module

### 1e. Update Dependencies to Python 3 Compatible Versions
- [ ] Update MongoEngine to 0.27+ (Python 3 compatible)
- [ ] Update PyMongo to 4.6+ (Python 3.12 compatible)
- [ ] Update Django to 4.2 LTS (temporary, before FastAPI migration)
- [ ] Replace pycrypto with cryptography library
- [ ] Update Pillow to 10.x
- [ ] Update python-magic to latest
- [ ] Update lxml to latest
- [ ] Update requests to latest
- [ ] Update PyYAML to latest
- [ ] Update celery to 5.3+
- [ ] Update python-dateutil to latest
- [ ] Remove/replace deprecated packages (simplejson, anyjson)

### 1f. Fix MongoEngine Compatibility Issues
- [ ] Update Document class definitions for new API
- [ ] Fix queryset operations (no_dereference, etc.)
- [ ] Update field definitions (StringField, etc.)
- [ ] Fix GridFS file handling for new API
- [ ] Update connection management code
- [ ] Test all model save/load operations

### 1g. Validate Python 3.12 Migration
- [ ] Run existing test suite with Python 3.12
- [ ] Fix failing tests due to migration
- [ ] Add type hints to core modules (gradual)
- [ ] Run mypy on migrated code
- [ ] Run ruff linter and fix issues
- [ ] Create migration test script for CI

---

## Phase 2: Docker Stack Foundation

### 2a. Create Base Docker Infrastructure
- [ ] Create `docker/` directory structure
- [ ] Write `docker/Dockerfile.api` (Python 3.12 FastAPI)
- [ ] Write `docker/Dockerfile.ui` (Node 20 + nginx)
- [ ] Write `docker/Dockerfile.worker` (Celery worker)
- [ ] Create `.dockerignore` with proper exclusions
- [ ] Create `docker/nginx/nginx.conf` for reverse proxy

### 2b. Create Docker Compose Configuration
- [ ] Write `docker-compose.yml` for development
- [ ] Write `docker-compose.prod.yml` for production
- [ ] Configure MongoDB service with persistence
- [ ] Configure Redis service for caching/broker
- [ ] Configure nginx service with SSL support
- [ ] Add healthchecks for all services
- [ ] Configure named volumes for data persistence
- [ ] Set up inter-service networking

### 2c. Create Environment Configuration
- [ ] Create `.env.example` with all variables
- [ ] Document all environment variables
- [ ] Create `docker/env/` with per-service env files
- [ ] Add secrets management approach (Docker secrets or env)
- [ ] Configure MongoDB authentication
- [ ] Configure Redis authentication

### 2d. Database Migration Scripts
- [ ] Create MongoDB initialization script
- [ ] Create index creation script for collections
- [ ] Create data migration script from legacy format
- [ ] Add backup/restore utilities
- [ ] Create seed data for development

---

## Phase 3: FastAPI Backend Implementation

### 3a. Create FastAPI Application Structure
- [ ] Create `src/crits_api/` package
- [ ] Create `src/crits_api/main.py` with FastAPI app
- [ ] Create `src/crits_api/config.py` with Pydantic settings
- [ ] Create `src/crits_api/dependencies.py` for DI
- [ ] Set up CORS middleware configuration
- [ ] Set up request logging middleware
- [ ] Create health check endpoints

### 3b. Implement Beanie ODM Models - Core
- [ ] Create `src/crits_api/models/` package
- [ ] Create `base.py` with CritsDocument base class
- [ ] Create `user.py` with User model
- [ ] Create `role.py` with Role model
- [ ] Create `source.py` with Source and SourceAccess models
- [ ] Create `audit.py` with AuditLog model
- [ ] Create `config.py` with CRITsConfig model
- [ ] Create `comment.py` with Comment model
- [ ] Create `relationship.py` with Relationship model

### 3c. Implement Beanie ODM Models - TLOs (Top-Level Objects)
- [ ] Create `actor.py` with Actor model
- [ ] Create `backdoor.py` with Backdoor model
- [ ] Create `campaign.py` with Campaign model
- [ ] Create `certificate.py` with Certificate model
- [ ] Create `domain.py` with Domain model
- [ ] Create `email.py` with Email model
- [ ] Create `event.py` with Event model
- [ ] Create `exploit.py` with Exploit model
- [ ] Create `indicator.py` with Indicator model
- [ ] Create `ip.py` with IP model
- [ ] Create `pcap.py` with PCAP model
- [ ] Create `raw_data.py` with RawData model
- [ ] Create `sample.py` with Sample model
- [ ] Create `screenshot.py` with Screenshot model
- [ ] Create `signature.py` with Signature model
- [ ] Create `target.py` with Target model

### 3d. Implement Pydantic Schemas
- [ ] Create `src/crits_api/schemas/` package
- [ ] Create input/output schemas for each TLO
- [ ] Create pagination schemas
- [ ] Create filter/search schemas
- [ ] Create error response schemas
- [ ] Add OpenAPI schema customizations

### 3e. GitHub OAuth Implementation
- [ ] Install authlib dependency
- [ ] Create `src/crits_api/auth/` package
- [ ] Create `oauth.py` with GitHub OAuth client
- [ ] Create `jwt.py` with JWT token handling
- [ ] Create `dependencies.py` with auth dependencies
- [ ] Implement login redirect endpoint
- [ ] Implement OAuth callback endpoint
- [ ] Implement token refresh endpoint
- [ ] Implement logout endpoint
- [ ] Create user provisioning from GitHub profile
- [ ] Map GitHub organizations to CRITs roles

### 3f. REST API Endpoints - Core
- [ ] Create `src/crits_api/routers/` package
- [ ] Create `auth.py` router (login, logout, me)
- [ ] Create `users.py` router (CRUD, preferences)
- [ ] Create `roles.py` router (CRUD, permissions)
- [ ] Create `sources.py` router (CRUD, access)
- [ ] Create `config.py` router (system settings)
- [ ] Create `audit.py` router (log viewing)
- [ ] Create `search.py` router (global search)
- [ ] Create `dashboard.py` router (stats, widgets)

### 3g. REST API Endpoints - TLOs
- [ ] Create `actors.py` router with full CRUD
- [ ] Create `backdoors.py` router with full CRUD
- [ ] Create `campaigns.py` router with full CRUD
- [ ] Create `certificates.py` router with full CRUD
- [ ] Create `domains.py` router with full CRUD
- [ ] Create `emails.py` router with full CRUD
- [ ] Create `events.py` router with full CRUD
- [ ] Create `exploits.py` router with full CRUD
- [ ] Create `indicators.py` router with full CRUD
- [ ] Create `ips.py` router with full CRUD
- [ ] Create `pcaps.py` router with full CRUD
- [ ] Create `raw_data.py` router with full CRUD
- [ ] Create `samples.py` router with full CRUD
- [ ] Create `screenshots.py` router with full CRUD
- [ ] Create `signatures.py` router with full CRUD
- [ ] Create `targets.py` router with full CRUD

### 3h. File Upload/Download Handling
- [ ] Implement GridFS async file storage
- [ ] Create file upload endpoint with streaming
- [ ] Create file download endpoint with streaming
- [ ] Implement file type detection
- [ ] Add virus/malware upload safety measures
- [ ] Implement file hash calculation (MD5, SHA1, SHA256)

---

## Phase 4: Strawberry GraphQL Server

### 4a. GraphQL Schema Foundation
- [ ] Install strawberry-graphql with FastAPI integration
- [ ] Create `src/crits_api/graphql/` package
- [ ] Create `schema.py` with root Query and Mutation types
- [ ] Create `context.py` with request context
- [ ] Create `dataloaders.py` for N+1 prevention
- [ ] Mount GraphQL endpoint on FastAPI app
- [ ] Configure GraphQL playground/explorer

### 4b. GraphQL Types - Core
- [ ] Create `types/user.py` with UserType
- [ ] Create `types/role.py` with RoleType
- [ ] Create `types/source.py` with SourceType
- [ ] Create `types/comment.py` with CommentType
- [ ] Create `types/relationship.py` with RelationshipType
- [ ] Create `types/audit.py` with AuditLogType
- [ ] Create `types/pagination.py` with Connection types

### 4c. GraphQL Types - TLOs
- [ ] Create `types/actor.py` with ActorType
- [ ] Create `types/backdoor.py` with BackdoorType
- [ ] Create `types/campaign.py` with CampaignType
- [ ] Create `types/certificate.py` with CertificateType
- [ ] Create `types/domain.py` with DomainType
- [ ] Create `types/email.py` with EmailType
- [ ] Create `types/event.py` with EventType
- [ ] Create `types/exploit.py` with ExploitType
- [ ] Create `types/indicator.py` with IndicatorType
- [ ] Create `types/ip.py` with IPType
- [ ] Create `types/pcap.py` with PCAPType
- [ ] Create `types/raw_data.py` with RawDataType
- [ ] Create `types/sample.py` with SampleType
- [ ] Create `types/screenshot.py` with ScreenshotType
- [ ] Create `types/signature.py` with SignatureType
- [ ] Create `types/target.py` with TargetType

### 4d. GraphQL Queries
- [ ] Implement single-object queries (actor, sample, etc.)
- [ ] Implement list queries with pagination
- [ ] Implement filter arguments for each type
- [ ] Implement search query with full-text search
- [ ] Implement relationship traversal queries
- [ ] Implement dashboard statistics queries
- [ ] Implement audit log queries

### 4e. GraphQL Mutations
- [ ] Implement create mutations for each TLO
- [ ] Implement update mutations for each TLO
- [ ] Implement delete mutations for each TLO
- [ ] Implement relationship mutations (add/remove)
- [ ] Implement comment mutations
- [ ] Implement bulk operations
- [ ] Implement file upload mutations

### 4f. GraphQL Authorization
- [ ] Create `auth/permissions.py` with permission decorators
- [ ] Implement field-level authorization
- [ ] Implement source-based access control
- [ ] Implement role-based query filtering
- [ ] Add authorization to all resolvers
- [ ] Create permission denied error handling
- [ ] Test authorization edge cases

### 4g. GraphQL Caching with Redis
- [ ] Create `cache/redis.py` with Redis client
- [ ] Implement query result caching
- [ ] Create cache key generation strategy
- [ ] Implement cache invalidation on mutations
- [ ] Add cache headers to responses
- [ ] Create cache warming for common queries
- [ ] Monitor cache hit/miss rates

---

## Phase 5: React Frontend Foundation

### 5a. Create React Application
- [ ] Initialize Vite + React + TypeScript project in `ui/`
- [ ] Configure `vite.config.ts` with proxy to API
- [ ] Install and configure Tailwind CSS
- [ ] Set up ESLint + Prettier configuration
- [ ] Configure path aliases (@/ for src/)
- [ ] Set up environment variable handling

### 5b. Core UI Components
- [ ] Create `ui/src/components/` structure
- [ ] Create `Layout/` with Header, Sidebar, Footer
- [ ] Create `Navigation/` with NavBar, Breadcrumbs
- [ ] Create `DataDisplay/` with Card, Badge, Tag
- [ ] Create `Feedback/` with Toast, Alert, Modal
- [ ] Create `Forms/` with Input, Select, Checkbox
- [ ] Create `Buttons/` with Button, IconButton
- [ ] Create loading spinners and skeletons

### 5c. Preserve CRITs Visual Identity
- [ ] Extract color palette from existing CSS
- [ ] Create Tailwind theme configuration
- [ ] Create CSS variables for CRITs colors
- [ ] Recreate header/banner styling
- [ ] Recreate sidebar navigation styling
- [ ] Recreate table styling (preserve jTable look)
- [ ] Recreate form styling
- [ ] Recreate modal/dialog styling
- [ ] Create Font Awesome icon integration

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

### 5e. Authentication UI
- [ ] Create login page with GitHub OAuth button
- [ ] Create authentication context provider
- [ ] Implement protected route wrapper
- [ ] Create user profile dropdown
- [ ] Implement token refresh logic
- [ ] Create logout functionality
- [ ] Handle authentication errors

### 5f. GraphQL Client Setup
- [ ] Install urql or Apollo Client
- [ ] Configure GraphQL client with auth headers
- [ ] Set up client-side caching
- [ ] Create code generation for types (graphql-codegen)
- [ ] Create custom hooks for common queries
- [ ] Implement optimistic updates
- [ ] Set up error handling

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

The following code/features should be removed as they are obsolete:

**Containerization (keep Docker only):**
- [ ] Remove `Vagrantfile` - Vagrant VM configuration
- [ ] Remove `.vagrant/` directory if present
- [ ] Remove Vagrant references in documentation

**Deployment Tools:**
- [ ] Remove `fabfile.py` - Fabric deployment automation
- [ ] Remove `script/bootstrap` - Legacy bootstrap script
- [ ] Remove `script/server` - Legacy dev server script
- [ ] Remove `django.wsgi` - Apache mod_wsgi config
- [ ] Remove `wsgi.py` - Legacy WSGI entry point

**Legacy Django Code (after FastAPI migration):**
- [ ] Remove `crits/settings.py` - Django settings
- [ ] Remove `crits/urls.py` - Django URL router
- [ ] Remove `manage.py` - Django management script
- [ ] Remove all `views.py` files
- [ ] Remove all `forms.py` files
- [ ] Remove all Django templates (`templates/` directories)
- [ ] Remove all Tastypie API files (`api.py`)
- [ ] Remove Django middleware code
- [ ] Remove Django admin configurations

**Legacy Frontend:**
- [ ] Remove `extras/www/` static files directory
- [ ] Remove jQuery and all jQuery plugins
- [ ] Remove jTable library
- [ ] Remove jQuery UI
- [ ] Remove legacy CSS files
- [ ] Remove legacy JavaScript files

**Legacy Authentication:**
- [ ] Remove LDAP authentication code
- [ ] Remove TOTP implementation (or reimplement if needed)
- [ ] Remove CRITsAuthBackend
- [ ] Remove CRITsRemoteUserBackend
- [ ] Remove API key authentication (replace with JWT)

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

### Python Dependencies (Legacy → Modern)

| Legacy | Modern | Notes |
|--------|--------|-------|
| Django 1.x | FastAPI 0.109+ | Complete framework change |
| MongoEngine 0.8.9 | Beanie 1.25+ | Async ODM with Pydantic |
| PyMongo 3.2.2 | Motor 3.3+ | Async MongoDB driver |
| django-tastypie | FastAPI routers | Built-in REST support |
| pycrypto | cryptography 42+ | Security-maintained |
| python-ldap | N/A | Removed (GitHub OAuth only) |
| django-celery | celery 5.3+ | Direct Celery usage |
| Pillow 3.x | Pillow 10+ | Image processing |
| simplejson | stdlib json | No longer needed |

### Frontend Dependencies (Legacy → Modern)

| Legacy | Modern | Notes |
|--------|--------|-------|
| jQuery 1.10 | React 18 | Complete rewrite |
| jQuery UI | Radix UI / Headless UI | Accessible components |
| jTable | TanStack Table | Virtual tables |
| jQuery GridSter | react-grid-layout | Dashboard widgets |
| Font Awesome 4 | Font Awesome 6 / Lucide | Icon library |
| Custom CSS | Tailwind CSS | Utility-first styling |

---

## Appendix B: Migration Phases Summary

| Phase | Focus | Dependencies | Est. Complexity |
|-------|-------|--------------|-----------------|
| 1 | Python 3.12 Migration | None | High |
| 2 | Docker Stack | Phase 1 | Medium |
| 3 | FastAPI Backend | Phase 1, 2 | High |
| 4 | GraphQL Server | Phase 3 | High |
| 5 | React Foundation | Phase 2 | Medium |
| 6 | React Features | Phase 4, 5 | High |
| 7 | Worker Framework | Phase 3 | Medium |
| 8 | Testing | Phase 3-7 | Medium |
| 9 | Documentation | Phase 1-8 | Low |
| 10 | Production | Phase 1-9 | Medium |

---

## Appendix C: Risk Mitigation

### High-Risk Items

1. **MongoEngine → Beanie Migration**: Data model changes could cause data loss
   - Mitigation: Extensive testing with production data copies
   - Mitigation: Create reversible migration scripts

2. **Authentication Change**: Users losing access during transition
   - Mitigation: Parallel auth systems during transition
   - Mitigation: Clear communication and migration docs

3. **Frontend Rewrite**: Feature parity gaps
   - Mitigation: Comprehensive feature audit before migration
   - Mitigation: Incremental deployment with feature flags

### Rollback Strategy

Each phase should be deployable independently with rollback capability:
- Maintain legacy system in parallel during migration
- Use database migrations that can be reversed
- Keep Docker images tagged by version
- Document rollback procedures for each phase
