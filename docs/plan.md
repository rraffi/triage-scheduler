# Triage Scheduler — Implementation Plan

## Context

Build an internal tool to assign team members ("automation angels") to triage duty
across K applications on a weekly cadence. Uses a **label-rotating round-robin** with
cross-app cool-down, vacation pointer holding, and graceful degradation.

The algorithm is K-app generic — start with K=2 (App A, App B), but adding a third app
is a configuration change, not a code change.

Tech stack: Flask + PostgreSQL + SQLAlchemy + Jinja templates + Bootstrap 5.

---

## Current State

The core scheduling algorithm is implemented and tested as a pure Python library:

- `src/models.py` — Domain dataclasses: `Member`, `App`, `Assignment`, `PointerState`, `ScheduleState`
- `src/scheduler.py` — Algorithm: `build_initial_state()`, `compute_week()`, `run_schedule()`
- `tests/test_scheduler.py` — 14 tests covering rotation, label rotation, vacation, graceful degradation, K=1/2/3, edge cases
- `docs/` — Architecture plan, 6-phase specs, algorithm diagrams

---

## Algorithm: Label-Rotating Round-Robin with K Apps

File: `src/scheduler.py` — pure functions, no Flask dependencies.

**Core mechanics:**
1. **K independent pointers** traverse a ring of N members sorted by `rotation_order`.
2. **Label rotation**: every `N/K` weeks, rotate which pointer maps to which app.
   This breaks the GCD lock-in, giving every member every app equally over an
   N-week super-cycle.
3. **Cross-app cool-down**: anyone assigned *any* app last week is skipped for all
   apps this week (pointer advances past them).
4. **Vacation handling (Option C — pointer holds)**:
   - Pointer does NOT advance past a vacationing member.
   - A substitute is found from the remaining pool.
   - When the member returns, the held pointer makes them first in line (deferred turn).
5. **Graceful degradation**: if the pool is too small to satisfy cool-down, relax the
   constraint with a logged warning. If fewer available members than apps, raise `SchedulingError`.

**Orchestration** (`run_schedule(members, apps, weeks)`):
- For each of N weeks, call `compute_week(state)` which mutates state in place.
- Returns `list[list[Assignment]]` — one inner list per week, one assignment per app.

**Skip reasons are logged** with pointer behavior:
- `VACATION` — pointer holds (does not advance)
- `COOLDOWN` — pointer advances
- `ALREADY_ASSIGNED` — pointer advances

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Web Dashboard                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Admin UI    │  │  Schedule    │  │  Fairness  │ │
│  │  (Phase 3)   │  │  View        │  │  Stats     │ │
│  │              │  │  (Phase 4)   │  │  (Phase 6) │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │        │
│  ───────┴─────────────────┴─────────────────┴─────── │
│                      API Layer                       │
│  ───────────────────────┬────────────────────────── │
│                         │                            │
│         ┌───────────────┴───────────────┐            │
│         │     Scheduling Engine         │            │
│         │         (Phase 2)             │            │
│         └───────────────┬───────────────┘            │
│                         │                            │
│         ┌───────────────┴───────────────┐            │
│         │    Data Model & Persistence   │            │
│         │         (Phase 1)             │            │
│         └───────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │    Notifications      │
              │      (Phase 5)        │
              │  Email  │  Teams Chat │
              └───────────────────────┘
```

---

## Project Structure (Target)

```
triage-scheduler/
├── .gitignore
├── .env.example
├── .flaskenv
├── requirements.txt
├── config.py                       # Dev/Test/Prod config classes
├── wsgi.py                         # WSGI entry point
├── src/                            # Pure domain logic (no Flask deps)
│   ├── __init__.py
│   ├── models.py                   # Domain dataclasses (EXISTS)
│   └── scheduler.py               # Scheduling algorithm (EXISTS)
├── app/                            # Flask web layer (Phases 3-4)
│   ├── __init__.py                 # App factory: create_app()
│   ├── extensions.py               # db, migrate instances
│   ├── db_models/                  # SQLAlchemy ORM models (Phase 1)
│   │   ├── __init__.py
│   │   ├── member.py
│   │   ├── app.py
│   │   ├── team.py
│   │   ├── availability.py
│   │   ├── assignment.py
│   │   └── schedule_state.py
│   ├── main/
│   │   ├── __init__.py             # Blueprint definition
│   │   └── routes.py               # HTTP routes (Phases 3-4)
│   ├── templates/                  # Jinja2 templates (Phases 3-4)
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── schedule.html
│   │   ├── team_members.html
│   │   └── availability.html
│   └── static/
│       └── css/style.css
├── docs/
│   ├── plan.md                     # Architecture plan (EXISTS)
│   ├── render_diagrams.py          # Diagram renderer (EXISTS)
│   └── specs/                      # Per-phase specs (EXISTS)
├── migrations/                     # Created by flask db init
└── tests/
    ├── __init__.py
    ├── test_scheduler.py           # Algorithm tests (EXISTS — 14 tests)
    ├── test_db_models.py           # ORM model tests (Phase 1)
    └── test_routes.py              # Route tests (Phases 3-4)
