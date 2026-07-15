"""Judge Engine — dedicated internal module for code execution and validation.

This module is **completely separate** from the Interview Runtime.
It has no knowledge of sessions, interviews, or WebSocket connections.

Responsibilities:
    - Language Registry (supported languages, runners, Docker images)
    - Sandbox Manager (Docker/subprocess isolation with resource limits)
    - Execution Queue (async job processing for submissions)
    - Result Processor (test case judging, scoring, formatting)
    - Metrics Collector (execution timing, pass rates, error counters)

Ownership:
    Judge Engine → Language Registry → Sandbox Manager → Docker
                         ↓
                   Result Processor → Metrics Collector

The Judge Engine is consumed by ``features/code/service.py`` which
adds persistence and API integration on top.
"""
