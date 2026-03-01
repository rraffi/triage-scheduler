# Phase 3 — Admin UI & Member Management

## Scope

Web interface for managing the roster, apps, and availability. Hybrid model:
members self-manage their own availability; admins manage the roster and app config.

## Depends On

Phase 1 (Data Model & Persistence).

## Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Add/remove members, set rotation order, add/remove apps, configure team, trigger schedule, override assignments |
| **Member** | View own schedule, mark vacation/unavailability, request swap with another member |

## Admin Capabilities

### Roster Management
- Add member (name, email, rotation order).
- Remove member (soft-delete — set `is_active = false`).
- Reorder members (drag-and-drop or manual `rotation_order` edit).
- View current roster with rotation order.

### App Configuration
- Add/remove apps.
- Rename apps.
- Reorder apps (affects pointer-to-app mapping).

### Schedule Control
- Trigger a schedule run for the next week (preview before publish).
- Override an assignment (manual swap) with audit trail.
- Re-run schedule if an error occurred.

## Member Self-Service

### Availability
- Mark date ranges as unavailable (vacation, leave).
- Cancel a previously marked absence.
- View own upcoming availability calendar.

### Swap Requests
- Request to swap assignment with another member for a specific week.
- Other member must accept.
- Admin can approve/deny if policy requires.

## UI Views

| View | Description |
|------|-------------|
| Roster | List of members with rotation order, status, email |
| Apps | List of apps with sort order |
| Availability Calendar | Per-member or team-wide availability grid |
| Swap Requests | Pending/approved/denied swap requests |

## Invariants

1. Rotation order stays unique after any edit.
2. Removing a member does not break existing schedule history.
3. Adding a member mid-cycle inserts them at the end of the ring.
4. Swap requests require mutual consent (or admin override).

## Out of Scope

- Schedule viewing (Phase 4).
- Notification preferences (Phase 5).
