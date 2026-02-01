# CRITs Repository Agent Instructions

This document provides instructions for AI agents working on the CRITs modernization project. Each section covers different aspects of the codebase and migration work.

---

## Repository Overview

CRITs (Collaborative Research Into Threats) is a threat intelligence platform being migrated from a legacy Python 2.7/Django stack to a modern Python 3.12+/FastAPI/React architecture.

### Directory Structure

```
/home/matt/crits/
├── crits/                      # Legacy Django application (Python 2.7)
│   ├── core/                   # Core functionality (users, auth, handlers)
│   ├── actors/                 # Threat actor intelligence
│   ├── samples/                # Malware sample management
│   ├── indicators/             # IoC indicator management
│   ├── [other TLO modules]/    # 20+ domain modules
│   └── settings.py             # Django configuration
├── src/                        # NEW: Modern Python 3.12+ code
│   ├── crits_api/              # FastAPI application
│   └── crits_worker/           # Celery worker tasks
├── ui/                         # NEW: React frontend
├── docker/                     # NEW: Docker configuration
├── MIGRATION_PLAN.md           # Detailed migration checklist
└── AGENTS.md                   # This file
```

### Key Concepts

**TLOs (Top-Level Objects)**: The core data types in CRITs:
- Actors, Backdoors, Campaigns, Certificates, Domains
- Emails, Events, Exploits, Indicators, IPs
- PCAPs, RawData, Samples, Screenshots, Signatures, Targets

**Sources**: Access control mechanism - users have access to data based on source permissions.

**Relationships**: TLOs can be related to each other with typed relationships.

---

## General Guidelines

### Code Style

**Python (Backend):**
- Use Python 3.12+ features (type hints, match statements, etc.)
- Follow PEP 8 with 100-character line limit
- Use ruff for linting and formatting
- Type hint all function signatures
- Use async/await for I/O operations
- Docstrings in Google style

**TypeScript (Frontend):**
- Use TypeScript strict mode
- Use functional components with hooks
- Follow Airbnb ESLint configuration
- Use named exports (not default exports)
- Co-locate tests with components

### Commit Messages

Use conventional commits format:
```
type(scope): description

feat(api): add actor CRUD endpoints
fix(ui): correct pagination in sample list
refactor(models): migrate Actor to Beanie ODM
docs(readme): update installation instructions
```

### Testing Requirements

- Backend: pytest with pytest-asyncio
- Frontend: Vitest for units, Playwright for E2E
- Minimum 80% code coverage for new code
- All PRs must pass CI checks

---

## Phase-Specific Instructions

### Phase 1: Python 3.12 Migration

**Objective**: Convert legacy Python 2.7 code to Python 3.12+ compatible code.

**Key Files to Modify**:
- All `.py` files in `crits/` directory
- `requirements.txt` → `pyproject.toml`

**Common Python 2 → 3 Fixes**:
```python
# Print statements
print "text"          →  print("text")

# Unicode handling
u"string"             →  "string"  # str is unicode in Py3
unicode(x)            →  str(x)
.encode('utf-8')      →  # Usually not needed

# Dictionary methods
dict.keys()           →  list(dict.keys())  # If list needed
dict.iteritems()      →  dict.items()
dict.itervalues()     →  dict.values()

# Imports
import ConfigParser   →  import configparser
import urllib2        →  import urllib.request
from StringIO         →  from io import StringIO

# Exception handling
except E, e:          →  except E as e:

# Integer division
5 / 2                 →  5 // 2  # If int result needed

# Range
xrange(n)             →  range(n)

# Metaclasses
__metaclass__ = Meta  →  class Foo(metaclass=Meta):
```

**Testing Migration**:
```bash
# Run 2to3 in preview mode first
2to3 -n -W crits/core/

# After manual fixes, test with Python 3.12
python3.12 -m py_compile crits/core/*.py
```

---

### Phase 2: Docker Stack

**Objective**: Create production-ready Docker infrastructure.

**File Locations**:
- `docker/Dockerfile.api` - FastAPI container
- `docker/Dockerfile.ui` - React/nginx container
- `docker/Dockerfile.worker` - Celery worker container
- `docker/nginx/nginx.conf` - Reverse proxy config
- `docker-compose.yml` - Development stack
- `docker-compose.prod.yml` - Production stack

**Service Architecture**:
```
┌─────────────┐     ┌─────────────┐
│   nginx     │────▶│   ui (React)│
│  (port 80)  │     │  (port 3000)│
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   api       │────▶│   mongodb   │
│  (FastAPI)  │     │  (port 27017)│
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   worker    │────▶│   redis     │
│  (Celery)   │     │  (port 6379)│
└─────────────┘     └─────────────┘
```

