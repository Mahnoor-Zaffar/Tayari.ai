# Deploying Tayari AI to Railway

This guide deploys the Tayari AI monorepo (FastAPI + Next.js + Celery + Redis +
PostgreSQL) on [Railway](https://railway.com). It is the **Railway** stage of the
intended evolution path:

```
Local Docker → Railway → Railway + managed DB → larger distributed architecture
```

Once user volume makes database reliability / operational control a concern, move
PostgreSQL to a managed database without moving the application — Railway's
Postgres plugin is already managed, so that decision is independent of the app
hosting.

---

## Architecture on Railway

| Component | Railway service | Source path | Builder |
| --- | --- | --- | --- |
| API (`FastAPI` + `Celery` workers + embedded Redis) | `api` | `apps/api` | `Dockerfile` |
| Web (`Next.js`) | `web` | repo root | `Dockerfile` |
| PostgreSQL | `Postgres` (plugin) | — | — |
| Redis | embedded in the `api` container | — | — |

Config-as-code lives in `apps/api/railway.json` (API service) and
`railway.json` (web service). Railway reads the config file from each service's
source root, so the two files do not collide.

Redis is **embedded** in the API container (`redis-server` on `127.0.0.1:6379`)
so the stack needs only one Railway plugin (Postgres) — handy on the free plan,
which caps how many resources you can provision. The app already defaults
`REDIS_URL` to `redis://localhost:6379/0`, so no extra variable is needed.

Key baked-in settings:

- **API** — `startCommand` launches `redis-server` (background) then `uvicorn`;
  `preDeployCommand` runs `uv run alembic upgrade head` (schema migrations run
  automatically before every deploy); healthcheck is `GET /ready`.
- **Web** — `startCommand` runs `next start` on Railway's injected `PORT`;
  healthcheck is `GET /`.

---

## Prerequisites

- A [Railway](https://railway.com) account (logged in via GitHub).
- The repository pushed to GitHub.
- The `railway` CLI (optional — the dashboard covers everything below):

  ```sh
  brew install railway
  railway login
  ```

---

## Step 1 — Create the project and services

1. In the Railway dashboard click **New Project → Deploy from GitHub repo**,
   select this repository, and create a blank project (do **not** use the
   auto-generated template).
2. Create the **API service**: **New → Empty Service**, then set
   **Source → Source path** to `apps/api`. Railway will build from
   `apps/api/railway.json` + `apps/api/Dockerfile`.
3. Create the **web service**: **New → Empty Service**, set **Source → Source path**
   to the repo root (`.`). Railway builds with `apps/web/Dockerfile` per
   `railway.json`.
4. Add **Postgres**: **New → Database → PostgreSQL** and wait for it to be ready.

   Redis is **not** added as a plugin — it runs inside the `api` container
   (`redis-server` on `127.0.0.1:6379`, launched by the `startCommand`). The app
   defaults `REDIS_URL` to `redis://localhost:6379/0`, which already points at
   it. If you later want managed Redis, set `REDIS_URL` on the `api` service to
   an external URL and it overrides the embedded instance.

5. Optionally rename services (`api`, `web`) for clarity.

## Step 2 — Database URL

The app requires the `asyncpg` driver, so the DB URL must use the
`postgresql+asyncpg://` scheme. Railway's `Postgres.DATABASE_URL` reference only
provides `postgresql://`. Set the API's `DATABASE_URL` as a **composed reference**:

```
DATABASE_URL = postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
```

The Postgres plugin exposes `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`,
`PGDATABASE` as reference variables.

> No `REDIS_URL` variable is required — the embedded `redis-server` is already on
> `127.0.0.1:6379`. Set it only when switching to an external/managed Redis.

## Step 3 — API service variables (secrets checklist)

Add these to the `api` service. Generate strong values locally, never commit them.

| Variable | Value / source |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | composed reference from Step 2 |
| `JWT_ALGORITHM` | `HS256` (simplest) — or `RS256` with a real RSA keypair |
| `JWT_SECRET_KEY` | `openssl rand -base64 48` (see note below) |
| `FRONTEND_URL` | `https://<your-domain>` e.g. `https://tayari.ai` |
| `PUBLIC_API_URL` | `https://api.<your-domain>` (used for CSP `connect-src`) |
| `CORS_ORIGINS` | JSON array string, e.g. `["https://tayari.ai","https://www.tayari.ai"]` |
| `ADMIN_EMAILS` | comma-separated list of admin addresses (must be **verified** to get admin — see security note) |
| `OPENAI_API_KEY` | from OpenAI / model gateway |
| `DEEPGRAM_API_KEY` | for speech-to-text |
| `RESEND_API_KEY` | for verification / reset emails |
| `SENTRY_DSN` | optional error monitoring |
| `STRIPE_SECRET_KEY` | optional billing |
| `STRIPE_WEBHOOK_SECRET` | optional billing webhook |
| `SUPABASE_URL` | optional social login |
| `SUPABASE_SERVICE_KEY` | optional social login |
| `STORAGE_ENDPOINT` / `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` / `STORAGE_BUCKET` | S3-compatible storage for evaluation reports (Railway object storage or external) |

**JWT secret note:** the config default is `JWT_ALGORITHM=RS256`, which requires
a PEM RSA keypair (`SECRET_KEY` = private key). For the simplest secure setup set
`JWT_ALGORITHM=HS256` with `openssl rand -base64 48`. If you use RS256, generate a
keypair and store the private key in `JWT_SECRET_KEY` (newlines are fine in the
Railway variable editor).

**Security note (admin elevation):** admin roles are only granted to an email in
`ADMIN_EMAILS` **after** that address is verified. Registering with an admin email
does not grant admin until the user clicks the verification link — so the default
`admin@tayari.ai` (used by e2e tests) should be removed or replaced in production.

## Step 4 — Web service variables

`NEXT_PUBLIC_*` values are inlined at build time (the web `Dockerfile` declares
them as `ARG`s), so set them as **service variables** before the first build:

| Variable | Value / source |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://api.<your-domain>` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL (if social login is on) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key |
| `NEXT_PUBLIC_SENTRY_DSN` | optional |
| `NEXT_PUBLIC_APP_VERSION` | optional version string |
| `NEXT_PUBLIC_FF_INTERVIEWS` / `NEXT_PUBLIC_FF_REPORTS` / `NEXT_PUBLIC_FF_SETTINGS` / `NEXT_PUBLIC_FF_NEW_INTERVIEW` / `NEXT_PUBLIC_FF_ANALYTICS` | feature flags (`1`/`true` to enable) |

The WebSocket URL is **not** configured separately — the web client derives it
from `NEXT_PUBLIC_API_URL` by swapping `http` → `ws`. Point it at
`https://api.<your-domain>` and WebSockets will target `wss://api.<your-domain>`.

## Step 5 — Migrations

Already wired up: `apps/api/railway.json` declares
`preDeployCommand: uv run alembic upgrade head`, so migrations run automatically
against the Postgres service before the new API container starts. You can also
run them manually with the CLI:

```sh
railway service   # select api
railway run -- uv run alembic upgrade head
```

> Redis is embedded in the API container and ephemeral (persistence disabled).
> A revoked-token blacklist therefore resets if the container restarts — tokens
> stay valid until their natural expiry. This is acceptable for launch; if it
> ever matters, set `REDIS_URL` on the API service to an external managed Redis.

## Step 6 — Custom domain + Cloudflare

1. In Railway, open the **api** service → **Settings → Networking → Generate
   domain** (or add a custom domain) → note the `*.up.railway.app` URLs.
2. Add a custom domain for `api.<your-domain>` and `<your-domain>`.
3. Put **Cloudflare** in front for DNS/CDN/security:
   - Add both Railway `*.up.railway.app` URLs as **CNAME** targets (proxy
     enabled).
   - Ensure WebSockets are allowed through Cloudflare (the `wss://api.*` route).
     No extra config is normally needed — Cloudflare proxies WebSocket upgrades
     by default. Do **not** enable caching on `/` or API paths (Next dynamic
     pages + live interviews must stay uncached).
4. Update the API variables to the final domains and redeploy:
   - `FRONTEND_URL=https://<your-domain>`
   - `PUBLIC_API_URL=https://api.<your-domain>`
   - `CORS_ORIGINS=["https://<your-domain>"]`
   - Web: `NEXT_PUBLIC_API_URL=https://api.<your-domain>`

## Step 7 — Verify

- **API:** `curl https://api.<your-domain>/ready` → `{"status":"ok","database":"ok",...}`
- **Web:** `https://<your-domain>` serves the landing page; login works end-to-end.
- **Migrations:** first deploy runs `alembic upgrade head`; confirm tables exist.
- **Auth:** register a user → complete email verification → confirm an `ADMIN_EMAILS`
  address gains admin only after verification.

---

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `could not translate host name` / connection refused | `DATABASE_URL` scheme is `postgresql://` — use the `postgresql+asyncpg://` composed reference. |
| Deploy logs show `Invalid or expired access token` on login | `JWT_SECRET_KEY` changed between deploys, or `JWT_ALGORITHM=RS256` with a non-RSA key — use a fixed secret + `HS256`. |
| `429` login errors | Redis-backed rate limiter counts across deploys; expected after repeated failures. |
| Emails not sent | `RESEND_API_KEY` unset; verification/reset emails silently no-op. |
| Admin endpoint returns 403 | Email in `ADMIN_EMAILS` not verified yet, or `ADMIN_EMAILS` not set on the API service. |
| WebSocket won't connect | `NEXT_PUBLIC_API_URL` must use the final `https://api.*` domain; confirm Cloudflare proxies `wss://`. |
