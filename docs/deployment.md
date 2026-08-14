# Deploying Tayari AI for free (Vercel + GCP e2-micro)

The app does not need any paid hosting. The chosen **$0/month** stack splits the
monorepo across two always-free services:

| Piece | Hosts it | Runs | Cost |
| --- | --- | --- | --- |
| **Web** (Next.js) | **Vercel** (Hobby, free) | `apps/web`, built from repo root | $0 |
| **API** (FastAPI + embedded Redis + APScheduler) | **GCP `e2-micro`** (Always Free) | `infrastructure/docker-compose.prod.yml` → `apps/api/Dockerfile` | $0 |
| **PostgreSQL** | same VM via Compose (`postgres:17-alpine`) | named volume `pgdata` | $0 |
| **TLS / reverse proxy** | **Traefik** on the same VM | `infrastructure/traefik/traefik.yml` | $0 |

No separate Redis: `redis-server` runs inside the API container
(`127.0.0.1:6379`, persistence disabled) for the JWT blacklist and shared rate
limiting.

```
Browser ──► Vercel (Next.js) ──REST/WS──► Traefik :443 ──► FastAPI (+Redis) ──► Postgres
                                         (GCP e2-micro VM, Docker Compose)
```

---

## Part A — Frontend on Vercel (free)

1. Push the monorepo to GitHub (repo root contains `apps/`).
2. Vercel → **Add New Project** → import the GitHub repo.
3. **Root Directory: `apps/web`** so Vercel builds the Next.js app.
4. Framework preset: **Next.js**; leave build/output commands at their defaults
   (Vercel builds directly, no Dockerfile involved).
5. Add environment variables (Runtime → Production → **Settings → Environment
   Variables**). Use the values in `infrastructure/vercel.env.example` (replace
   `YOURDOMAIN`); core ones:
   - `NEXT_PUBLIC_API_URL=https://api.YOURDOMAIN.com/api/v1` — drives REST **and**
     WebSockets (the frontend derives `wss://` from it)
   - `NEXT_PUBLIC_SITE_URL=https://YOURDOMAIN.com` (metadata/SEO base URL)
   - `NEXT_PUBLIC_APP_VERSION=0.1.0`
   - `NEXT_PUBLIC_FF_INTERVIEWS=1`, `NEXT_PUBLIC_FF_REPORTS=1`,
     `NEXT_PUBLIC_FF_SETTINGS=1`, `NEXT_PUBLIC_FF_NEW_INTERVIEW=1`,
     `NEXT_PUBLIC_FF_ANALYTICS=1`
   - Leave `NEXT_PUBLIC_SUPABASE_URL` / `_ANON_KEY` **blank** unless you want
     Google/GitHub social login (email+password auth needs no Supabase)
   - `NEXT_PUBLIC_SENTRY_DSN` — optional
6. Deploy. Note the web service expects its backend split by the same origin —
   CORS must allow your Vercel domain.

## Part B — Backend on Google Cloud (e2-micro, Always Free)

1. **Sign up** at `cloud.google.com` (card validates with a $0–$1 hold that is
   released; **never billed**).
2. Console → **Compute Engine → Create instance**:
   - Name `tayari-api`, region **us-east1 / us-central1 / us-west1**
   - Machine type **e2-micro** (1 vCPU burstable, 1 GB RAM — this is the
     always-free allowance in those three regions)
   - Boot disk **20–30 GB** (Standard persistent disk, Ubuntu 24.04)
   - Firewall: allow **HTTP** (80) and **HTTPS** (443), plus default SSH
3. Open ports in the VPC firewall rules (Compute Engine auto-creates the
   `default-allow-http` / `default-allow-https` rules if you enable that
   checkbox; otherwise add them under **VPC network → Firewall**).
4. **1 GB RAM is tight** — add swap immediately after first boot:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

## Part C — Deploy the API stack (on the VM)

```bash
sudo apt-get update && sudo apt-get install -y git
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && exit   # re-login, then:

git clone https://github.com/<you>/tayari-ai.git
cd tayari-ai/infrastructure
cp .env.example .env && nano .env       # real passwords, keys, domains
# set DOMAIN + API_DOMAIN to your real domain, and a strong POSTGRES_PASSWORD + JWT_SECRET_KEY
nano traefik/traefik.yml                # change the LetsEncrypt email
docker compose -f docker-compose.prod.yml up -d --build
```

## Part D — DNS

Point A records at the VM's **static/external IP**:
- `api.YOURDOMAIN.com` → VM IP
- Your Vercel site already has its own URL (`*.vercel.app`), or point
  `YOURDOMAIN.com` / `www` at Vercel.

## Part E — Verify

```bash
curl -s https://api.YOURDOMAIN.com/health     # {"status":"ok",...}
curl -sI https://YOURDOMAIN.vercel.app/        # 200
```

The API's embedded Redis, Traefik TLS (Let's Encrypt), and Postgres all run on
the one free VM.

---

## Costs & caveats

- **$0.00/mo** across Vercel + GCP. You only pay OpenAI / Deepgram / Resend
  usage per interview.
- e2-micro bursts; sustained interviews throughput is fine for single users but
  don't expect multi-user load-testing scale.
- Single VM = single point of failure; acceptable for launch.
- Free-tier egress is 1 GB/mo out of GCP (us-east1 etc.) and 100 GB/mo on
  Vercel — plenty for a demo workload, watch it once users upload audio.
- To redeploy: `git pull && docker compose -f docker-compose.prod.yml up -d
  --build` on the VM; Vercel redeploys on push to `main`.