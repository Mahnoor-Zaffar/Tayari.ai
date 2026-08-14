# Deploying Tayari AI to Fly.io

This guide deploys the Tayari AI monorepo (FastAPI + Next.js + PostgreSQL) on
[Fly.io](https://fly.io). Containers run long-lived with native WebSocket
support — required for the live voice interviews — and the stack stays a
single-machine-per-app shape:

```
Local Docker → Fly.io → Fly.io + managed DB → larger distributed architecture
```

Redis **does not need a separate service**: `redis-server` runs inside the API
container (`127.0.0.1:6379`, persistence disabled) for the JWT blacklist and
shared rate limiting. The app defaults `REDIS_URL` to that address.

---

## Architecture on Fly.io

| App | Purpose | Build | Runs |
| --- | --- | --- | --- |
| `tayari-api` | FastAPI + embedded Redis + APScheduler | `apps/api/Dockerfile` | `apps/api/fly.toml` |
| `tayari-web` | Next.js | `apps/web/Dockerfile` (context = repo root) | `fly.toml` (repo root) |
| `tayari-pg` | PostgreSQL (managed) | Fly Postgres app | created via CLI |

Config lives in code:

- `apps/api/fly.toml` — build, `release_command = alembic upgrade head`,
  `/ready` healthcheck, no auto-stop (WebSockets must stay connected).
- `fly.toml` — web build args (`NEXT_PUBLIC_*`, baked at build time), `/`
  healthcheck.

---

## Prerequisites

- [Fly.io](https://fly.io) account; `brew install flyctl` (or
  `curl -L https://fly.io/install.sh | sh`).
- `fly auth login`.
- The repo checked out locally.

---

## Step 1 — Create the API app

```sh
cd apps/api
fly launch --no-deploy --copy-config --region <region>   # e.g. --region ams, iad, ...
```

- `--copy-config` reuses `apps/api/fly.toml` (so edits to the file are kept).
- `--no-deploy` builds nothing yet; Database will be wired below.

## Step 2 — Provision PostgreSQL

```sh
fly postgres create --name tayari-pg --region <region>
fly postgres attach tayari-pg      # runs from apps/api
```

Attach sets a `DATABASE_URL` secret in the `postgres://…` scheme, but the app
requires the `asyncpg` driver. Convert the scheme and force the value:

```sh
fly ssh console -C 'printenv DATABASE_URL'     # show the generated URL
fly secrets set "DATABASE_URL=postgresql+asyncpg://<user>:<password>@tayari-pg.internal:5432/<db>"
```

(You can also use any managed Postgres such as Neon and set `DATABASE_URL` the
same way.)

## Step 3 — Set API secrets

```sh
fly secrets set JWT_SECRET_KEY="$(openssl rand -base64 48)"
fly secrets set OPENAI_API_KEY=... RESEND_API_KEY=... DEEPGRAM_API_KEY=...
fly secrets set ADMIN_EMAILS="you@example.com"       # remove the default admin@tayari.ai
# optional: SENTRY_DSN, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
#           SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_*
```

Public defaults (`ENVIRONMENT`, `JWT_ALGORITHM=HS256`, `CORS_ORIGINS`,
`FRONTEND_URL`, `PUBLIC_API_URL`) are already in `apps/api/fly.toml` — edit
them there and redeploy. The full list with notes is in
[`.env.fly.example`](../.env.fly.example).

> **JWT:** keep `JWT_ALGORITHM=HS256` with a 48-byte random `JWT_SECRET_KEY`.
> The config default is `RS256`, which needs a real RSA keypair — a plain
> secret under RS256 makes signup fail with a 500.
>
> **Admin:** admin is only granted to an `ADMIN_EMAILS` address after that
> email is verified. Replace the default e2e `admin@tayari.ai` in production.

## Step 4 — Deploy the API

```sh
fly deploy
```

Before starting, Fly runs `fly_toml.release_command` →
`uv run alembic upgrade head`, creating all tables. Then the container starts
`redis-server` + `uvicorn`. Verify with:

```sh
curl https://tayari-api.fly.dev/ready
# {"status":"ok","dependencies":{"database":"ok"}}
```

## Step 5 — Create + deploy the web app

From the **repo root** (the web Dockerfile builds the whole monorepo):

```sh
fly launch --no-deploy --copy-config --region <region>
fly deploy
```

`NEXT_PUBLIC_API_URL` is baked to `https://tayari-api.fly.dev` in `fly.toml`
build args; the WebSocket URL is derived from it automatically
(`wss://tayari-api.fly.dev`). Feature flags default to enabled in the build
args — remove any flag you want off.

```sh
curl -s -o /dev/null -w '%{http_code}\n' https://tayari-web.fly.dev   # 200
```

## Step 6 — Custom domain + Cloudflare

1. `fly domains add api.tayari.ai` (run in `apps/api`) and `fly domains add tayari.ai` (repo root).
2. Follow the per-domain instructions (`fly certs show …`) to add the DNS
   records at your DNS provider, or put **Cloudflare** in front:
   - CNAME `api` → `tayari-api.fly.dev` and `@`/`tayari.ai` → `tayari-web.fly.dev`
     (proxied), plus a Cloudflare Full/strict TLS cert since Fly serves HTTPS.
   - Do **not** cache `/` or API paths — interviews are live and dynamic.
3. Update `CORS_ORIGINS`, `FRONTEND_URL`, `PUBLIC_API_URL` in
   `apps/api/fly.toml` and `NEXT_PUBLIC_API_URL` in `fly.toml`, then redeploy both.

## Step 7 — Verify end-to-end

- Register an account → complete email verification → confirm a `ADMIN_EMAILS`
  address only gets admin **after** verification.
- Start an interview (verifies WebSockets end-to-end).
- Complete one → confirm the background evaluation runs (APScheduler, in-process).

---

## Runtime ops

| Task | Command |
| --- | --- |
| API logs | `fly logs` (in `apps/api`) |
| Web logs | `fly logs` |
| Manual migration | `fly ssh console -C 'uv run alembic upgrade head'` |
| Scale (api) | `fly scale memory 1024` |
| Secrets | `fly secrets list` / `fly secrets set K=V` |

---

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| Signup returns 500, logs show `Unable to load PEM file` | `JWT_ALGORITHM=RS256` with a plain secret — set `HS256` |
| `/ready` shows `database: unreachable` | `DATABASE_URL` scheme is wrong or Postgres not attached — use `postgresql+asyncpg://…` |
| {`429`} on login | Redis-backed rate limiter counting attempts; expected after repeated failures |
| Emails not sent | `RESEND_API_KEY` missing (verification/reset silently skip) |
| Admin route 403 | `ADMIN_EMAILS` not set, or that address not verified |
| Deploy stuck building web | Build context must be the **repo root** (root `fly.toml`) |