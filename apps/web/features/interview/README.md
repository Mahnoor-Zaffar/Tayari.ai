# Interview Setup Feature

Multi-step wizard for configuring AI-powered mock interviews. Frontend lives in `apps/web/features/interview/`, backend in `apps/api/features/interview/`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Route: /dashboard/interview/new                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  FeatureFlag("interviews")                             │ │
│  │  ┌───────────────────────────────────────────────────┐ │ │
│  │  │  InterviewSetupHome (memo, ErrorBoundary)        │ │ │
│  │  │  ┌─────────────────────────────────────────────┐  │ │ │
│  │  │  │  InterviewSetupWizard (FormProvider)        │  │ │ │
│  │  │  │                                             │  │ │ │
│  │  │  │  StepIndicator ← StepTransition             │  │ │ │
│  │  │  │                                             │  │ │ │
│  │  │  │  Step 0: InterviewTypeStep (static)         │  │ │ │
│  │  │  │  Step 1: PreferencesStep   (static)         │  │ │ │
│  │  │  │  Step 2: UploadsStep      (dynamic, ssr:false)│ │ │ │
│  │  │  │  Step 3: DeviceCheckStep (dynamic, ssr:false)│ │ │ │
│  │  │  │  Step 4: ReviewStep       (static)         │  │ │ │
│  │  │  └─────────────────────────────────────────────┘  │ │ │
│  │  └───────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User → React Hook Form (Zod resolver) → validateStep() → API payload
                                         ↓
                          useWatch (5 fields for canGoNext reactivity)
                                         ↓
                          Subscription (all fields, no re-renders) → saveDraft()
```

### AI Layer Integration

The `InterviewConfiguration` type in `lib/config-builder.ts` is the normalized contract between the setup wizard and the AI interview engine. Build it from:

- Form values: `buildInterviewConfiguration(values)` — before starting the interview
- API response: `buildInterviewConfigurationFromResponse(response)` — when resuming

```ts
interface InterviewConfiguration {
  interview_type: "coding" | "system-design" | "behavioral"
  company: string
  role: string
  seniority: "junior" | "mid-senior" | "staff-lead"
  language: "python" | "java" | "cpp" | "javascript" | "csharp" | null
  framework: "react" | "vue" | "angular" | "svelte" | "django" | "fastapi" | "spring" | "express" | "next" | null
  duration_minutes: 15 | 30 | 45
  difficulty: "easy" | "medium" | "hard"
  resume_reference: string | null
  job_description_reference: string | null
  template_reference: string | null
  custom_prompt: string | null
  device_status: DeviceStatus
}
```

## Directory Structure

```
features/interview/
├── api/
│   └── interview-setup.ts        # API client wrappers
├── components/
│   ├── InterviewSetupHome.tsx    # Page orchestrator (memo, ErrorBoundary)
│   ├── InterviewSetupWizard.tsx  # Wizard shell (FormProvider, navigation, autosave)
│   ├── StepIndicator.tsx         # Progress indicator (5 steps)
│   ├── StepTransition.tsx        # Framer Motion slide transition
│   └── steps/
│       ├── InterviewTypeStep.tsx # Step 0: type, company, role, experience
│       ├── PreferencesStep.tsx   # Step 1: language, framework, difficulty, duration
│       ├── UploadsStep.tsx       # Step 2: resume, JD, custom instructions (lazy)
│       ├── DeviceCheckStep.tsx   # Step 3: mic, camera, speaker, browser (lazy)
│       └── ReviewStep.tsx        # Step 4: review + submit
├── hooks/
│   └── use-interview-setup.ts    # TanStack Query hooks (6 hooks)
├── lib/
│   ├── wizard-schema.ts          # Zod schema, draft storage, step validation
│   └── config-builder.ts         # InterviewConfiguration type + builder (AI layer)
└── types/
    └── index.ts                  # TS interfaces for API responses
```

## Key Design Decisions

### Performance

- **Lazy-loaded heavy steps**: `UploadsStep` (react-dropzone ~20KB) and `DeviceCheckStep` (browser APIs) use `next/dynamic` with `ssr: false`, loading only when the user reaches steps 2-3. Page size dropped from 30KB → 13KB.
- **Subscription-based autosave**: Uses `methods.watch(callback)` instead of `methods.watch()` to avoid re-renders on every keystroke. Debounced at 1500ms.
- **Targeted `useWatch`**: Only 5 validation-relevant fields are watched for `canGoNext` reactivity, not the entire form.
- **`mode: "onTouched"`**: Validates on blur first, then on change — prevents validation on every keystroke.
- **Memoized ReviewStep**: `labelFor` and `reviewSections` use `useMemo`/`useCallback`.

### Security

- **Magic number validation**: Reads first 4 bytes to verify file content matches its extension (PDF: `%PDF`, DOCX: `PK`).
- **Filename sanitization**: Strips path separators and control characters before API call.
- **Text sanitization**: Removes null bytes from JD text before upload.
- **Draft TTL**: Drafts expire after 24 hours and are auto-cleaned on load.
- **Client-side size enforcement**: Files >5MB rejected before hashing.

### Accessibility

- **Dropzone keyboard support**: Enter/Space triggers file picker on focused dropzone.
- **ARIA roles**: `radiogroup` for type/difficulty/duration selections, `progressbar` for step indicator, `alert` for errors.
- **Screen reader labels**: `sr-only` legends on fieldsets, descriptive `aria-label` on interactive buttons.
- **Keyboard navigation**: ArrowLeft/Right for step navigation.

### Error Handling

- **Options load failure**: Inline error with retry button when API options fail to load.
- **Submit failure**: Error message with retry button.
- **Upload failure**: Per-file error with retry/remove actions.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/interviews/options` | Fetch available companies, roles, languages, frameworks, etc. |
| POST | `/interviews` | Create a new interview session |
| POST | `/interviews/upload-resume` | Upload a resume by hash (dedup on backend) |
| POST | `/interviews/upload-job-description` | Upload JD by text or file hash |
| POST | `/interviews/device-check` | Record device check results |
| GET | `/interviews` | List interviews for current user |
| GET | `/interviews/:id` | Get a specific interview |

## Testing

```bash
cd apps/web && pnpm test                    # All frontend tests
cd apps/web && pnpm test -- --reporter=verbose  # Verbose output
cd apps/api && pytest features/interview/   # Backend tests
```

Test coverage:
- `wizard-schema.test.ts` — 19 tests (schema validation, step validation, draft storage with TTL)
- `config-builder.test.ts` — 11 tests (configuration builder, option label resolution)
- `InterviewTypeStep.test.tsx` — 6 tests (rendering, options, fallbacks, loading)
- `PreferencesStep.test.tsx` — 5 tests (rendering, language requirements)
- `ReviewStep.test.tsx` — 6 tests (sections, label resolution, submit, edit)

## Feature Flag

The interview feature is behind the `interviews` feature flag (`NEXT_PUBLIC_FF_INTERVIEWS`). Defaults to `false`. Enable in `.env.local`:

```env
NEXT_PUBLIC_FF_INTERVIEWS=true
```