# EDOF-NETZ

Tek konteynerde çalışan, Railway'e taşınmaya hazır CPF/EDOF yönetim ERP'si.

## Stack

- **Frontend:** Next.js 15 + React 19 + TypeScript
- **Backend:** FastAPI + Pydantic v2 + SQLModel + Alembic
- **Queue / Background:** Celery + Redis
- **Database:** PostgreSQL 17
- **Reverse Proxy:** nginx
- **Process Manager:** supervisord

## Lokal Çalıştırma

```bash
docker compose up --build
```

Açılacak adresler:

- UI: http://localhost:3000
- API docs: http://localhost:3000/docs
- API health: http://localhost:3000/api/health

## Railway Deploy

1. Repoyu Railway'e bağlayın.
2. `railway.json` otomatik olarak Dockerfile'dan build alır.
3. Railway panelinden aşağıdaki volume'leri ekleyin:
   - `pgdata` → `/var/lib/postgresql/17/main`
   - `redisdata` → `/var/lib/redis`
4. Gerekli environment variable'ları (SECRET_KEY, WEDOF_API_KEY, PENNYLANE_API_TOKEN vb.) Railway'de tanımlayın.

## Ortam Değişkenleri

| Değişken | Açıklama |
|----------|----------|
| `PORT` | Railway tarafından otomatik atanır (default: 3000) |
| `SECRET_KEY` | JWT / session imzalama anahtarı |
| `DATABASE_URL` | PostgreSQL bağlantı URL'i |
| `REDIS_URL` | Redis bağlantı URL'i |
| `WEDOF_API_KEY` | Wedof API anahtarı |
| `PENNYLANE_API_TOKEN` | Pennylane API token'ı |
