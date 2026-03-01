# Phase 6 — Observability & Audit

## Scope

Full transparency into scheduling decisions. Every skip, override, and degradation
is logged and queryable. Provides the evidence that the system is fair and the
tools to investigate when something looks off.

## Depends On

Phase 2 (Scheduling Engine).

## Components

### Decision Log

Every scheduling run produces a detailed log of what happened:

| Field | Description |
|-------|-------------|
| week | Which week was being scheduled |
| pointer_id | Which pointer was being resolved |
| app | Which app (after label rotation) |
| member | Member being evaluated |
| action | `assigned`, `skipped`, `substituted` |
| reason | `cooldown`, `vacation`, `already_assigned`, `selected` |
| pointer_advanced | Whether the pointer moved past this member |
| cooldown_relaxed | Whether cool-down was relaxed for this assignment |
| timestamp | When the decision was made |

### Override Log

When an admin manually changes an assignment:

| Field | Description |
|-------|-------------|
| week | Affected week |
| original_member | Who was originally assigned |
| new_member | Who replaced them |
| app | Which app |
| admin | Who made the change |
| reason | Free-text justification |
| timestamp | When the override occurred |

### Fairness Dashboard

Aggregated view of assignment distribution:

- **Per-member totals**: assignments by app, over configurable time ranges.
- **Deviation indicator**: flag if any member's count deviates beyond 1 from the
  expected value for the current super-cycle position.
- **Trend chart**: assignments over time, showing the rotation pattern.

### System Health

| Metric | Description |
|--------|-------------|
| Cool-down relaxation count | How often degradation kicked in |
| Vacation fill-in count | How often substitutes were needed |
| Scheduling failures | Runs that raised `SchedulingError` |
| Notification delivery rate | Success/failure per channel |

## Acceptance Criteria

1. Every scheduling decision is persisted and queryable by week.
2. Admin overrides include the admin's identity and stated reason.
3. Fairness dashboard shows correct per-member per-app counts.
4. Deviation alerts fire when distribution skew exceeds threshold.
5. Decision logs are linkable from the schedule history view (Phase 4).

## Out of Scope

- External monitoring integration (Datadog, PagerDuty, etc.) — can be layered on.
- Automated corrective actions (e.g., auto-rebalancing on skew).
