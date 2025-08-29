# CRITs Next Backend

This is a minimal FastAPI project exposing a GraphQL API using Strawberry.

## Requirements

- Python 3.12+
- Dependencies from `requirements.txt`

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000/graphql`.

