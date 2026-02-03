# CRITs React UI

Modern React frontend for CRITs threat intelligence platform.

## Security: Package Manager

**IMPORTANT: Use pnpm only - do NOT use npm or yarn**

This project uses [pnpm](https://pnpm.io/) exclusively for supply chain security reasons:

1. **Strict lockfile**: pnpm's lockfile format is more secure and harder to tamper with
2. **Content-addressable storage**: Packages are verified by content hash
3. **No phantom dependencies**: pnpm creates a strict node_modules structure that prevents accessing undeclared dependencies
4. **Faster and more efficient**: Uses hard links to save disk space

### Install pnpm

```bash
# Using corepack (recommended, built into Node.js 16.13+)
corepack enable
corepack prepare pnpm@10 --activate

# Or via npm (one-time only)
npm install -g pnpm@10
```

### Commands

```bash
# Install dependencies
pnpm install

# Development server
pnpm dev

# Build for production
pnpm build

# Type check
pnpm type-check

# Lint
pnpm lint
```

## Development

The UI runs at `http://localhost:3000` in development mode with hot reload.

API requests are proxied to the FastAPI backend at `http://localhost:8001`.

## Production

In production, the UI is built and served by nginx at `/app/` path:
- React UI: `http://localhost:8080/app/`
- Django UI (legacy): `http://localhost:8080/`
- GraphQL API: `http://localhost:8080/api/graphql`

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TanStack Query** - Data fetching
- **TanStack Table** - Data tables
- **React Router** - Routing
- **Lucide React** - Icons
