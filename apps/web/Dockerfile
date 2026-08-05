FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate

# NEXT_PUBLIC_* values are inlined into the client bundle at build time, so
# they must be baked in here. Pass them via --build-arg; unset args fall back
# to the app's defaults (see apps/web/env.ts and lib/feature-flags.ts).
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_SENTRY_DSN
ARG NEXT_PUBLIC_APP_VERSION
ARG NEXT_PUBLIC_FF_INTERVIEWS
ARG NEXT_PUBLIC_FF_REPORTS
ARG NEXT_PUBLIC_FF_SETTINGS
ARG NEXT_PUBLIC_FF_NEW_INTERVIEW
ARG NEXT_PUBLIC_FF_ANALYTICS

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/ packages/

RUN pnpm install --frozen-lockfile --filter @tayari/web

COPY apps/web apps/web
RUN pnpm --filter @tayari/web build

FROM node:22-alpine AS runner

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/apps/web/.next .next
COPY --from=builder /app/apps/web/public public
COPY --from=builder /app/apps/web/package.json package.json
COPY --from=builder /app/apps/web/next.config.ts next.config.ts
COPY --from=builder /app/node_modules node_modules

EXPOSE 3000

CMD ["pnpm", "start"]
