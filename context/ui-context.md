# UI Context

> This document defines the visual language, design system, component conventions, interaction patterns, and UX principles for Tayari.ai. It serves as the single source of truth for all user interface decisions. AI coding agents must follow these rules instead of inventing new visual patterns.

---

# Design Philosophy

Tayari.ai follows a **Professional Enterprise SaaS** design language with modern AI product aesthetics.

The interface should feel:

- Professional
- Minimal
- Calm
- Intelligent
- Premium
- Fast
- Trustworthy

The UI should inspire confidence rather than excitement.

The interview experience should always remain the primary focus.

---

# Design Principles

## 1. Content First

The product exists to help users complete interviews.

The interface should never compete with the interview itself.

Visual hierarchy should always prioritize:

1. Primary task
2. Important information
3. Secondary actions
4. Decorative elements

---

## 2. Simplicity Over Decoration

Every UI element should have a purpose.

Avoid unnecessary:

- Colors
- Animations
- Shadows
- Borders
- Icons
- Cards

If removing an element does not reduce usability, it should probably not exist.

---

## 3. Consistency

Every screen should feel like it belongs to the same product.

Spacing, typography, colors, and interactions must remain consistent across all features.

---

## 4. Accessibility

Interfaces should be usable by everyone.

Every implementation should consider:

- Keyboard navigation
- Focus states
- Screen readers
- Color contrast
- Reduced motion preferences

Accessibility is not optional.

---

## 5. Motion Has Meaning

Animations should communicate state changes.

Never animate purely for decoration.

Good uses include:

- Loading
- Navigation
- State transitions
- Expand/collapse
- Modal appearance
- Success feedback

---

# Visual Identity

## Overall Feel

Imagine a combination of:

- OpenAI
- Vercel
- Linear
- Supabase
- Stripe Dashboard
- Clerk

The product should look like a production SaaS platform rather than a portfolio demo.

---

# Color System

## Theme

Dark mode is the primary experience.

Light mode is fully supported.

Never hardcode colors.

Always use semantic design tokens.

---

## Primary

Used for:

- Primary buttons
- Links
- Interactive states
- Focus indicators

Accent color:

Blue / Indigo

---

## Secondary

Used for:

- Highlights
- Secondary actions
- Charts
- Supporting UI

Accent color:

Cyan

---

## Semantic Colors

Use semantic tokens instead of raw colors.

- Primary
- Secondary
- Success
- Warning
- Error
- Info
- Muted
- Border
- Background
- Foreground

Never reference hexadecimal values directly in components.

---

# Typography

Typography should prioritize readability.

## Heading

Large

Bold

Comfortable spacing

---

## Body

Readable

Medium weight

Comfortable line height

Avoid dense paragraphs.

---

## Labels

Small

Uppercase only where appropriate.

---

## Code

Use monospace for:

- Code
- IDs
- Technical information
- API values

---

# Layout System

Use a consistent spacing scale.

Prefer generous whitespace.

Large layouts should breathe.

Avoid dense dashboards.

---

## Containers

Content should remain centered.

Avoid excessive width.

Large dashboards should use responsive layouts.

---

## Grid

Use responsive grids.

Prefer:

- 1 column on mobile
- 2 columns on tablet
- 3–4 columns on desktop

Only increase complexity when necessary.

---

# Component Library

Primary UI library:

- shadcn/ui

Icons:

- Lucide React

Avoid mixing component libraries unless there is a compelling reason.

---

# Component Principles

## Buttons

One primary action per screen.

Secondary actions should never visually compete with the primary action.

Destructive actions should always require confirmation.

---

## Cards

Cards should group related content.

Avoid deeply nested cards.

Use spacing instead of borders where possible.

---

## Forms

Use:

- React Hook Form
- Zod validation

Validation should appear inline.

Errors should clearly explain how to resolve the issue.

---

## Tables

Tables should support:

- Sorting
- Pagination
- Empty states
- Loading states

Avoid horizontal scrolling where possible.

---

## Dialogs

Dialogs should only interrupt when necessary.

Prefer drawers or inline editing for simple interactions.

---

## Empty States

Every empty state should help the user understand what to do next.

Example:

Instead of:

"No interviews."

Use:

"You haven't completed an interview yet. Start your first interview to receive personalized feedback."

---

## Loading States

Never show blank screens.

Prefer:

- Skeleton loaders
- Progressive loading
- Optimistic updates when appropriate

---

## Error States

Errors should:

- Explain the problem
- Suggest a solution
- Never expose internal implementation details

---

# Navigation

Navigation should remain predictable.

The user should always know:

- Where they are
- What they can do
- How to return

Primary navigation should remain stable across the application.

---

# Dashboard Design

Dashboards should answer three questions immediately:

1. How am I performing?
2. What should I do next?
3. What has changed?

Analytics should be easy to scan.

Avoid visual clutter.

---

# Interview Experience

The interview room is the most important interface in the product.

The interview experience should feel closer to:

- Google Meet
- Zoom
- VS Code
- Cursor

than:

- Messaging applications
- Chatbots
- Social platforms

The user's attention should remain on the conversation and coding environment.

---

## Behavioral Interviews

Primary focus:

Conversation.

Transcript.

Current question.

Microphone controls.

Timer.

---

## Coding Interviews

Primary focus:

Monaco Editor.

Problem statement.

Console output.

Execution controls.

AI conversation should remain secondary.

---

## System Design Interviews

Primary focus:

Whiteboard.

Drawing tools.

Diagram space.

Conversation should support—not replace—the whiteboard.

---

# Reports & Analytics

Reports should feel analytical rather than gamified.

Prioritize:

- Evidence
- Skill breakdown
- Timeline
- Strengths
- Weaknesses
- Recommendations

Charts should support—not replace—the written analysis.

---

# AI Presentation

Treat the AI interviewer as another participant in the interview.

Avoid:

- Robot illustrations
- Cartoon AI
- Excessive AI branding

The AI should feel professional and conversational.

---

# Motion Guidelines

Animations should be subtle.

Preferred animations:

- Fade
- Opacity
- Slide
- Scale (minimal)
- Blur transitions

Avoid:

- Bounce
- Spin
- Elastic effects
- Long transitions

Animation duration should generally remain under 300ms.

---

# Responsive Design

Every page must support:

- Mobile
- Tablet
- Desktop

Responsive behavior should be designed—not patched.

Avoid hiding critical functionality on smaller screens.

---

# Theme Support

Support:

- Light mode
- Dark mode
- System preference

Never assume one theme.

Both themes must feel equally polished.

---

# Icons

Use only:

- Lucide React

Icons should communicate meaning, not decoration.

Avoid excessive icon usage.

---

# Future Design Direction

As Tayari.ai grows, the design system should remain:

- Modular
- Token-based
- Component-driven
- Accessible
- Scalable

New features should extend the existing design language rather than introducing new visual patterns.

---

# UI Invariants

The following rules must never be violated:

- Never hardcode colors.
- Never hardcode spacing values outside the design system.
- Never mix multiple component libraries unnecessarily.
- Never introduce inconsistent typography.
- Never create duplicate component patterns.
- Never sacrifice accessibility for aesthetics.
- Never add animations without purpose.
- Never make the interface compete with the interview experience.
- Every screen must have a clear primary action.
- Every interactive element must have visible focus states.
- Every empty state should guide the user toward the next action.
- Every loading state should communicate progress.
- Every error state should help users recover.

These rules define the visual identity of Tayari.ai and must be followed consistently across the entire application.