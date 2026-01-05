# Ticket Managing App (Docker + Simple Frontend)

This repository contains three FastAPI services (auth, event, client) and a minimal demo frontend.

## Quick start (Docker Compose)

1. Build and start everything:

   docker compose up --build

2. Services:
   - Auth: http://localhost:8000
   - Event: http://localhost:8001
   - Client: http://localhost:8002
   - Frontend (demo): http://localhost:3000

Notes:
- Mongo is included for the client service and is accessible at mongodb://localhost:27017 when running compose.
- SQLite DB files for `auth` and `event` are stored under `./data/auth` and `./data/event` on the host (created by compose).

## Development notes
- Backend services read configuration from environment variables (examples shown in `docker-compose.yml`):
  - `DATABASE_URL` for SQLite (e.g. `sqlite:////data/auth.db`)
  - `MONGO_URL` and `MONGO_DB` for the client service
  - `EVENT_SERVICE_URL` for the client to reach the event service
  - `CORS_ORIGINS` to configure allowed origins (comma-separated or `*`)

## Minimal smoke checks
- After `docker compose up` visit the frontend at `http://localhost:3000` and click *Load Events*.

