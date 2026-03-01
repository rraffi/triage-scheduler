# Phase 4 — Schedule Dashboard

## Scope

The read-only published view of the schedule. This is the primary interface team
members use to check who is on triage this week and what's coming up.

## Depends On

Phase 2 (Scheduling Engine).

## Views

### Current Week
- Prominent display of this week's assignments: who is on which app.
- Highlight if any assignment is a substitute (vacation fill-in).
- Show the assignee's contact info for easy reach.

### Upcoming Schedule
- Preview of the next 2-4 weeks (generated or projected).
- Indicate known vacations that will affect upcoming assignments.
- Projected assignments shown as tentative (may change if availability changes).

### Schedule History
- Paginated list of past weeks with assignments.
- Filter by member or app.
- Link to decision log (Phase 6) for each week.

### Fairness Summary
- Per-member breakdown: total assignments, per-app counts.
- Time range selector (last N weeks, last cycle, all time).
- Visual indicator if distribution is skewed beyond threshold.

## Data Flow

```
ScheduleState + Assignments (DB)
        │
        ▼
   Dashboard API
        │
        ▼
   Web Dashboard (read-only)
```

## Acceptance Criteria

1. Current week's assignments are visible within 1 page load (no navigation).
2. Upcoming schedule updates automatically when the engine runs.
3. History is searchable by member name and app name.
4. Fairness summary shows correct counts matching actual assignment records.

## Out of Scope

- Editing assignments (that's Phase 3 admin override).
- Notification delivery (Phase 5).
- Detailed decision logs (Phase 6, linked from here).
