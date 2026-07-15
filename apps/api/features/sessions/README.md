# Interview Session Runtime — Architecture

Real-time engine for conducting AI-powered voice interviews.
Manages session lifecycle, WebSocket signaling, AI orchestration,
and connection recovery.

## Directory Structure

```
apps/api/
├── ai/realtime/                          # Runtime engine (no framework deps)
│   ├── __init__.py
│   ├── state_machine.py                  # Session state transitions
│   ├── session_manager.py                # In-memory session registry
│   ├── orchestrator.py                   # AI turn-loop orchestration
│   ├── memory_manager.py                 # Sliding-window conversation buffer
│   ├── prompt_builder.py                 # Prompt template loading + interpolation
│   ├── transcript_manager.py             # Transcript segment recording
│   ├── event_dispatcher.py               # In-process pub/sub event bus
│   └── heartbeat.py                      # Connection health monitoring
│
└── features/sessions/                    # HTTP/WS interface layer
    ├── __init__.py
    ├── models.py                         # SessionEvent ORM model
    ├── schemas.py                        # Pydantic request/response + WS schemas
    ├── repository.py                     # Event persistence
    ├── service.py                        # Session orchestration service
    ├── routes.py                         # REST endpoints + WebSocket handler
    ├── dependencies.py                   # DI wiring
    └── tests/
        ├── test_state_machine.py         # 17 tests
        ├── test_memory_manager.py        # 8 tests
        ├── test_prompt_builder.py        # 8 tests
        ├── test_transcript_manager.py    # 6 tests
        ├── test_event_dispatcher.py      # 5 tests
        ├── test_session_manager.py       # 15 tests
        └── test_integration.py           # 6 tests (requires mocked deps)
```

## Session State Machine

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │INITIALIZI│
                    │   NG     │
                    └────┬─────┘
                         │
              ┌─────▶ ACTIVE ◀─────┐
              │         │          │
              │    pause│     resume│
              │         │          │
              │   ┌────▼─────┐     │
              └───│ PAUSED   │─────┘
              │    └──────────┘
              │         │
              │    time │ expires
              │         │
              │    ┌────▼─────┐
              └───▶COMPLETING│
                   └────┬─────┘
                        │
                   ┌────▼─────┐
                   │COMPLETED │
                   └──────────┘

        FAILED / TIMEOUT ← (from any active state)
```

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/sessions` | Start a new interview session |
| GET | `/api/v1/sessions/{id}` | Get session status |
| POST | `/api/v1/sessions/{id}/pause` | Pause the interview |
| POST | `/api/v1/sessions/{id}/resume` | Resume the interview |
| POST | `/api/v1/sessions/{id}/end` | Gracefully end |
| GET | `/api/v1/sessions/{id}/reconnect` | Check reconnection eligibility |
| WS | `/api/v1/sessions/{id}/ws` | Real-time communication |

## WebSocket Message Protocol

### Client → Server

| Type | Payload | Description |
|------|---------|-------------|
| `session.join` | `{ session_id, token }` | Join session |
| `user.answer` | `{ text, timestamp_ms }` | Submit answer |
| `user.code` | `{ code, language }` | Submit code |
| `session.pause` | `{}` | Pause |
| `session.resume` | `{}` | Resume |
| `session.request_hint` | `{}` | Request hint |
| `media.stream_ready` | `{ sdp, ice_candidates }` | WebRTC signal |
| `heartbeat` | `{ timestamp }` | Keepalive (10s) |

### Server → Client

| Type | Payload | Description |
|------|---------|-------------|
| `session.connected` | `{ session_id, state }` | Connection ack |
| `ai.question` | `{ id, text, type }` | AI question |
| `ai.hint` | `{ text }` | AI hint |
| `session.paused` | `{ state, remaining_seconds }` | Pause ack |
| `session.resumed` | `{ state, remaining_seconds }` | Resume ack |
| `session.completing` | `{}` | Wrap-up phase |
| `session.completed` | `{ interview_id }` | Interview done |
| `timer.tick` | `{ remaining_seconds }` | Every 5s |
| `timer.warning` | `{ remaining_seconds }` | 5min/1min |
| `heartbeat_ack` | `{ timestamp }` | Keepalive ack |
| `error` | `{ code, message }` | Error info |

## Core Design Decisions

1. **Session manager is in-memory**. Active sessions live in a dict. Snapshots persist to DB at key transitions via the event sourcing table.

2. **Evaluation is async**. The interview completes immediately. Evaluation runs as a background worker and notifies when ready.

3. **Turn-based AI**. AI operates in rounds: question → answer → next question. This avoids real-time interruption complexity. Barge-in can be added later.

4. **Media never touches the app server**. The client sends audio directly to Deepgram (STT). The WebSocket handles only signaling and text.

5. **Event sourcing** via `session_events` table enables reconnection replay and audit logging.

## Error Recovery

| Scenario | Strategy |
|----------|----------|
| Network drop | 30s grace period. Client reconnects with `session.join`. Server replays context. |
| AI provider failure | 3 retries with exponential backoff. Fallback message on final failure. |
| Browser crash | On reload, detect active session from localStorage flag. Reconnect via WS. |
| Concurrent tab | Server rejects second WS connection for same session. |

## Reconnection Flow

```
Client                                Server
   │                                    │
   │  WS disconnect                     │
   │────────────────────────────────────  Mark offline
   │                                    │  Start 30s grace timer
   │                                    │
   │  WS reconnect                      │
   │────────────────────────────────────  session.rejoin
   │                                    │  Send missed events from buffer
   │  session.resumed                   │
   │◄────────────────────────────────────
   │  current_question                  │
   │◄────────────────────────────────────
   │  Resume normal flow                │
```

## Configuration

All settings in `core/config.py`:

| Key | Default | Description |
|-----|---------|-------------|
| `AI_INTERVIEWER_MODEL` | gpt-4o-mini | Model for interviewer |
| `AI_EVALUATOR_MODEL` | gpt-4o | Model for evaluation |
| `AI_MAX_TOKENS_PER_INTERVIEW` | 10000 | Per-interview token cap |
| `AI_COST_CAP_DOLLARS` | 0.30 | Per-interview cost cap |
| `INTERVIEW_DURATION_MINUTES` | 30 | Default duration |
| `GRACE_PERIOD_MINUTES` | 10 | Disconnect grace period |