**Environment Variables**:
```bash
# API Configuration
MONGODB_URL=mongodb://mongo:27017/crits
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generate-secure-key>
GITHUB_CLIENT_ID=<from-github>
GITHUB_CLIENT_SECRET=<from-github>

# Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_GRAPHQL_URL=http://localhost:8000/graphql
```

---

### Phase 3: FastAPI Backend

**Objective**: Implement REST API endpoints with FastAPI.

**Directory Structure**:
```
src/crits_api/
├── __init__.py
├── main.py              # FastAPI app initialization
├── config.py            # Pydantic settings
├── dependencies.py      # Dependency injection
├── models/              # Beanie ODM models
│   ├── __init__.py
│   ├── base.py          # CritsDocument base
│   ├── user.py
│   ├── actor.py
│   └── ...
├── schemas/             # Pydantic schemas
│   ├── __init__.py
│   ├── actor.py
│   └── ...
├── routers/             # API routers
│   ├── __init__.py
│   ├── auth.py
│   ├── actors.py
│   └── ...
├── auth/                # Authentication
│   ├── oauth.py
│   └── jwt.py
└── services/            # Business logic
    └── ...
```

**Beanie Model Pattern**:
```python
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, List

class Actor(Document):
    name: Indexed(str)
    description: Optional[str] = None
    threat_types: List[str] = Field(default_factory=list)
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "actors"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "name": "APT29",
                "description": "Russian threat actor",
                "threat_types": ["nation-state"]
            }
        }
```

**Router Pattern**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models.actor import Actor
from ..schemas.actor import ActorCreate, ActorRead, ActorUpdate
from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/actors", tags=["actors"])

@router.get("/", response_model=List[ActorRead])
async def list_actors(
    skip: int = 0,
    limit: int = 100,
    user = Depends(get_current_user)
):
    return await Actor.find_all().skip(skip).limit(limit).to_list()

@router.post("/", response_model=ActorRead, status_code=status.HTTP_201_CREATED)
async def create_actor(
    actor: ActorCreate,
    user = Depends(get_current_user)
):
    new_actor = Actor(**actor.dict())
    await new_actor.insert()
    return new_actor
```

---

### Phase 4: Strawberry GraphQL

**Objective**: Implement GraphQL API with Strawberry.

**Directory Structure**:
```
src/crits_api/graphql/
├── __init__.py
├── schema.py            # Root schema
├── context.py           # Request context
├── dataloaders.py       # DataLoader instances
├── types/               # GraphQL types
│   ├── __init__.py
│   ├── user.py
│   ├── actor.py
│   └── ...
├── queries/             # Query resolvers
│   └── ...
├── mutations/           # Mutation resolvers
│   └── ...
└── auth/                # Authorization
    └── permissions.py
```

**Type Definition Pattern**:
```python
import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class ActorType:
    id: strawberry.ID
    name: str
    description: Optional[str]
    threat_types: List[str]
    created: datetime
    modified: datetime

    @strawberry.field
    async def relationships(self, info) -> List["RelationshipType"]:
        # Use dataloader to prevent N+1
        loader = info.context.relationship_loader
        return await loader.load(self.id)
```

**Query Pattern with Auth**:
```python
import strawberry
from strawberry.types import Info
from .types.actor import ActorType
from .auth.permissions import IsAuthenticated

@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def actor(self, info: Info, id: strawberry.ID) -> Optional[ActorType]:
        from ..models.actor import Actor
        actor = await Actor.get(id)
        if not actor:
            return None
        # Check source access
        if not info.context.user.has_source_access(actor.source):
            raise PermissionError("Access denied")
        return ActorType.from_orm(actor)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def actors(
        self,
        info: Info,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActorType]:
        from ..models.actor import Actor
        user = info.context.user
        # Filter by accessible sources
        actors = await Actor.find(
            {"source": {"$in": user.source_access}}
        ).skip(offset).limit(limit).to_list()
        return [ActorType.from_orm(a) for a in actors]
```

**Redis Caching Pattern**:
```python
import strawberry
from functools import wraps
from ..cache.redis import cache

