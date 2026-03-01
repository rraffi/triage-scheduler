# Phase 2 — Scheduling Engine

## Scope

The scheduling algorithm as a service. Takes the current `ScheduleState` and member
availability, produces assignments for the next week. This is a pure-logic layer
with no UI or notification concerns.

## Depends On

Phase 1 (Data Model & Persistence).

## Inputs

| Input | Source |
|-------|--------|
| `ScheduleState` | Database (Phase 1) |
| Active members + rotation order | Member table |
| Availability for target week | Availability table |
| App list + sort order | App table |

## Outputs

| Output | Destination |
|--------|-------------|
| List of `Assignment` records (one per app) | Assignment table |
| Updated `ScheduleState` | ScheduleState table |
| Decision log (skips, reasons) | Stdout/log (Phase 6 will persist) |

## Algorithm Summary

1. Load state; determine label rotation offset for this week's cycle.
2. For each pointer (in order):
   a. Advance from `pointer.position + 1`.
   b. Skip unavailable members (vacation) — pointer does NOT advance.
   c. Skip members on cool-down (assigned last week) — pointer DOES advance.
   d. Skip members already assigned this week — pointer DOES advance.
   e. If no candidate found, retry with relaxed cool-down.
3. Update pointer positions, `last_assignments`, and week counter.
4. Persist assignments and state.

## Guarantees

| # | Guarantee | Enforcement |
|---|-----------|-------------|
| G1 | No member assigned twice in the same week | `already_assigned` set check |
| G2 | No member assigned in consecutive weeks (unless relaxed) | `last_assignments` cool-down check |
| G3 | Equal app exposure over N-week super-cycle | Label rotation every N/K weeks |
| G4 | Vacationers never assigned | `is_available` check before assignment |
| G5 | Deferred turns fulfilled on return | Pointer holds at vacationer's position |
| G6 | Always produces K assignments | Graceful degradation relaxes cool-down |

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Pool too small for cool-down | Relax cool-down, log warning |
| Fewer available members than apps | Raise `SchedulingError` |
| No state exists (first run) | `build_initial_state()` creates fresh state |

## Trigger

The engine should support two modes:
- **Automatic**: a scheduled job (e.g., cron) runs every Monday.
- **Manual**: admin triggers via API/UI for re-runs or previews.

## Out of Scope

- Persisting decision logs (Phase 6).
- Sending notifications (Phase 5).
- UI for viewing results (Phase 4).
