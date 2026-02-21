# Phase 1 — Data Model & Persistence

## Scope

Define and persist all entities the system operates on. This phase delivers the
database schema and data-access layer that every subsequent phase builds upon.

## Depends On

Nothing — this is the foundation.

## Entities

### Member
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Display name |
| email | string | For notifications (Phase 5) |
| rotation_order | int | Position in the ring (0-based, unique within team) |
| is_active | bool | Soft-delete flag; inactive members are excluded from scheduling |
| created_at | timestamp | |
| updated_at | timestamp | |

### App
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Display name (e.g., "App A") |
| sort_order | int | Determines pointer-to-app mapping order |

### Team
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Team name |
| apps | FK[] | Apps this team rotates across |
| members | FK[] | Members in this team's rotation pool |

### Availability
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| member_id | FK | |
| week_start | date | Monday of the unavailable week |
| week_end | date | Monday of the return week |
| reason | enum | `vacation`, `leave`, `other` |
| created_by | FK | Self or admin who created it |

### Assignment
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| member_id | FK | |
| app_id | FK | |
| team_id | FK | |
| week | date | Monday of the assigned week |
| is_substitute | bool | True if filling in for a vacationer |
| created_at | timestamp | When the engine generated this |

### ScheduleState
| Field | Type | Description |
|-------|------|-------------|
| team_id | FK | One state per team |
| pointer_positions | JSON | `{pointer_id: position}` |
| pointer_held | JSON | `{pointer_id: bool}` |
| label_rotation_offset | int | Current rotation offset |
| last_assignments | JSON | `{member_name: app_name}` from prior week |
| current_week | int | Week counter |

## Invariants

1. `rotation_order` is unique within a team.
2. A member can belong to at most one team.
3. Availability ranges do not overlap for the same member.
4. At most one Assignment per member per week per team.

## Out of Scope

- User authentication (deferred to Phase 3).
- Notification preferences (Phase 5).
- Audit log entries (Phase 6).
