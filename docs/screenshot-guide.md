# Screenshot Guide

Replace the placeholder SVGs in `assets/screenshots/` with real PNG screenshots following the specifications below.

## Style Guidelines

- **Dimensions**: 1200×675px (16:9 aspect ratio)
- **Format**: PNG
- **Browser**: Chrome or Firefox, clean incognito window
- **Resolution**: Capture at 1440×900 viewport, scale to 1200×675
- **Background**: Use the app's dark theme consistently
- **No cursor**: Hide the mouse cursor unless demonstrating a click interaction
- **No browser chrome**: Crop browser UI (use browser dev tools or extensions)
- **Consistent state**: Use the same demo user, same interview data across all screenshots

---

## Screenshot Checklist

### 1. `hero.png` — Landing Page

**What to capture**: The full landing page (`/` route)

- Hero section with headline and tagline
- CTA buttons (Sign In / Get Started)
- Feature highlights or illustration
- Clean, uncluttered view — no scrolling

### 2. `dashboard.png` — Dashboard Home

**What to capture**: `/dashboard` after login

- Welcome card with greeting and streak
- Stats grid (Total Interviews, Completed, Current Streak, Average Score)
- Quick Actions row (New Interview, View Reports, Practice, Set Goal)
- Recent Activity section with at least 2-3 interview entries
- Subscription Status widget in the sidebar or right column
- Interview Progress card with progress bar and latest evaluation score

### 3. `interview-setup.png` — Setup Wizard

**What to capture**: `/dashboard/interview/new` — the wizard form

- Step indicator showing current step (e.g., Step 2 of 4)
- A visible form step with populated fields:
  - Interview type selector (Coding / System Design / Behavioral)
  - Company dropdown or input
  - Role selection
  - Experience level
  - Language / Framework (for coding type)
  - Difficulty and duration options
- Clean form layout, no validation errors visible

### 4. `live-interview.png` — Interview Session (Behavioral/System Design)

**What to capture**: `/dashboard/interview/[id]` during an active session

- Conversation area with AI question and user answer bubbles
- Session timer showing remaining time
- Connection status indicator (green = connected)
- Voice controls (mic toggle, mute button)
- Progress indicator showing question count
- Pause/End buttons visible

### 5. `coding-interview.png` — Coding Interview Session

**What to capture**: `/dashboard/interview/[id]/coding` during an active session

- Split layout: problem description on left, Monaco editor on right
- AI question/chat panel below the problem description
- Code editor with syntax-highlighted code visible
- Language selector
- Test results panel (if tests have run)
- Timer and session controls in the top bar

### 6. `evaluation-report.png` — Post-Interview Evaluation

**What to capture**: `/dashboard/interview/[id]/evaluation` after completion

- Overall score prominently displayed
- Hire verdict badge (e.g., "Hire", "Lean Hire")
- Radar chart or bar chart showing dimension scores
- Strengths section with bullet points
- Areas for improvement section
- Transcript viewer or summary
- Score breakdown per question (if available)

### 7. `analytics.png` — Analytics / Reports Dashboard

**What to capture**: `/dashboard/reports`

- Filters or date range selector
- Performance trend chart(s)
- Aggregated statistics (average score, interviews completed, etc.)
- Score distribution or comparison data
- List of recent evaluations with scores

### 8. `architecture.png` — Architecture Diagram

**What to capture**: Not a UI screenshot — this should be a clean architecture diagram

- Create a diagram using tools like Excalidraw, Diagrams.net, or Figma
- Show: Browser → Next.js → FastAPI → PostgreSQL + Redis + AI Provider
- Include WebSocket connection for real-time interviews
- Show background evaluation worker flow
- Export at 1200×675px matching the other screenshots

---

## Upload Process

1. Capture/render each image at 1200×675px
2. Save as PNG with the filename specified above
3. Replace the SVG placeholder in `assets/screenshots/`
4. Verify the README renders the images correctly
5. Optimize PNGs (tinyPNG or similar) to keep repo size manageable
