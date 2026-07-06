```
# Product Requirements Document (PRD)
**Project Name:** AI-Powered Interactive Interview Simulator  
**Document Version:** 1.0  
**Phase:** High-Level Architecture & Core Requirements  

---

## 1. Executive Summary
The product is an interactive, conversational AI interview simulation platform designed to prepare candidates for rigorous technical and behavioral interviews. Unlike static question banks or simple chatbots, this system leverages full-duplex voice interactions, retrieval-augmented generation (RAG) based on candidate resumes, and a multi-agent AI architecture to dynamically adjust interview difficulty and pathing. 

## 2. Target Audience & Use Cases
*   **Primary Persona:** Full-stack engineers, AI developers, and technical professionals preparing for rigorous technical loops.
*   **Core Use Case:** A user uploads their resume, selects a target role (e.g., Senior LLMOps Engineer), and engages in a turn-based, voice-driven mock interview. The system evaluates their responses in real-time for technical accuracy, communication clarity, and structural formatting (e.g., STAR method).

## 3. High-Level Architecture & Tech Stack

### Frontend / Presentation Layer
*   **Framework:** Next.js (App Router)
*   **Styling:** Tailwind CSS 
*   **Audio Interface:** Native Web Audio API and MediaRecorder API for low-latency chunked audio capture.
*   **State Management:** React Context / Zustand for managing conversational states and stream buffering.

### Backend Orchestration & Data Layer
*   **Core Database:** Supabase (PostgreSQL)
*   **Vector Storage:** pgvector extension for embedding resume chunks and job descriptions.
*   **API Runtime:** Next.js Serverless Edge functions / Node.js route handlers.
*   **Post-Processing & Automation:** Webhooks triggering robust background data pipelines managed via n8n and Make to handle asynchronous report generation and automated user follow-ups.

### AI & Speech Infrastructure
*   **Speech-to-Text (STT):** Deepgram (Nova-2) for sub-300ms, highly accurate transcription that captures natural stutters and filler words.
*   **Interviewer Persona Engine:** Groq (Llama-3 70B) or OpenAI (GPT-4o-mini) prioritized for ultra-low Time-to-First-Token (TTFT) to maintain natural conversational cadence.
*   **Evaluator & RAG Engine:** OpenAI (GPT-4o) / text-embedding-3-small for semantic matching, technical critique generation, and structured JSON output.

---

## 4. Core Features & Functional Requirements

### 4.1. Candidate Onboarding & Profile Initialization
*   **Resume Parsing:** Users upload existing profiles (PDF/Markdown). The system chunks and embeds these documents into the Supabase vector store.
*   **Simulation Configuration:** Users configure the simulation by selecting target role, technical difficulty (Junior to Staff), and interview stage (Initial Screen, Technical Deep-Dive, Behavioral).

### 4.2. Conversational Voice Engine
*   **Turn-Based Audio Loop:** System records user audio, transcribes it via Deepgram, and passes the transcript to the backend.
*   **Dynamic Context Grounding:** Every user response triggers a semantic search against their stored resume embeddings to allow the interviewer AI to ask highly specific, personalized follow-up questions.
*   **Strict Persona Constraints:** The AI must utilize specific system prompts that forbid standard LLM pleasantries, enforcing a realistic, challenging, and professional interviewer tone.

### 4.3. Multi-Agent Evaluation System
*   **Foreground Agent (The Interviewer):** Generates the immediate conversational response and next question. Streams text back to the client UI.
*   **Background Agent (The Shadow Evaluator):** Operates asynchronously via background queues. Analyzes the candidate's last answer to score technical depth, detect filler words, and verify structural coherence (STAR framework).

### 4.4. Post-Interview Analytics Dashboard
*   **Session Scorecard:** An interactive UI breaking down the interview timeline.
*   **Metrics Tracked:**
    *   Overall technical and communication scores (1-10).
    *   Filler word frequency analysis.
    *   Sentence-by-sentence constructive critique.
    *   Actionable rewrite suggestions for weak answers.

---

## 5. Data Model Architecture

The relational schema must enforce a clear hierarchy between the session, the conversation turns, and the background evaluations.

1.  **`interview_sessions`**: Tracks global state (`target_role`, `difficulty`, `current_stage`, `resume_context`).
2.  **`interview_turns`**: Chronological ledger of the exact Q&A transcript (`interviewer_question`, `candidate_response`).
3.  **`turn_evaluations`**: Stores the granular JSON payload from the shadow evaluator (`technical_score`, `star_framework_check`, `constructive_critique`).
4.  **`resume_embeddings`**: Stores the chunked vector arrays of the candidate's professional history.

---

## 6. Non-Functional Requirements & Best Practices

*   **Latency Budget:** The end-to-end delay between the user finishing speaking and the AI starting its audio/text response must strictly remain under 1500ms.
*   **LLMOps & Prompt Versioning:** Core persona instructions must be version-controlled separately from application logic to allow rapid iteration on the AI's behavior.
*   **Data Privacy:** All temporary audio buffers must be flushed from memory immediately after transcription.
*   **Resiliency:** If the background evaluation worker queue fails or lags, it must not block the foreground conversational loop.

---

## 7. Implementation Phasing

*   **Phase 1: Foundation & Data Layer:** Setup Supabase, provision pgvector, and establish the user session schema.
*   **Phase 2: Voice & STT Integration:** Implement the browser audio capture and Deepgram transcription pipeline.
*   **Phase 3: RAG & Inference Loop:** Build the embedding extraction and the foreground interviewer prompt logic.
*   **Phase 4: Shadow Evaluator Engine:** Deploy the background worker processes and complex JSON-structured evaluation prompts.
*   **Phase 5: Presentation & Dashboards:** Finalize the Tailwind UI, post-interview scorecards, and data visualization elements.
```

