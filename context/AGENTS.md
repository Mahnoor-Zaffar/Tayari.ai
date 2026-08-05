# AGENTS.md

# Tayari.ai — AI Coding Agent Entry Point

Welcome to the Tayari.ai codebase.

This project is a production-grade AI Interview Platform designed to demonstrate senior-level software engineering, scalable backend architecture, real-time communication, AI orchestration, and production-ready system design.

Before making **any** implementation or architectural decision, you **must** read the project context files listed below.

---

# Required Reading Order

Read these files in the following order before making any code changes.

1. `context/project-overview.md`
   - Product vision
   - Goals
   - Core user flows
   - Feature list
   - Scope boundaries
   - Success criteria

2. `context/architecture.md`
   - System architecture
   - Technology stack
   - Module boundaries
   - Storage model
   - Authentication
   - AI architecture
   - System invariants

3. `context/code-standards.md`
   - Coding conventions
   - Project structure
   - Backend standards
   - Frontend standards
   - Testing conventions

4. `context/ui-context.md`
   - Design system
   - Component conventions
   - Layout rules
   - Typography
   - Color tokens
   - Animation guidelines

5. `context/ai-workflow-rules.md`
   - Mandatory implementation rules
   - Development workflow
   - Scope management
   - Verification process

6. `context/progress-tracker.md`
   - Current sprint
   - Completed work
   - Current implementation
   - Next priorities
   - Open questions
   - Architecture decisions

If additional context files exist (for example `ai-architecture.md`, `deployment.md`, or `security.md`), read those before implementing work related to those domains.

---

# Implementation Workflow

Every task should follow the same workflow.

## Phase 1 — Understand

Before writing code:

- Read the required context.
- Understand the requested feature.
- Identify the affected modules.
- Verify dependencies.
- Review existing patterns.
- Do not make assumptions.

If requirements are ambiguous, stop and ask for clarification.

---

## Phase 2 — Plan

Before implementation:

- Determine the affected features.
- Keep changes within the appropriate module.
- Avoid cross-feature coupling.
- Reuse existing abstractions where possible.
- Do not introduce technical debt.

---

## Phase 3 — Implement

Implement only the requested scope.

Do not:

- Refactor unrelated code.
- Rename files unnecessarily.
- Change architecture without approval.
- Introduce speculative features.
- Add unnecessary dependencies.

Respect all architectural boundaries.

---

## Phase 4 — Verify

Before considering work complete:

- Build successfully.
- Pass linting.
- Pass type checking.
- Pass tests.
- Verify no regressions.
- Verify responsive UI (if applicable).
- Verify security implications.
- Review code quality.

---

## Phase 5 — Update Documentation

If implementation changes:

- Architecture
- Public APIs
- Environment variables
- Deployment
- User-facing functionality

Update the appropriate documentation before finishing.

Also update:

`context/progress-tracker.md`

---

# Project Principles

Always optimize for:

- Maintainability
- Scalability
- Security
- Readability
- Performance
- Testability
- Production readiness

Never optimize only for speed of implementation.

---

# Architecture Principles

This project follows a feature-first modular architecture.

Backend:

- Routes
- Services
- Repositories
- Schemas
- Models
- Tests

Frontend:

- App Router
- Features
- Components
- Hooks
- Shared UI

Business logic must never exist inside routes or UI components.

---

# AI Development Principles

This project uses AI extensively.

Maintain clear separation between:

- Prompt templates
- Prompt builders
- AI providers
- Conversation memory
- Evaluation logic
- Session orchestration

Never hardcode prompts into business logic.

---

# Security Requirements

Security is mandatory.

Always:

- Authenticate requests.
- Verify authorization.
- Validate ownership.
- Validate user input.
- Protect WebSockets.
- Protect background jobs.
- Prevent injection attacks.
- Prevent path traversal.
- Respect RBAC.

Never bypass security checks for convenience.

---

# Definition of Done

A task is complete only when:

- Requirements are fully implemented.
- Code follows project architecture.
- Tests pass.
- Documentation is updated.
- No known regressions exist.
- Security has been considered.
- Performance remains acceptable.

---

# Progress Tracking

At the beginning of each implementation:

- Read `context/progress-tracker.md`.

At the end of each implementation:

- Mark completed work.
- Update current status.
- Record architectural decisions.
- Record any new technical debt.
- Record next recommended task.

---

# Final Rule

If the requested implementation conflicts with the documented architecture, standards, or workflow:

**Stop.**

Explain the conflict clearly.

Request clarification before making changes.

Do not silently change the architecture or project conventions.