# ADR-003: AI Provider Abstraction

## Status
Accepted

## Context
We use OpenAI for both the interviewer and evaluator. Locking directly into OpenAI's SDK makes it difficult to switch providers or use local models for testing.

## Decision
Create an abstract `AIProvider` base class with `chat()`, `chat_stream()`, and `structured_output()` methods. Implement `OpenAIProvider` as the first concrete provider. All feature code depends on the abstraction, not the implementation.

## Consequences
- Easy to add Anthropic, Google, or local (Ollama) providers later
- Slight indirection overhead but negligible for AI-bound calls
- Enables injecting mock providers in tests
