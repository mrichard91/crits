# CRITs Next

This directory contains an experimental rewrite of CRITs using modern technologies. The goal is to create a Python 3.12+ backend powered by FastAPI and GraphQL with a React-based frontend.

## Structure

- `backend/` – FastAPI project exposing a basic GraphQL endpoint.
- `frontend/` – React application bootstrapped with Vite.

Both sides are intentionally minimal to provide a starting point for further development.

## User Management

The backend now includes a lightweight user management system with Google OAuth.
Users and their preferences are stored in a local SQLite database. Admin users can
edit preferences and permissions via a simple management UI exposed in the
frontend.

### Docker Development

Dockerfiles are provided for both frontend and backend along with a
`docker-compose.yml` at the repository root. To start the stack, run:

```bash
docker-compose up --build
```

The frontend will be available on port `3000` and the backend on port `8000`.

