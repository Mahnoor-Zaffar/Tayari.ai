# ADR-001: Monorepo with pnpm + Turborepo

## Status
Accepted

## Context
The project has a Next.js frontend and a FastAPI backend with shared TypeScript types and UI components. We need a build system that can orchestrate across both.

## Decision
Use pnpm workspaces + Turborepo. TypeScript packages live under `packages/` and are shared via workspace protocol. Turborepo caches builds and runs tasks in dependency order.

## Consequences
- Single repo means atomic commits across frontend and backend
- Turborepo caching speeds up CI
- Python code is not cached by Turborepo but is orchestrated via npm scripts
