# Dashboard Module

Feature-first dashboard module with summary stats, recent activity, subscription info, and interview progress tracking.

## Architecture

```
features/dashboard/
├── api/dashboard.ts         # API client (getDashboard, getRecentInterviews, getAnalytics)
├── hooks/use-dashboard.ts   # TanStack Query hooks (useDashboard, useRecentInterviews, useAnalytics)
├── types/index.ts           # TypeScript interfaces (DashboardData, DashboardStats, RecentInterview, etc.)
├── components/
│   ├── DashboardHome.tsx       # Page-level orchestrator — wires hooks to child components
│   ├── StatsGrid.tsx           # 4-card stat grid (total, completed, streak, avg score)
│   ├── RecentActivityList.tsx  # Scrollable list of recent interviews
│   ├── QuickActions.tsx        # "New Interview", "View Reports", "Practice", "Set Goal" buttons
│   ├── WelcomeCard.tsx         # Animated greeting card with streak tip
│   ├── SubscriptionStatus.tsx  # Current plan + renew date + CTA
│   └── InterviewProgress.tsx   # Progress bar + latest eval score
├── __tests__/                 # Unit tests (migrate to features/dashboard/__tests__/)
└── README.md
```

## Component API

| Component | Props | Notes |
|-----------|-------|-------|
| `DashboardHome` | — | Orchestrator; surfaces query errors with retry button |
| `StatsGrid` | `stats?: DashboardStats`, `isLoading: boolean` | 4 responsive stat cards; null-safe |
| `RecentActivityList` | `interviews?: RecentInterview[]`, `isLoading: boolean` | Memoized list items; empty/loading/error states |
| `QuickActions` | — | Static 2x2 grid of action buttons |
| `WelcomeCard` | `displayName?: string`, `isLoading: boolean`, `streak?: number` | Animated gradient card; time-based greeting |
| `SubscriptionStatus` | `subscription?: SubscriptionInfo \| null`, `isLoading: boolean` | Free/pro/enterprise with "Upgrade" or "Manage" CTA |
| `InterviewProgress` | `latestReport?: LatestReport \| null`, `completed: number`, `total: number`, `isLoading: boolean` | Progress bar + latest evaluation score |

## Hooks

All hooks use TanStack Query with global `retry: 1`:

```ts
useDashboard()        → { data: DashboardData, isLoading, error, refetch }  (staleTime: 30s)
useRecentInterviews() → { data: { interviews: RecentInterview[] }, ... }     (staleTime: 15s)
useAnalytics()        → { data: AnalyticsData, ... }                         (staleTime: 60s)
```

## Error Handling

- `DashboardHome` checks `error` from both hooks and renders a centered error state with "Try again" button.
- React Query global `onError` logs to console (swap with Sentry/DataDog in production).
- Route-level `error.tsx` catches render exceptions.
- `ErrorBoundary` in layout catches unhandled errors at the layout level.

## Loading States

- Each component renders `Skeleton` placeholders matching the card layout.
- Route-level `loading.tsx` provides a full-page skeleton shell.
- `DashboardHome` passes `isLoading` to children for granular control.

## Accessibility

- Skip-to-content link at top of dashboard layout.
- `Sheet` panel uses `useFocusTrap` to trap Tab/Shift+Tab within the drawer.
- `DropdownMenu` auto-focuses the first menuitem on open.
- All interactive elements have `aria-*` attributes.
- Color-coded scores (green/amber/red) include text descriptors.