def cached(ttl: int = 300):
    def decorator(resolver):
        @wraps(resolver)
        async def wrapper(self, info, **kwargs):
            cache_key = f"{resolver.__name__}:{hash(frozenset(kwargs.items()))}"
            cached_result = await cache.get(cache_key)
            if cached_result:
                return cached_result
            result = await resolver(self, info, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator

@strawberry.type
class Query:
    @strawberry.field
    @cached(ttl=60)
    async def dashboard_stats(self, info: Info) -> DashboardStats:
        # Expensive aggregation query
        ...
```

---

### Phase 5-6: React Frontend

**Objective**: Build React frontend preserving CRITs visual identity.

**Directory Structure**:
```
ui/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── DataTable/
│   │   │   ├── VirtualTable.tsx
│   │   │   ├── TablePagination.tsx
│   │   │   └── ColumnConfig.tsx
│   │   ├── TLO/
│   │   │   ├── ActorCard.tsx
│   │   │   ├── SampleCard.tsx
│   │   │   └── ...
│   │   └── ...
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── actors/
│   │   │   ├── ActorList.tsx
│   │   │   └── ActorDetail.tsx
│   │   └── ...
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useGraphQL.ts
│   │   └── ...
│   ├── graphql/
│   │   ├── queries/
│   │   └── mutations/
│   ├── styles/
│   │   └── crits-theme.css    # CRITs color preservation
│   └── lib/
│       └── utils.ts
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

**CRITs Color Palette** (preserve in Tailwind config):
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        crits: {
          primary: '#2c3e50',      // Dark blue-gray header
          secondary: '#34495e',    // Slightly lighter
          accent: '#3498db',       // Blue accent
          success: '#27ae60',      // Green
          warning: '#f39c12',      // Orange
          danger: '#e74c3c',       // Red
          background: '#ecf0f1',   // Light gray background
          surface: '#ffffff',      // White cards
          text: '#2c3e50',         // Dark text
          muted: '#7f8c8d',        // Muted gray text
        }
      }
    }
  }
}
```

**Virtual Table Component Pattern**:
```tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useReactTable, getCoreRowModel } from '@tanstack/react-table';

interface VirtualTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  onRowClick?: (row: T) => void;
  isLoading?: boolean;
}

export function VirtualTable<T>({
  data,
  columns,
  onRowClick,
  isLoading
}: VirtualTableProps<T>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const { rows } = table.getRowModel();
  const parentRef = React.useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 10,
  });

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <table className="w-full">
        <thead className="sticky top-0 bg-crits-primary text-white">
          {/* Header rendering */}
        </thead>
        <tbody>
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index];
            return (
              <tr
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                className="hover:bg-crits-background cursor-pointer"
              >
                {/* Cell rendering */}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

---

### Phase 7: Worker Framework

**Objective**: Implement Celery workers for background processing.

**Directory Structure**:
```
src/crits_worker/
├── __init__.py
├── celery.py           # Celery app configuration
├── config.py           # Worker settings
├── tasks/
│   ├── __init__.py
│   ├── analysis.py     # Analysis service tasks
│   ├── enrichment.py   # Data enrichment tasks
│   └── maintenance.py  # Cleanup/maintenance tasks
└── services/
    ├── __init__.py
    ├── base.py         # Service base class
    ├── yara.py         # YARA scanning
    └── hash.py         # Hash calculation
```

**Celery Configuration**:
```python
# src/crits_worker/celery.py
from celery import Celery

app = Celery('crits_worker')
app.config_from_object('crits_worker.config')

app.conf.update(
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    task_routes={
        'crits_worker.tasks.analysis.*': {'queue': 'analysis'},
        'crits_worker.tasks.enrichment.*': {'queue': 'enrichment'},
    }
)
```

**Task Pattern**:
```python
# src/crits_worker/tasks/analysis.py
from celery import shared_task
from ..services.yara import YaraScanner

@shared_task(bind=True, max_retries=3)
def scan_sample_yara(self, sample_id: str):
    """Scan a sample with YARA rules."""
    try:
        scanner = YaraScanner()
        result = scanner.scan(sample_id)
        # Store result
        return {"sample_id": sample_id, "matches": result}
    except Exception as exc:
        self.retry(countdown=60, exc=exc)
```

---

## Troubleshooting

### Common Issues

**MongoDB Connection Errors**:
```python
# Ensure Motor is used for async operations
from motor.motor_asyncio import AsyncIOMotorClient

# Not pymongo.MongoClient directly in async code
```

**Import Errors After Py3 Migration**:
```bash
# Check for circular imports
python -c "from crits.core.user import CRITsUser"

# Use TYPE_CHECKING for type-only imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .related_module import RelatedClass
```

**GraphQL N+1 Queries**:
```python
# Always use DataLoaders for relationship fields
# Never query directly in field resolvers
```

### Getting Help

- Check existing issues on the repository
- Review MIGRATION_PLAN.md for context
- Reference legacy code in `crits/` for behavior expectations
- Test against MongoDB with realistic data

---

## Validation Checklist

Before marking any phase complete:

- [ ] All tests pass
- [ ] No ruff/eslint errors
- [ ] Type checking passes (mypy/tsc)
- [ ] Docker containers build successfully
- [ ] API endpoints return expected responses
- [ ] GraphQL schema is valid
- [ ] UI renders without console errors
- [ ] Manual testing of critical paths
- [ ] Documentation updated
- [ ] MIGRATION_PLAN.md checklist items marked complete
