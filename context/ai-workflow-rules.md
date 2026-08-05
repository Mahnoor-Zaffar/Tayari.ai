# AI Workflow Rules

> These are mandatory rules for any AI coding agent working on Tayari.ai.
> They are not recommendations. They are constraints that must be followed.

---

# Objective

Build and maintain Tayari.ai as a production-grade AI Interview Platform.

Every implementation should prioritize:

- Scalability
- Maintainability
- Security
- Performance
- Clean Architecture
- Production readiness

Never optimize for speed at the expense of code quality.

---

# Core Philosophy

The AI agent is an implementation engine.

The human is responsible for:

- Product decisions
- Architecture
- System design
- Scope
- Prioritization

The AI is responsible for implementing those decisions accurately.

Never invent product requirements.

Never redesign the architecture unless explicitly instructed.

---

# Development Methodology

Development is **spec-driven**.

Every feature should be implemented only after a specification exists.

Never implement features based on assumptions.

If requirements are ambiguous:

- Stop.
- Explain what is missing.
- Ask for clarification.
- Wait before implementing.

---

# Scope Rules

Only implement the requested feature.

Do not:

- Improve unrelated code.
- Refactor neighboring modules.
- Rename files unnecessarily.
- Change APIs outside the requested scope.
- Add unrelated optimizations.
- Introduce new dependencies unless required.

Small bug fixes discovered during implementation should be reported, not silently fixed, unless explicitly authorized.

---

# Architectural Rules

Never violate these architectural boundaries.

## Backend

Business logic belongs in:

- Services

Database logic belongs in:

- Repositories

HTTP logic belongs in:

- Routes

Validation belongs in:

- Schemas

Persistence belongs in:

- Models

Routes must remain thin.

Repositories must never call other repositories.

Services may orchestrate multiple repositories.

Business logic must never exist inside route handlers.

---

## Frontend

Pages compose features.

Features compose reusable components.

Business logic belongs in hooks or feature services.

Avoid placing business logic directly inside UI components.

Prefer Server Components.

Use Client Components only when interactivity requires them.

Avoid unnecessary client-side rendering.

---

# Project Structure

Respect the feature-first architecture.

Each feature owns:

- routes
- services
- repositories
- schemas
- models
- tests

Do not create cross-feature coupling unless explicitly designed.

Shared utilities belong only inside shared packages.

---

# Code Quality Rules

Every implementation must:

- Follow SOLID principles
- Use dependency injection where appropriate
- Prefer composition over inheritance
- Be strongly typed
- Be asynchronous where possible
- Avoid duplicated logic
- Be easy to test
- Be production-ready

Never leave TODOs for core functionality.

Never ship placeholder implementations unless explicitly requested.

---

# Security Rules

Security is mandatory.

Always:

- Authenticate protected endpoints.
- Verify authorization.
- Validate ownership.
- Sanitize user input.
- Validate uploaded files.
- Prevent path traversal.
- Prevent injection attacks.
- Protect WebSocket endpoints.
- Protect background jobs.
- Respect RBAC.

Never expose secrets.

Never bypass authentication.

Never trust client input.

---

# Performance Rules

Prefer:

- Async I/O
- Efficient database queries
- Pagination
- Lazy loading
- Streaming where appropriate
- Background jobs for long-running work
- Redis for caching

Avoid:

- N+1 queries
- Blocking operations
- Duplicate API calls
- Unnecessary renders
- Loading unnecessary data

---

# AI System Rules

The AI Interview Engine must remain modular.

Separate:

- Prompt templates
- Prompt builders
- Conversation memory
- Evaluation logic
- Model providers
- AI orchestration

Never hardcode prompts inside application logic.

Prompt templates must remain versionable.

LLM providers should remain interchangeable.

---

# Database Rules

Database changes require:

- SQLAlchemy models
- Alembic migrations
- Repository updates
- Tests

Never rely on `create_all()` for production schema changes.

Alembic is the source of truth.

---

# API Rules

Every endpoint should:

- Validate input
- Return typed responses
- Handle expected errors
- Log meaningful failures
- Use consistent response models

Never expose internal exceptions.

Never return inconsistent response shapes.

---

# Testing Rules

Every meaningful implementation should include:

- Unit tests
- Integration tests (when applicable)
- API tests (for new endpoints)

Existing tests must continue passing.

Never reduce test coverage.

---

# Documentation Rules

Whenever implementation changes:

- Architecture
- Public APIs
- Environment variables
- Deployment
- Project structure

Update the corresponding documentation before considering the feature complete.

Documentation is part of the implementation.

---

# Git Workflow

One feature per branch.

One feature per pull request.

Keep commits focused.

Avoid mixing unrelated work.

---

# Dependency Rules

Only install packages when:

- They are required.
- Existing tools cannot solve the problem.

Prefer existing project dependencies.

Avoid dependency bloat.

---

# Error Handling

Never swallow exceptions.

Use the project's structured error hierarchy.

Provide meaningful logs.

Return user-friendly errors.

---

# Production Readiness Checklist

Before considering any feature complete, verify:

- Builds successfully
- Passes linting
- Passes type checking
- Passes tests
- No console errors
- No security regressions
- No performance regressions
- Documentation updated

---

# Definition of Done

A feature is complete only if:

- Requirements are fully implemented.
- Tests pass.
- Documentation is updated.
- Code follows project architecture.
- Security is verified.
- Performance is acceptable.
- No known regressions exist.

If any of these conditions are not met, the feature is not complete.

---

# AI Agent Instructions

At the start of every session:

1. Read all project context files.
2. Read the current progress tracker.
3. Understand the requested scope.
4. Verify architectural consistency.
5. Implement only the requested work.

After implementation:

1. Review the implementation.
2. Verify against the specification.
3. Run the required validation steps.
4. Update documentation if needed.
5. Update `progress-tracker.md`.

Never assume.

Never guess.

Never expand scope.

Build only what has been specified.