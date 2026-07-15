# Operational Runbook — Realtime Interview Engine

## Health Checks

| Endpoint | Type | Expected | Frequency |
|---|---|---|---|
| `GET /health` | HTTP | 200 | 30s |
| `GET /api/v1/sessions/{id}` | HTTP | 200/404 | On demand |
| `WS /api/v1/sessions/{id}/ws` | WS | 101 → connected | On demand |

## Monitoring

### Key Metrics

| Metric | Source | Alert Threshold |
|---|---|---|
| `active_sessions` | SessionManager.list_active() | > 500 warn, > 1000 critical |
| `session_errors` | Session.error_count | > 3 per session |
| `ai_latency_ms` | AIResponse.latency_ms | > 5000ms avg |
| `ai_cost_per_session` | CostTracker | > $0.30 |
| `ws_messages_per_second` | Rate limiter counters | > 100/s per server |
| `disconnect_rate` | Session.disconnect_count | > 20% of sessions |
| `heartbeat_misses` | HeartbeatMonitor | > 5 per session |

### Logged Events (structured JSON)

All session events log with:
```
{
  "event": "session.started|completed|failed",
  "session_id": "...",
  "user_id": "...",
  "interview_id": "...",
  "duration_ms": 12345,
  "error": null
}
```

## Alerting

| Alert | Condition | Action |
|---|---|---|
| **High session count** | active_sessions > 1000 | Scale horizontally, check Redis |
| **High AI latency** | avg latency > 5s over 5 min | Check OpenAI status, fallback model |
| **High error rate** | session_errors > 10% of sessions | Investigate provider, check logs |
| **Cost spike** | AI cost > $X/hour | Cap concurrent sessions, check for leaks |
| **Heartbeat silence** | No heartbeat for 60s | Mark session as FAILED, notify user |

## Runbooks

### Session won't start
1. Check `POST /api/v1/sessions` returns 201
2. Check `GET /api/v1/sessions/{id}` returns `state: active`
3. Check WS connection succeeds (101 upgrade)
4. Verify user owns the interview (auth check)

### WebSocket disconnects
1. Check `disconnect_count` in session status
2. If < 3, client-side network issue (grace period active)
3. If > 3, investigate client network stability
4. After 30s grace, session marked as FAILED

### AI not responding
1. Check OpenAI API key is valid
2. Check `AI_INTERVIEWER_MODEL` is accessible
3. Check rate limits (RPM/TPM) on OpenAI account
4. Check `ai_latency_ms` — if high, downgrade model
5. Check `AI_COST_CAP_DOLLARS` — may have been hit

### Prompt not loading
1. Check `packages/prompts/interviewers/{type}.md` exists
2. Check `packages/prompts/evaluators/{type}.md` exists
3. Verify template variables match prompt format strings
4. Check `PROMPTS_ROOT` path resolution

## Recovery Procedures

### Server restart (active sessions lost)
1. All in-memory sessions are LOST on restart
2. Clients reconnect → WS returns SESSION_NOT_FOUND
3. Frontend shows "Session expired — start a new interview"
4. **Mitigation**: Add Redis persistence (Sprint 6)

### Partial outage (some sessions fail)
1. Failed sessions emit `session.failed` event
2. Frontend shows reconnection overlay
3. User can retry or start new interview
4. Failed sessions visible in audit log

### OpenAI outage
1. AI generation returns None → orchestrator detects failure
2. Fallback to static responses ("Let me rephrase...")
3. Session continues with degraded experience
4. Alert fires for ops investigation

## Capacity Planning

| Component | Current Limit | Bottleneck | Scaling Strategy |
|---|---|---|---|
| **In-memory sessions** | ~500 per worker (2GB RAM) | Dict memory + AI calls | Horizontal scaling with Redis |
| **WebSocket connections** | ~1000 per uvicorn worker | Thread pool | Multiple workers + sticky sessions |
| **AI API calls** | Depends on OpenAI rate limit | Token consumption | Round-robin API keys, fallback models |
| **DB writes (events)** | ~50 writes/session | I/O per event | Batch writes, async commit |

## Debugging

### Top commands
```bash
# Check active session count
curl -s http://localhost:8000/api/v1/sessions/status

# Get session details
curl -s http://localhost:8000/api/v1/sessions/{id}

# Tail session events from DB
psql -c "SELECT event_type, payload FROM session_events WHERE session_id='{id}' ORDER BY sequence;"

# Check WebSocket connectivity (manual test)
wscat -c "ws://localhost:8000/api/v1/sessions/{id}/ws" -H "Authorization: Bearer {token}"

# Force session timeout
curl -X POST http://localhost:8000/api/v1/sessions/{id}/end

# Monitor AI latency (from logs)
grep "ai_latency" /var/log/app.log | tail -20
```

### Common error codes

| Code | Meaning | Action |
|---|---|---|
| `SESSION_NOT_FOUND` | Session not in memory | Check session_id, may have expired after restart |
| `FORBIDDEN` | User doesn't own session | Verify auth token matches session.user_id |
| `INVALID_MESSAGE` | WS message failed schema validation | Check message format |
| `RATE_LIMITED` | Too many WS messages | Client should back off |
| `HINT_UNAVAILABLE` | AI couldn't generate hint | Rare — usually a transient AI error |
