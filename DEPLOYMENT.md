# Sococo PLIE Showcase - Enterprise Deployment Runbook

This runbook outlines the exact sequence for deploying this monorepo infrastructure to [Railway.app](https://railway.app). The repository contains a decoupled FastAPI orchestration engine (`/backend`) and a Next.js 16 Client (`/frontend`).

## Step 1: Provision Infrastructure
Deploy the foundational data layers first.

1. Create a new Project in your Railway dashboard.
2. Click **New Service** → **Database** → **PostgreSQL**.
3. Click **New Service** → **Database** → **Redis**.

Wait for both instances to fully provision. Railway will automatically generate the internal connection strings.

## Step 2: Deploy the Backend (FastAPI Orchestrator)
Deploy the core engine that handles parallel API gathering and Redis idempotency locks.

1. Click **New Service** → **GitHub Repo**.
2. Select the `sococo-plie-showcase` repository.
3. Once generated, navigate immediately to the Backend Service Settings.
4. Update the **Root Directory** to `/backend`. (Railway will automatically detect the Python `uv` / Dockerfile setup and execute the build).
5. Navigate to the **Variables** tab and inject the following strict Environment Variables:
   - `OPENAI_API_KEY`: Your OpenAI organization key.
   - `POSTGRES_USER`: *(Copy from Railway Postgres Variables)*
   - `POSTGRES_PASSWORD`: *(Copy from Railway Postgres Variables)*
   - `POSTGRES_DB`: *(Copy from Railway Postgres Variables)*
   - `POSTGRES_PORT`: *(Copy from Railway Postgres Variables)*
   - `REDIS_URL`: *(Copy from Railway Redis internal URL)*
   - `PUBLIC_TENANT_ID`: `1` (Required for the public showcase constraint).

*Ensure the backend is healthy and responding before proceeding to Step 3.*

## Step 3: Deploy the Frontend (Next.js Client)
Deploy the Corporate Banking aesthetic UI, configuring the Next.js BFF proxy to bridge internally to the orchestration engine.

1. Click **New Service** → **GitHub Repo** again.
2. Select the *same* `sococo-plie-showcase` repository.
3. Under Service Settings, update the **Root Directory** to `/frontend`.
4. Railway will automatically parse the `package.json` and invoke the standard `next build` and `next start` scripts to stand up the Node.js web server.
5. Navigate to the **Variables** tab and map the internal boundary:
   - `BACKEND_URL`: `http://backend.railway.internal:8000` (Update `backend` precisely to the internal networking name of your specific FastAPI service).

6. Under Settings, ensure Railway generates a **Public Domain** for the frontend service.

The platform is now securely deployed and publicly accessible.
