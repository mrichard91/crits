"""
FastAPI application for CRITs GraphQL API.

This API runs alongside Django, sharing MongoEngine models and user sessions.
nginx routes /api/graphql to this service.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from crits_api.config import settings
from crits_api.db.connection import connect_mongodb
from crits_api.graphql.schema import schema
from crits_api.graphql.context import get_context

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting CRITs GraphQL API...")
    connect_mongodb()
    logger.info(f"Connected to MongoDB at {settings.mongo_host}:{settings.mongo_port}")

    yield

    # Shutdown
    logger.info("Shutting down CRITs GraphQL API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="GraphQL API for CRITs threat intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handler for better error visibility in debug mode
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Log unhandled exceptions and return error details in debug mode."""
    logger.exception(f"Unhandled exception: {exc}")
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "crits-api",
        "version": "0.1.0",
    }


# Mount GraphQL router
graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=settings.graphiql_enabled,
)
app.include_router(graphql_router, prefix=settings.graphql_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "crits_api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
    )
