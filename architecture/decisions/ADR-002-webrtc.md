# ADR-002: Pseudo-Realtime Voice via Browser APIs (MVP)

## Status
Accepted

## Context
Real-time voice is a core feature but OpenAI Realtime API costs ~$1.80 per 30-min interview. We need a $0-cost voice solution for MVP validation.

## Decision
Use Browser Web Speech API (SpeechRecognition) for STT and Speech Synthesis API for TTS with a chunked recording approach (5-10s chunks). This creates a pseudo-realtime conversational experience at $0 cost.

## Consequences
- Only works well in Chrome (Web Speech API quality varies)
- Higher latency than true realtime (~1-2s vs ~400ms)
- Plan to migrate to OpenAI Realtime API post-MVP when we have paying users
