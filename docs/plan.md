# Triage Scheduler — Implementation Plan

## Problem

A team of N members rotates triage duty across K applications on a weekly cadence.
Naive round-robin with K independent pointers causes members to get locked to the
same app(s) due to the GCD problem (effective step size `gcd(K, N)` partitions the
ring). We need a system that is both **fair** (equal total duty) and **balanced**
(equal exposure to every app).

## Solution: Label-Rotating Round-Robin

- **K independent pointers** traverse a ring of N members sorted by `rotation_order`.
- **Cool-down**: anyone assigned last week is skipped for all apps this week.
- **Label rotation**: every `N/K` weeks, rotate which pointer maps to which app.
  This breaks the GCD lock-in, giving every member every app equally over an
  N-week super-cycle.
- **Vacation**: pointer HOLDS at the vacationing member; a substitute fills in.
  When the member returns they are first in line (deferred turn, not lost).
- **Graceful degradation**: if the pool is too small to satisfy cool-down, relax
  the constraint with a logged warning.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vacation pointer behavior | Hold (Option C) | Preserves fairness; deferred turn fulfilled on return |
| Cool-down scope | Cross-app (any app last week) | Prevents back-to-back duty regardless of app |
| Label rotation period | N/K weeks | Mathematically guarantees full app coverage per super-cycle |
| Algorithm generality | K-app generic | Start with K=2, adding K=3 is a config change, not a code change |
| Management model | Hybrid crowd-sourced | Self-service availability + admin roster control |

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

## Phases

| Phase | Name | Depends On | Delivers |
|-------|------|------------|----------|
| 1 | Data Model & Persistence | — | Members, apps, teams, schedule history in DB |
| 2 | Scheduling Engine | Phase 1 | Algorithm as a service with guarantees |
| 3 | Admin UI & Member Management | Phase 1 | Roster management, self-service availability |
| 4 | Schedule Dashboard | Phase 2 | Published weekly view, history, upcoming |
| 5 | Notifications | Phase 4 | Email + Teams alerts on schedule publish |
| 6 | Observability & Audit | Phase 2 | Decision logs, fairness tracking, overrides |

See `docs/specs/` for detailed per-phase specifications.

## Key Invariants (must hold across all phases)

1. No member is assigned two apps in the same week.
2. No member is assigned in consecutive weeks (unless cool-down is relaxed).
3. Over any N-week super-cycle, each member does each app the same number of times.
4. A vacationing member is never assigned; their deferred turn is fulfilled on return.
5. Every scheduling decision is logged with skip reasons.
