# CRITs Next

This directory contains an experimental rewrite of CRITs using modern technologies. The goal is to create a Python 3.12+ backend powered by FastAPI and GraphQL with a React-based frontend.

## Structure

- `backend/` – FastAPI project exposing a basic GraphQL endpoint.
- `frontend/` – React application bootstrapped with Vite.

Both sides are intentionally minimal to provide a starting point for further development.

## User management and Google auth

The example application now includes a very small user management system. Users can
authenticate with Google, and their preferences and permissions are stored in the
backend. An administrator panel in the React frontend allows viewing and updating
these details.

## Running with Docker

A basic Docker setup is provided for local testing:

```bash
cd crits_next
docker compose up --build
```

The frontend will be available on `http://localhost:3000` and expects a Google OAuth
client id provided via the `VITE_GOOGLE_CLIENT_ID` environment variable.

