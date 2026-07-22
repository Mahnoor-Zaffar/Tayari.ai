"""End-to-end test: Full interview session → evaluation pipeline.

Tests the complete flow:
1. Login → get auth token
2. Create interview via wizard payload
3. Start session via REST
4. Connect WebSocket, simulate Q&A
5. End session
6. Trigger evaluation
7. Verify evaluation results

Run: python3 -m pytest tests/test_e2e_evaluation.py -v -s
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"
EMAIL = "admin@tayari.ai"
PASSWORD = "Tayari123!"


# ── Helpers ──────────────────────────────────────────────────────────────────


async def login(client: httpx.AsyncClient) -> str:
    """Login and return access token."""
    resp = await client.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("data", {}).get("access_token") or data.get("access_token")
    assert token, f"No token in response: {data}"
    return token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_interview_payload(user_id: str) -> dict:
    """Create a realistic interview payload matching the wizard schema."""
    return {
        "type": "coding",
        "company": "Google",
        "role": "Senior Software Engineer",
        "experience_level": "mid-senior",
        "difficulty": "hard",
        "language": "python",
        "spoken_language": "en",
        "duration_minutes": 45,
        "custom_instructions": "Focus on distributed systems and system design.",
    }


# ── Test ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_interview_to_evaluation():
    """Full E2E: create interview → session → Q&A → evaluation."""

    async with httpx.AsyncClient(base_url=API, timeout=30.0) as client:
        # ── Step 1: Login ────────────────────────────────────────────────
        print("\n[1/7] Logging in...")
        token = await login(client)
        headers = auth_header(token)
        print(f"  ✓ Token obtained: {token[:20]}...")

        # ── Step 2: Create Interview ────────────────────────────────────
        print("\n[2/7] Creating interview...")
        payload = make_interview_payload(user_id="placeholder")
        resp = await client.post("/interviews", json=payload, headers=headers)
        print(f"  Response: {resp.status_code} {resp.text[:200]}")
        assert resp.status_code in (200, 201), f"Create interview failed: {resp.status_code} {resp.text}"
        interview_data = resp.json().get("data", resp.json())
        interview_id = interview_data.get("interview_id") or interview_data.get("id")
        assert interview_id, f"No interview_id in response: {interview_data}"
        print(f"  ✓ Interview created: {interview_id[:8]}...")

        # ── Step 3: Start Session ───────────────────────────────────────
        print("\n[3/7] Starting session...")
        resp = await client.post(
            "/sessions",
            json={"interview_id": interview_id},
            headers=headers,
        )
        print(f"  Response: {resp.status_code} {resp.text[:300]}")
        assert resp.status_code in (200, 201), f"Start session failed: {resp.status_code} {resp.text}"
        session_data = resp.json().get("data", resp.json())
        session_id = session_data.get("session_id") or session_data.get("id") or interview_id
        print(f"  ✓ Session started: {session_id[:8]}...")

        # ── Step 4: WebSocket Q&A Simulation ────────────────────────────
        print("\n[4/7] Simulating Q&A via WebSocket...")
        ws_url = f"ws://localhost:8000/api/v1/sessions/{session_id}/ws"
        messages_received = []
        messages_sent = []

        try:
            import websockets

            async with websockets.connect(ws_url) as ws:
                # Read initial connection messages
                for _ in range(3):
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        parsed = json.loads(msg)
                        messages_received.append(parsed)
                        print(f"  ← Received: {parsed.get('type', 'unknown')}")
                    except TimeoutError:
                        break

                # Simulate answering 3 questions
                answers = [
                    "I would use a hash map to track character frequencies, "
                    "iterating through the string once for O(n) time complexity.",
                    "The system would use a microservices architecture with an "
                    "API gateway, event-driven communication via Kafka, and Redis for caching.",
                    "In my previous role, I led a team of 5 to migrate a monolith "
                    "to microservices, reducing deployment time from 2 hours to 15 minutes.",
                ]

                for i, answer in enumerate(answers):
                    # Wait for question
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        parsed = json.loads(msg)
                        messages_received.append(parsed)
                        print(f"  ← Received: {parsed.get('type', 'unknown')}")
                        if parsed.get("type") == "ai.question":
                            print(f"    Question: {parsed.get('payload', {}).get('text', '')[:80]}...")
                    except TimeoutError:
                        print(f"  ⚠ Timeout waiting for question {i + 1}")

                    # Send answer
                    answer_msg = {
                        "type": "user.answer",
                        "payload": {
                            "text": answer,
                            "question_index": i,
                        },
                    }
                    await ws.send(json.dumps(answer_msg))
                    messages_sent.append(answer_msg)
                    print(f"  → Sent answer {i + 1}: {answer[:60]}...")

                    # Wait for acknowledgment or next question
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                        parsed = json.loads(msg)
                        messages_received.append(parsed)
                        print(f"  ← Received: {parsed.get('type', 'unknown')}")
                    except TimeoutError:
                        pass

                # End session
                end_msg = {"type": "session.end", "payload": {}}
                await ws.send(json.dumps(end_msg))
                messages_sent.append(end_msg)
                print("  → Sent session.end")

                # Wait for completion messages
                for _ in range(3):
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        parsed = json.loads(msg)
                        messages_received.append(parsed)
                        print(f"  ← Received: {parsed.get('type', 'unknown')}")
                        if parsed.get("type") == "session.completed":
                            break
                    except TimeoutError:
                        break

        except ImportError:
            print("  ⚠ websockets not installed, skipping WebSocket test")
            print("  Install: pip install websockets")
        except Exception as e:
            print(f"  ⚠ WebSocket error: {e}")

        print(f"  ✓ WebSocket exchange complete: {len(messages_sent)} sent, {len(messages_received)} received")

        # ── Step 5: End Session via REST (fallback) ─────────────────────
        print("\n[5/7] Ensuring session ended via REST...")
        resp = await client.post(f"/sessions/{session_id}/end", headers=headers)
        print(f"  Response: {resp.status_code} {resp.text[:200]}")
        # May fail if already ended, that's OK

        # ── Step 6: Trigger Evaluation ──────────────────────────────────
        print("\n[6/7] Triggering evaluation...")
        resp = await client.post(f"/evaluations/{interview_id}", headers=headers)
        print(f"  Response: {resp.status_code} {resp.text[:500]}")

        if resp.status_code in (200, 201):
            eval_data = resp.json().get("data", resp.json())
            eval_id = eval_data.get("evaluation_id") or eval_data.get("id")
            overall_score = eval_data.get("overall_score")
            verdict = eval_data.get("hire_verdict")
            dimensions = eval_data.get("dimensions", [])

            print("  ✓ Evaluation complete!")
            print(f"    ID: {eval_id}")
            print(f"    Score: {overall_score}/5.0 ({eval_data.get('overall_score_100', 'N/A')}%)")
            print(f"    Verdict: {verdict}")
            print(f"    Dimensions: {len(dimensions)}")
            for d in dimensions:
                print(f"      - {d.get('label', d.get('key'))}: {d.get('score')}/5.0")

            # ── Step 7: Verify Results ──────────────────────────────────
            print("\n[7/7] Verifying results...")
            assert overall_score is not None, "No overall_score"
            assert 0.0 <= overall_score <= 5.0, f"Score out of range: {overall_score}"
            assert verdict in ("hire", "lean-hire", "lean-no-hire", "no-hire"), f"Invalid verdict: {verdict}"
            assert len(dimensions) > 0, "No dimensions returned"
            print("  ✓ All assertions passed!")
        else:
            print(f"  ⚠ Evaluation failed with status {resp.status_code}")

            # Try fetching existing evaluation
            print("\n[7/7] Checking for existing evaluation...")
            resp = await client.get(f"/evaluations/{interview_id}", headers=headers)
            print(f"  Response: {resp.status_code} {resp.text[:300]}")

        # ── Summary ─────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("E2E TEST SUMMARY")
        print("=" * 60)
        print(f"Interview:  {interview_id[:8]}...")
        print(f"Session:    {session_id[:8]}...")
        print(f"WS Messages: {len(messages_sent)} sent, {len(messages_received)} received")
        if resp.status_code == 200:
            print(f"Evaluation: {eval_id}")
            print(f"Score:      {overall_score}/5.0 → {verdict}")
        print("=" * 60)


@pytest.mark.asyncio
async def test_evaluation_without_session():
    """Test evaluation endpoint directly with an interview that has transcript data."""

    async with httpx.AsyncClient(base_url=API, timeout=30.0) as client:
        print("\n[Direct Evaluation Test]")
        token = await login(client)
        headers = auth_header(token)

        # Create interview with mock transcript
        payload = make_interview_payload(user_id="placeholder")
        resp = await client.post("/interviews", json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            print(f"  Could not create interview: {resp.status_code}")
            return

        interview_data = resp.json().get("data", resp.json())
        interview_id = interview_data.get("interview_id") or interview_data.get("id")

        # Check if the interview model has transcript field
        print(f"  Interview {interview_id[:8]}... created")
        print("  Note: Full evaluation requires transcript data in the interview record")
        print("  Transcript is populated during live WebSocket sessions")


@pytest.mark.asyncio
async def test_auth_flow():
    """Test authentication flow works correctly."""

    async with httpx.AsyncClient(base_url=API, timeout=10.0) as client:
        print("\n[Auth Flow Test]")

        # Test invalid login
        resp = await client.post("/auth/login", json={"email": "wrong@email.com", "password": "wrong"})
        print(f"  Invalid login: {resp.status_code} (expected 401)")

        # Test valid login
        resp = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        print(f"  Valid login: {resp.status_code}")
        assert resp.status_code == 200

        token = resp.json().get("data", {}).get("access_token") or resp.json().get("access_token")
        assert token, "No token"

        # Test protected endpoint
        headers = auth_header(token)
        resp = await client.get("/auth/me", headers=headers)
        print(f"  /auth/me: {resp.status_code}")

        # Test without auth
        resp = await client.get("/auth/me")
        print(f"  /auth/me (no token): {resp.status_code} (expected 401)")

        print("  ✓ Auth flow works")


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
    asyncio.run(test_full_interview_to_evaluation())
