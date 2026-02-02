# Welcome to CRITs

![Image](https://github.com/crits/crits/raw/master/extras/www/new_images/crits_logo.png)

## What Is CRITs?

CRITs is a web-based tool which combines an analytic engine with a cyber threat database that not only serves as a repository for attack data and malware, but also provides analysts with a powerful platform for conducting malware analyses, correlating malware, and for targeting data. These analyses and correlations can also be saved and exploited within CRITs. CRITs employs a simple but very useful hierarchy to structure cyber threat information. This structure gives analysts the power to 'pivot' on metadata to discover previously unknown related content.

Visit our [website](https://crits.github.io) for more information, documentation, and links to community content such as our mailing lists and IRC channel.

## Project Status

> **Note**: This repository contains ongoing modernization work to update CRITs from Python 2.7 to Python 3.12+ and Django 1.x to Django 4.2.

### Current Status (v5.0.0-dev)

| Component | Status |
|-----------|--------|
| Python 3.12 | ✅ Working |
| Django 4.2 | ✅ Working |
| MongoDB 7.x | ✅ Working |
| Docker Compose | ✅ Working |
| Web UI (Login/Dashboard) | ✅ Working |
| User Management | ✅ Working |
| Domains | ✅ Working |
| GraphQL API (FastAPI + Strawberry) | ✅ Working |
| REST API (tastypie) | ❌ Disabled (incompatible) |
| Services/Plugins | ⚠️ Untested |

### What's Working

- User authentication and login
- Dashboard and navigation
- Domain management
- IP management (requires source permissions)
- User administration
- Basic CRUD operations
- GraphQL API for programmatic access (indicators query)

### Known Limitations

- **REST API disabled**: The legacy tastypie-based API is incompatible with modern MongoEngine. A new GraphQL API using FastAPI + Strawberry is now available.
- **Some features untested**: Services, bulk operations, and some advanced features may have compatibility issues.
- **Source permissions**: Some operations require proper source access configuration.

## Requirements

- Python 3.12+
- MongoDB 7.x
- Redis 7.x (for caching/sessions)
- Docker & Docker Compose (recommended)

## Quick Start with Docker Compose

The easiest way to run CRITs is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/crits/crits.git
cd crits

# Start all services (first run - initializes database)
CRITS_INIT_DB=true docker compose up -d

# View logs
docker compose logs -f web

# Access the web UI
open http://localhost:8080
```

### First-Time Setup

After starting the containers, you need to create an admin user:

```bash
# Create admin user (password must be complex: uppercase, lowercase, number, special char)
docker compose exec web uv run python manage.py users -a -u admin -e admin@example.com

# Note the temporary password output, then reset it to something memorable:
docker compose exec web uv run python manage.py shell -c "
from crits.core.user import CRITsUser
user = CRITsUser.objects(username='admin').first()
user.set_password('YourComplexPassword123!')
"

# Create default roles and collections
docker compose exec web uv run python manage.py shell -c "
from crits.core.management.commands.create_roles import add_uber_admin_role, add_readonly_role, add_analyst_role
from crits.core.management.commands.create_default_dashboard import create_dashboard
from crits.core.management.commands.create_default_collections import populate_tlds
add_uber_admin_role(False)
add_readonly_role()
add_analyst_role()
create_dashboard(False)
populate_tlds(True)
"
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 8080 | Reverse proxy, serves static files |
| web | - | Django/Gunicorn application |
| api | - | FastAPI + GraphQL API server |
| mongodb | 27017 | MongoDB database |
| redis | 6379 | Redis cache |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable Django debug mode |
| `SECRET_KEY` | (generated) | Django secret key |
| `SECURE_COOKIES` | `false` | Require HTTPS for cookies |
| `SECURE_SSL_REDIRECT` | `false` | Redirect HTTP to HTTPS |
| `CSRF_TRUSTED_ORIGINS` | localhost | Comma-separated trusted origins |
| `CRITS_INIT_DB` | `false` | Initialize database on startup |

## GraphQL API

CRITs includes a modern GraphQL API built with FastAPI and Strawberry. The API shares authentication with the Django web UI via session cookies.

### Endpoint

- **URL**: `http://localhost:8080/api/graphql`
- **GraphiQL**: Available at the same URL in your browser for interactive exploration

### Authentication

The API uses Django session authentication. Log in to the web UI first, then your session cookie will authenticate GraphQL requests.

### Example Queries

**Health check (no auth required):**
```graphql
query {
  health
}
```

**Get current user:**
```graphql
query {
  me {
    username
    email
    isAdmin
  }
}
```

**List indicators:**
```graphql
query {
  indicators(limit: 10) {
    id
    value
    indType
    status
    tlp
    campaigns
  }
}
```

**Filter indicators by type:**
```graphql
query {
  indicators(indType: "Address - ipv4-addr", limit: 5) {
    id
    value
    description
  }
}
```

**Get indicator count:**
```graphql
query {
  indicatorsCount
  indicatorTypes
}
```

### Test Data

To create sample indicators for testing:

```bash
docker compose exec web uv run python scripts/bootstrap_test_data.py
```

## Legacy Installation

<details>
<summary>Click to expand legacy installation instructions</summary>

The following instructions are from the original CRITs project and may not work with the modernized codebase.

### Quick install using bootstrap

CRITs comes with a bootstrap script which will help you:

* Install all of the dependencies.
* Configure CRITs for database connectivity and your first admin user.
* Get MongoDB running with default settings.
* Use Django's runserver to quickly get you up and running with the CRITs interface.

Just run the following:

```bash
sh script/bootstrap
```

Once you've run bootstrap once, do not use it again to get the runserver going, you'll be going through the install process again. Instead use the server script:

```bash
sh script/server
```

### Production CRITs install

If you are looking for a more permanent and performant CRITs installation or just interested in tweaking things, read more about setting up CRITs for [production](https://github.com/crits/crits/wiki/Production-grade-CRITs-install).

</details>

## Development

### Running Tests

```bash
# Run the environment validation test
make env-test-full

# Run Python tests
docker compose exec web uv run pytest
```

### Local Development

```bash
# Install dependencies
uv sync --extra dev --extra fuzzy

# Run development server
uv run python manage.py runserver
```

## Contributing

Contributions are welcome! Please note that this project is undergoing significant modernization. Key areas that need work:

- Fixing remaining Python 3 / Django 4 compatibility issues
- Implementing a new REST API (FastAPI + GraphQL)
- Adding test coverage
- Updating documentation

## License

CRITs is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## What's next?

We recommend adding services to your CRITs install. Services extend the features and functionality of the core project allowing you to enhance CRITs based on your needs. You can find more information about how to do this [here](https://github.com/crits/crits/wiki/Adding-services-to-CRITs).

**Thanks for using CRITs!**