```

---

## 6-Phase Roadmap

| Phase | Name | Depends On | Delivers |
|-------|------|------------|----------|
| 1 | Data Model & Persistence | — | ORM models, migrations, DB seed |
| 2 | Scheduling Engine Integration | Phase 1 | Algorithm wired to DB, CLI trigger |
| 3 | Admin UI & Member Management | Phase 1 | Roster mgmt, self-service availability |
| 4 | Schedule Dashboard | Phase 2 | Published weekly view, history, fairness summary |
| 5 | Notifications | Phase 4 | Email + Teams alerts on schedule publish |
| 6 | Observability & Audit | Phase 2 | Decision logs, fairness tracking, override history |

See `docs/specs/` for detailed per-phase specifications.

---

## Phase 1 — Data Model & Persistence

### Database Models (SQLAlchemy ORM)

**Member** (`members`)
- `id` (UUID, PK)
- `name` (String, not null)
- `email` (String, not null, unique)
- `rotation_order` (Integer, not null, unique within team)
- `is_active` (Boolean, default True)
- `created_at`, `updated_at` (DateTime)

**App** (`apps`)
- `id` (UUID, PK)
- `name` (String, not null, unique)
- `sort_order` (Integer) — determines pointer-to-app mapping order

**Team** (`teams`)
- `id` (UUID, PK)
- `name` (String, not null)
- `apps` (FK[]) — apps this team rotates across
- `members` (FK[]) — members in this team's rotation pool

**Availability** (`availability`)
- `id` (UUID, PK)
- `member_id` (FK -> members.id)
- `week_start` (Date) — Monday of the unavailable week
- `week_end` (Date) — Monday of the return week
- `reason` (Enum: `vacation`, `leave`, `other`)
- `created_by` (FK) — self or admin

**Assignment** (`assignments`)
- `id` (UUID, PK)
- `member_id` (FK -> members.id)
- `app_id` (FK -> apps.id)
- `team_id` (FK -> teams.id)
- `week` (Date) — Monday of the assigned week
- `is_substitute` (Boolean) — True if filling in for a vacationer
- `created_at` (DateTime)

**ScheduleState** (`schedule_state`)
- `team_id` (FK, one state per team)
- `pointer_positions` (JSON) — `{pointer_id: position}`
- `pointer_held` (JSON) — `{pointer_id: bool}`
- `label_rotation_offset` (Integer)
- `last_assignments` (JSON) — `{member_name: app_name}` from prior week
- `current_week` (Integer)

### Phase 1 Tasks
1. Project scaffolding: `.gitignore`, `requirements.txt`, `config.py`, `.env.example`, Flask app factory
2. Define ORM models with migrations (`flask db init`, `flask db migrate`)
3. Seed command: `flask seed-db` creates default team, apps, and sample members
4. Tests: model constraints, relationships, seed command

---

## Phase 2 — Scheduling Engine Integration

Wire the pure algorithm (`src/scheduler.py`) to the persistence layer.

### Tasks
1. Service layer: load `ScheduleState` + members + availability from DB, call `compute_week()`, persist `Assignment` records and updated state
2. CLI command: `flask schedule-week` — runs one week of scheduling
3. Look-ahead: `flask schedule-preview --weeks=4` — dry-run preview without persisting
4. Tests: integration tests with DB fixtures

---

## Phases 3-6 (Outline)

### Phase 3 — Admin UI & Member Management
- Routes: team roster CRUD, self-service availability, manual swap
- Templates: Bootstrap 5, Jinja2 inheritance from `base.html`
- Auth: basic admin login (can evolve later)

### Phase 4 — Schedule Dashboard
- Published weekly view: current + upcoming weeks
- History view with fairness summary per member
- Manual override with `is_substitute` tracking

### Phase 5 — Notifications
- Email (Flask-Mail) + Teams Incoming Webhook
- Triggered on schedule publish

### Phase 6 — Observability & Audit
- Persist decision logs (skip reasons, pointer movements)
- Fairness dashboard: per-member app distribution over time
- Override history

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Algorithm generality | K-app generic | K=2 now; adding K=3 is config, not code |
| Vacation pointer behavior | Hold (Option C) | Preserves fairness; deferred turn on return |
| Cool-down scope | Cross-app | Prevents back-to-back duty regardless of app |
| Label rotation period | Every N/K weeks | Mathematically guarantees equal app exposure |
| Domain vs ORM separation | `src/` pure, `app/` Flask | Algorithm testable without DB or Flask |
| Management model | Hybrid crowd-sourced | Self-service availability + admin roster control |
| `week` field | Always normalized to Monday | Consistent weekly boundaries |

---

## Key Invariants (must hold across all phases)

1. No member is assigned two apps in the same week.
2. No member is assigned in consecutive weeks (unless cool-down is relaxed).
3. Over any N-week super-cycle, each member does each app the same number of times.
4. A vacationing member is never assigned; their deferred turn is fulfilled on return.
5. Every scheduling decision is logged with skip reasons.

---

## Verification Plan

1. `pytest tests/` — all 14 algorithm tests pass (rotation, label rotation, vacation, K=1/2/3, edge cases)
2. Phase 1: `flask db upgrade && flask seed-db` creates schema and seed data
3. Phase 2: `flask schedule-week` produces correct assignments; verify with `flask schedule-preview`
4. Phase 3+: manually add members, set availability, trigger recalculate, verify schedule
