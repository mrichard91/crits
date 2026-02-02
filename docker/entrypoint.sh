#!/bin/bash
set -e

echo "=== CRITs Entrypoint ==="

# Wait for MongoDB to be ready
echo "Waiting for MongoDB..."
MAX_TRIES=30
TRIES=0
while [ $TRIES -lt $MAX_TRIES ]; do
    if uv run python -c "
import os
from pymongo import MongoClient
host = os.environ.get('MONGO_HOST', 'mongodb')
port = int(os.environ.get('MONGO_PORT', 27017))
client = MongoClient(host, port, serverSelectionTimeoutMS=2000)
client.server_info()
print('MongoDB is ready!')
" 2>/dev/null; then
        break
    fi
    TRIES=$((TRIES + 1))
    echo "MongoDB not ready (attempt $TRIES/$MAX_TRIES)..."
    sleep 2
done

if [ $TRIES -eq $MAX_TRIES ]; then
    echo "ERROR: Could not connect to MongoDB after $MAX_TRIES attempts"
    exit 1
fi

# Initialize database if this is first run
if [ "${CRITS_INIT_DB:-false}" = "true" ]; then
    echo "Initializing database..."
    uv run python manage.py create_default_collections || true

    # Create admin user if credentials provided
    if [ -n "${CRITS_ADMIN_USER}" ] && [ -n "${CRITS_ADMIN_PASSWORD}" ]; then
        echo "Creating admin user: ${CRITS_ADMIN_USER}"
        uv run python manage.py users \
            -a \
            -u "${CRITS_ADMIN_USER}" \
            -p "${CRITS_ADMIN_PASSWORD}" \
            -e "${CRITS_ADMIN_EMAIL:-admin@localhost}" \
            -R UberAdmin \
            -s || echo "User may already exist"
    fi
fi

# Collect static files
echo "Collecting static files..."
uv run python manage.py collectstatic --noinput || echo "Static collection skipped"

echo "Starting CRITs..."
exec "$@"
