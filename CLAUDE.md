# CLAUDE.md — Triage Scheduler

## Project Overview

Weekly triage rotation tool. Assigns team members to triage duty across K apps using a label-rotating round-robin algorithm with vacation hold, cross-app cool-down, and graceful degradation.

## Architecture

```
src/                    # Pure Python algorithm — NO Flask dependencies
  models.py             # Domain dataclasses: Member, App, Assignment, PointerState, ScheduleState
  scheduler.py          # Core algorithm: build_initial_state(), compute_week(), run_schedule()

app/                    # Flask web layer
  admin/                # Admin blueprint — url_prefix="/manage"
    auth.py             # Session auth, @admin_required decorator
    routes.py           # Roster, apps, availability, schedule CRUD
  main/                 # Public blueprint — url_prefix="/" (read-only calendar)
  db_models/            # SQLAlchemy ORM models (Member, TriageApp, Team, Availability, Assignment, ScheduleState)
  services/
    scheduler_service.py  # Bridge: ORM → domain → algorithm → ORM
                          # Key public fn: build_calendar(), run_week()
  templates/
    schedule.html         # Public macOS-style monthly calendar
    admin/schedule.html   # Admin schedule (table view with Run/Delete)

tests/
  test_scheduler.py     # Pure algorithm tests (72 total)
  test_admin.py         # Admin route integration tests
  test_dashboard.py     # Public dashboard tests
```

## Key Design Decisions

- **Domain/ORM separation**: `src/` has zero Flask deps — algorithm is fully testable without DB
- **`build_calendar(team, year, month)`** in `scheduler_service.py` is shared by both admin and public views; returns `app_index` (int), not colors — color mapping stays in UI layer
- **`APP_COLORS`** is defined per-blueprint (`admin/routes.py`, `main/routes.py`) — future-ready for config-driven theming
- **Vacation hold**: pointer holds at vacationer's position; `is_substitute=True` only when the pointer's natural first candidate (`pos == start`) is on vacation
- **State reset guard**: treat `orm_state.pointer_positions == {}` same as `orm_state is None` (use `build_initial_state`)
- **Member reorder blocked** when assignments exist — must delete all weeks first

## Common Commands

```bash
# Run tests
pytest tests/ -v

# Start dev server
flask run --port 5001

# DB
flask db upgrade
flask seed-db

# Scheduling CLI
flask schedule-preview
flask schedule-week
```

## Environment Variables

```
DATABASE_URL=postgresql://triage:triage@localhost/triage_scheduler_dev
SECRET_KEY=change-me
ADMIN_PASSWORD=change-me
```

## Testing Notes

- Tests use SQLite in-memory (`TestingConfig`) — no Postgres needed
- Admin tests use `/manage/` prefix (blueprint name is still `"admin"`, url_prefix is `/manage`)
- Algorithm invariants enforced in `test_scheduler.py`: no duplicate weekly assignments, cool-down respected, fairness over super-cycle

## Gotchas

- `_delete_week` replays history using the **current** member order — reordering members after scheduling and then deleting will produce wrong state. Guard in `roster_reorder` blocks this.
- `except Exception: pass` in `build_calendar` preview generation silences scheduler errors — check server logs if preview goes blank
- Availability `week_start` and `week_end` must both be Mondays (enforced server-side)
- `flask run` defaults to port 5000 which conflicts with macOS AirPlay — use `--port 5001`
