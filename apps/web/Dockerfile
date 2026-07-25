FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate

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
