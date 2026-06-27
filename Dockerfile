# syntax=docker/dockerfile:1
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_MAJOR=22 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Node.js, PostgreSQL 17, Redis, nginx, supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    gnupg \
    build-essential \
    libpq-dev \
    gettext-base \
    nginx \
    supervisor \
    redis-server \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17 postgresql-client-17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure PostgreSQL to listen on localhost (IPv4 + IPv6) and allow local trust
RUN mkdir -p /var/log/postgresql /var/run/postgresql \
    && chown -R postgres:postgres /var/log/postgresql /var/run/postgresql /var/lib/postgresql \
    && sed -i 's/scram-sha-256/trust/g' /etc/postgresql/17/main/pg_hba.conf \
    && echo "listen_addresses = '127.0.0.1, ::1'" >> /etc/postgresql/17/main/postgresql.conf

# Configure Redis to listen on localhost
RUN sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf \
    && sed -i 's/^daemonize yes/daemonize no/' /etc/redis/redis.conf || true \
    && mkdir -p /var/lib/redis && chown redis:redis /var/lib/redis

# Create app directories
WORKDIR /app
RUN mkdir -p /app/backend /app/web /var/log/supervisor /var/log/nginx

# ---- Backend ----
COPY backend/pyproject.toml backend/README.md backend/alembic.ini ./backend/
COPY backend/src ./backend/src
COPY backend/alembic ./backend/alembic
RUN python -m venv /app/backend/.venv \
    && /app/backend/.venv/bin/pip install --upgrade pip \
    && /app/backend/.venv/bin/pip install -e /app/backend

# ---- Frontend ----
COPY web/package.json web/package-lock.json* web/pnpm-lock.yaml* ./web/
# Install frontend dependencies (supports npm; pnpm lockfile would need pnpm)
RUN if [ -f /app/web/pnpm-lock.yaml ]; then npm install -g pnpm && pnpm install --prefix /app/web; else npm install --prefix /app/web; fi

COPY web ./web
RUN cd /app/web && npm run build

# Copy runtime configs
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the default Railway/HTTP port (Railway overrides with $PORT)
EXPOSE 3000

CMD ["/app/start.sh"]
