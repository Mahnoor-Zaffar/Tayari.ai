# Tayari.ai UX Lifecycle Blueprint

## 1. Global Frontend Architecture State Machine
The client dashboard manages UI states utilizing standard React Context or a lightweight Zustand configuration hook.

+-----------+    Toggle Mic Click     +-----------+     Form Payload Stream     +------------+
|   IDLE    | ----------------------> | RECORDING | ------------------------> | PROCESSING |
+-----------+                         +-----------+                           +------------+
^                                                                             |
|                                                                             | SSE Tokens Emit
|                                  +-----------+                              |
+--------------------------------- | STREAMING | <----------------------------+
Stream Finalized         +-----------+


## 2. Primary UI View Sub-division Layouts

### Dashboard Workspace Panel (`/app/interview/[id]/page.tsx`)
- **Left Side Configuration Monitor:** Displays current target metadata card (`Senior Full-Stack Engineer`), a visible tracking step indicator representing interview phase progression (`Technical Case Round`), and an emergency "End Simulation" fallback exit toggle.
- **Center Focus Waveform Visualizer:** Displays dynamic CSS mic-amplitude waveforms when active. Includes an interactive tap-to-talk microphone trigger button.
- **Streaming Context Panel:** Displays a high-contrast terminal style streaming box. Displays `interviewer_question` character-by-character as tokens flash onto the screen.

### Analytics Review Metrics Dashboard (`/app/interview/[id]/report/page.tsx`)
- **Global Overview Scorecard Grid:** Displays macro data tracking cards containing average aggregated scores (e.g., `Technical Index: 7.8/10`, `STAR Layout Adherence: 82%`).
- **Interactive Chronological Transcript Feed:** A split-list layout row displaying each individual historical Q&A exchange. Clicking an individual turn element opens up an expander block displaying the background `constructive_critique` text string and the count list of flag-marked local filler words.