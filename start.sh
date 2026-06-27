#!/bin/bash
set -e

export PORT="${PORT:-3000}"
export DATABASE_URL="${DATABASE_URL:-postgresql://edofnetz:edofnetz@localhost:5432/edofnetz}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}"
export SECRET_KEY="${SECRET_KEY:-local-secret-key-change-in-production}"

export PGDATA="${PGDATA:-/var/lib/postgresql/17/main}"

# Ensure PostgreSQL data directory exists and is owned by postgres
mkdir -p "$PGDATA"
chown -R postgres:postgres "$PGDATA"
chmod 700 "$PGDATA"

# Initialize PostgreSQL if not already initialized
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL in $PGDATA..."
    # Ensure the target directory is empty (Debian package may create it)
    rm -rf "${PGDATA:?}"/*
    su - postgres -c "/usr/lib/postgresql/17/bin/initdb -D '$PGDATA' --auth=trust --encoding=UTF8 --locale=C.UTF-8"
fi

# Start PostgreSQL temporarily to create database/user and run migrations
echo "Starting PostgreSQL temporarily..."
su - postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D '$PGDATA' -o '-c config_file=/etc/postgresql/17/main/postgresql.conf' -l /var/log/postgresql/postgresql.log start"

# Wait for PostgreSQL to be ready
for i in {1..30}; do
    if su - postgres -c "/usr/lib/postgresql/17/bin/pg_isready -q"; then
        break
    fi
    sleep 1
done

# Create user and database if they don't exist
su - postgres -c "psql -v ON_ERROR_STOP=0 -c \"SELECT 1 FROM pg_roles WHERE rolname='edofnetz'\" | grep -q 1 || psql -v ON_ERROR_STOP=0 -c \"CREATE USER edofnetz WITH PASSWORD 'edofnetz';\""
su - postgres -c "psql -v ON_ERROR_STOP=0 -c \"SELECT 1 FROM pg_database WHERE datname='edofnetz'\" | grep -q 1 || psql -v ON_ERROR_STOP=0 -c \"CREATE DATABASE edofnetz OWNER edofnetz;\""
su - postgres -c "psql -v ON_ERROR_STOP=0 -c \"GRANT ALL PRIVILEGES ON DATABASE edofnetz TO edofnetz;\""
su - postgres -c "psql -v ON_ERROR_STOP=0 -d edofnetz -c \"GRANT ALL ON SCHEMA public TO edofnetz;\""

# Run migrations
echo "Running database migrations..."
cd /app/backend
/app/backend/.venv/bin/alembic upgrade head

# Stop temporary PostgreSQL (supervisord will start it)
su - postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D '$PGDATA' -o '-c config_file=/etc/postgresql/17/main/postgresql.conf' stop"

# Prepare Redis data directory
mkdir -p /var/lib/redis
chown -R redis:redis /var/lib/redis || true

# Generate nginx config from template with PORT substitution
echo "Generating nginx config for PORT=$PORT..."
envsubst '$PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start all services via supervisord
echo "Starting all services..."
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
