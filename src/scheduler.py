"""
Core scheduling algorithm for K-app triage rotation.

Design:
  - K independent pointers traverse a ring of N members.
  - Each pointer is mapped to an app via a label rotation that shifts
    every N/K weeks, ensuring every member works every app equally over
    a full N-week super-cycle.
  - Cool-down: a member assigned to *any* app last week is skipped for
    all other apps this week (pointer advances past them).
  - Vacation: pointer HOLDS at the vacationing member's position; a
    substitute is found from the remaining pool.
  - Graceful degradation: if the pool is too small to satisfy cool-down,
    the constraint is relaxed with a warning.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .models import (
    App,
    Assignment,
    Member,
    PointerState,
    ScheduleState,
    SkipReason,
)

logger = logging.getLogger(__name__)


class SchedulingError(Exception):
    """Raised when no valid assignment is possible."""


@dataclass
class SkipEvent:
    member: Member
    reason: SkipReason
    pointer_advanced: bool


def build_initial_state(members: list[Member], apps: list[App]) -> ScheduleState:
    """Create a fresh ScheduleState ready for week 1."""
    sorted_members = sorted(members, key=lambda m: m.rotation_order)
    pointers = []
    for i in range(len(apps)):
        # Stagger starting positions: pointer i starts at position i-1
        # so the first advance lands on position i.
        pointers.append(PointerState(pointer_id=i, position=i - 1))
    return ScheduleState(
        members=sorted_members,
        apps=apps,
        pointers=pointers,
        week=0,
        last_assignments={},
        label_rotation_offset=0,
    )


def _next_index(current: int, n: int) -> int:
    """Advance one step clockwise in the ring."""
    return (current + 1) % n


def _find_candidate(
    state: ScheduleState,
    pointer: PointerState,
    already_assigned_this_week: set[str],
    relax_cooldown: bool = False,
) -> tuple[Member, list[SkipEvent], bool]:
    """
    Walk the ring from pointer.position + 1 to find the next valid member.

    Returns (member, skip_events, is_substitute).
    Raises SchedulingError if we wrap the full ring with no candidate.
    """
    n = state.num_members
    skips: list[SkipEvent] = []
    start = _next_index(pointer.position, n)
    pos = start
    first_candidate = state.members[pos]
    is_substitute = False

    for _ in range(n):
        member = state.members[pos]

        # --- Vacation check (pointer does NOT advance) ---
        if not member.is_available:
            if pos == start:
                # This is the member the pointer naturally lands on.
                # Pointer HOLDS here; we look for a substitute.
                pointer.held = True
                is_substitute = True
            skips.append(SkipEvent(member, SkipReason.VACATION, pointer_advanced=False))
            pos = _next_index(pos, n)
            continue

        # --- Already assigned this week (pointer advances) ---
        if member.name in already_assigned_this_week:
            skips.append(SkipEvent(member, SkipReason.ALREADY_ASSIGNED, pointer_advanced=True))
            pos = _next_index(pos, n)
            continue

        # --- Cool-down check (pointer advances) ---
        if not relax_cooldown and member.name in state.last_assignments:
            skips.append(SkipEvent(member, SkipReason.COOLDOWN, pointer_advanced=True))
            pos = _next_index(pos, n)
            continue

        # Found a valid candidate
        return member, skips, is_substitute

    raise SchedulingError(
        f"No valid candidate found for pointer {pointer.pointer_id} "
        f"(week {state.week + 1}). All {n} members exhausted."
    )


def compute_week(state: ScheduleState) -> list[Assignment]:
    """
    Compute assignments for the next week, mutating state in place.

    Algorithm:
      1. Determine label rotation offset for this week's cycle.
      2. For each pointer (in order), find the next valid member.
      3. If cool-down blocks all candidates, retry with relaxed cool-down.
      4. Update pointer positions, last_assignments, and week counter.

    Returns a list of K Assignment objects (one per app).
    """
    state.week += 1
    k = state.num_apps
    n = state.num_members

    # --- Label rotation: shift every cycle_length weeks ---
    if n >= k and state.cycle_length > 0:
        cycle_index = ((state.week - 1) // state.cycle_length) % k
        state.label_rotation_offset = cycle_index

    assignments: list[Assignment] = []
    assigned_this_week: set[str] = set()
    new_last: dict[str, str] = {}

    for pointer in state.pointers:
        app = state.app_for_pointer(pointer.pointer_id)
        relax = False

        try:
            member, skips, is_sub = _find_candidate(
                state, pointer, assigned_this_week
            )
        except SchedulingError:
            # Retry with relaxed cool-down
            relax = True
            logger.warning(
                "Week %d: relaxing cool-down for %s (pool too small).",
                state.week, app.name,
            )
            pointer.held = False  # reset held state for retry
            member, skips, is_sub = _find_candidate(
                state, pointer, assigned_this_week, relax_cooldown=True
            )

        state.cooldown_relaxed = relax

        # Update pointer position (unless held for vacation)
        if is_sub:
            # Pointer stays held at the vacationing member's position.
            # The substitute does not move the pointer.
            pass
        else:
            # Advance pointer to the assigned member's position.
            pointer.position = state.members.index(member)
            pointer.held = False

        assigned_this_week.add(member.name)
        new_last[member.name] = app.name

        assignments.append(Assignment(
            member=member,
            app=app,
            week=state.week,
            is_substitute=is_sub,
        ))

        for skip in skips:
            reason = skip.reason.value
            adv = "ptr advances" if skip.pointer_advanced else "ptr holds"
            logger.debug(
                "Week %d, %s: skipped %s (%s, %s)",
                state.week, app.name, skip.member.name, reason, adv,
            )

    state.last_assignments = new_last
    return assignments


def run_schedule(
    members: list[Member],
    apps: list[App],
    weeks: int,
) -> list[list[Assignment]]:
    """Run the scheduler for the given number of weeks. Returns weekly assignments."""
    state = build_initial_state(members, apps)
    all_weeks: list[list[Assignment]] = []
    for _ in range(weeks):
        assignments = compute_week(state)
        all_weeks.append(assignments)
    return all_weeks
