"""
Tests for the triage scheduler algorithm.
"""
from __future__ import annotations

import pytest

from src.models import App, Member, ScheduleState
from src.scheduler import (
    SchedulingError,
    build_initial_state,
    compute_week,
    run_schedule,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_members(n: int = 6) -> list[Member]:
    names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank",
             "Grace", "Heidi", "Ivan"]
    return [Member(name=names[i], rotation_order=i) for i in range(n)]


def make_apps(k: int = 2) -> list[App]:
    labels = ["App A", "App B", "App C", "App D"]
    return [App(name=labels[i], id=i) for i in range(k)]


def assignment_table(weeks_result):
    """Return list of dicts: [{app_name: member_name}, ...]."""
    table = []
    for week_assignments in weeks_result:
        row = {a.app.name: a.member.name for a in week_assignments}
        table.append(row)
    return table


# ---------------------------------------------------------------------------
# Basic 2-app, 6-member tests
# ---------------------------------------------------------------------------

class TestBasicRotation:
    """Verify the fundamental round-robin pattern with 2 apps, 6 members."""

    def test_first_week_assigns_two_different_members(self):
        result = run_schedule(make_members(), make_apps(), weeks=1)
        assert len(result) == 1
        assert len(result[0]) == 2
        names = {a.member.name for a in result[0]}
        assert len(names) == 2, "Two different members should be assigned"

    def test_no_member_assigned_twice_same_week(self):
        result = run_schedule(make_members(), make_apps(), weeks=12)
        for week_assignments in result:
            names = [a.member.name for a in week_assignments]
            assert len(names) == len(set(names)), \
                f"Duplicate assignment in week {week_assignments[0].week}"

    def test_cooldown_respected(self):
        """A member assigned week W should not appear in week W+1."""
        result = run_schedule(make_members(), make_apps(), weeks=12)
        table = assignment_table(result)
        for i in range(len(table) - 1):
            assigned_this = set(table[i].values())
            assigned_next = set(table[i + 1].values())
            overlap = assigned_this & assigned_next
            assert not overlap, (
                f"Cool-down violated between week {i+1} and {i+2}: {overlap}"
            )

    def test_all_members_assigned_over_cycle(self):
        """Every member should be assigned at least once in 6 weeks."""
        result = run_schedule(make_members(), make_apps(), weeks=6)
        all_names = set()
        for week_assignments in result:
            for a in week_assignments:
                all_names.add(a.member.name)
        members = make_members()
        expected = {m.name for m in members}
        assert all_names == expected


# ---------------------------------------------------------------------------
# Label rotation / fairness
# ---------------------------------------------------------------------------

class TestLabelRotation:
    """Verify label rotation gives every member every app over the super-cycle."""

    def test_all_members_do_all_apps_over_supercycle(self):
        """Over N weeks (super-cycle), each member should do each app equally."""
        members = make_members(6)
        apps = make_apps(2)
        n = len(members)
        result = run_schedule(members, apps, weeks=n)

        # Count per member per app
        counts: dict[str, dict[str, int]] = {m.name: {a.name: 0 for a in apps} for m in members}
        for week_assignments in result:
            for a in week_assignments:
                counts[a.member.name][a.app.name] += 1

        for member_name, app_counts in counts.items():
            total = sum(app_counts.values())
            assert total == 2, f"{member_name} assigned {total} times in {n} weeks, expected 2"
            for app_name, count in app_counts.items():
                assert count == 1, (
                    f"{member_name} did {app_name} {count} times, expected 1 per super-cycle"
                )

    def test_label_rotation_offset_changes(self):
        """The label rotation offset should change after cycle_length weeks."""
        state = build_initial_state(make_members(6), make_apps(2))
        # cycle_length = 6 / 2 = 3 weeks
        assert state.cycle_length == 3

        # Weeks 1-3: offset 0
        for _ in range(3):
            compute_week(state)
        assert state.label_rotation_offset == 0  # still in first cycle's last week

        # Week 4 triggers offset 1
        compute_week(state)
        assert state.label_rotation_offset == 1


# ---------------------------------------------------------------------------
# Vacation handling
# ---------------------------------------------------------------------------

class TestVacation:
    """Pointer holds on vacation; substitute fills in; member returns first."""

    def test_vacation_produces_substitute(self):
        members = make_members(6)
        apps = make_apps(2)
        state = build_initial_state(members, apps)

        # Week 1: normal
        w1 = compute_week(state)

        # Put Carol on vacation for week 2
        state.members[2].is_available = False
        w2 = compute_week(state)
        w2_names = {a.member.name for a in w2}
        assert "Carol" not in w2_names, "Carol should not be assigned while on vacation"

    def test_pointer_holds_during_vacation(self):
        members = make_members(6)
        apps = make_apps(2)
        state = build_initial_state(members, apps)

        # Week 1: normal
        compute_week(state)

        # Carol (index 2) goes on vacation
        state.members[2].is_available = False

        # Record pointer positions before
        ptr_positions_before = [p.position for p in state.pointers]
        compute_week(state)

        # The pointer that would have landed on Carol should be held
        held_pointers = [p for p in state.pointers if p.held]
        assert len(held_pointers) >= 1, "At least one pointer should be held"

    def test_member_returns_gets_assigned(self):
        members = make_members(6)
        apps = make_apps(2)
        state = build_initial_state(members, apps)

        # Week 1: normal
        compute_week(state)

        # Carol on vacation weeks 2-3
        state.members[2].is_available = False
        compute_week(state)
        compute_week(state)

        # Carol returns week 4
        state.members[2].is_available = True
        w4 = compute_week(state)
        w4_names = {a.member.name for a in w4}
        assert "Carol" in w4_names, "Carol should be assigned on her return week"

    def test_multi_week_vacation_always_has_substitute(self):
        """
        Regression test for the 'and not pointer.held' bug.

        When a member is on vacation for multiple consecutive weeks, a substitute
        must be found every week — not just the first. The old guard prevented
        re-arming is_substitute on week 2+, causing the pointer to advance past
        the vacationing member instead of holding and finding a sub.
        """
        members = make_members(6)
        apps = make_apps(2)
        state = build_initial_state(members, apps)

        # Week 1: normal
        compute_week(state)

        # Put Carol (index 2) on vacation for 3 consecutive weeks
        state.members[2].is_available = False
        for week_num in range(2, 5):  # weeks 2, 3, 4
            week_result = compute_week(state)
            names = {a.member.name for a in week_result}
            assert "Carol" not in names, \
                f"Carol should not be assigned in week {week_num} while on vacation"
            # Exactly 2 assignments should exist (one per app)
            assert len(week_result) == 2, \
                f"Week {week_num} should still produce 2 assignments"
            # At least one should be flagged as a substitute
            subs = [a for a in week_result if a.is_substitute]
            assert len(subs) >= 1, \
                f"Week {week_num} should have a substitute while Carol is on vacation"

        # Carol returns week 5 — pointer should land on her
        state.members[2].is_available = True
        w5 = compute_week(state)
        w5_names = {a.member.name for a in w5}
        assert "Carol" in w5_names, "Carol should be assigned on her return week"


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    """Cool-down is relaxed when pool is too small."""

    def test_small_pool_still_assigns(self):
        """With 3 members and 2 apps, cool-down must be relaxed."""
        members = make_members(3)
        apps = make_apps(2)
        # Should not raise — cool-down relaxation kicks in
        result = run_schedule(members, apps, weeks=6)
        for week_assignments in result:
            assert len(week_assignments) == 2

    def test_minimum_viable_pool(self):
        """With exactly 2 members and 2 apps, everyone works every week."""
        members = make_members(2)
        apps = make_apps(2)
        result = run_schedule(members, apps, weeks=4)
        for week_assignments in result:
            names = {a.member.name for a in week_assignments}
            assert len(names) == 2


# ---------------------------------------------------------------------------
# 3-app generalization
# ---------------------------------------------------------------------------

class TestThreeApps:
    """Validate the algorithm generalizes to 3 apps."""

    def test_three_apps_six_members_basic(self):
        members = make_members(6)
        apps = make_apps(3)
        result = run_schedule(members, apps, weeks=6)
        for week_assignments in result:
            assert len(week_assignments) == 3
            names = [a.member.name for a in week_assignments]
            assert len(names) == len(set(names))

    def test_three_apps_no_cooldown_violation(self):
        members = make_members(6)
        apps = make_apps(3)
        result = run_schedule(members, apps, weeks=12)
        table = assignment_table(result)
        for i in range(len(table) - 1):
            assigned_this = set(table[i].values())
            assigned_next = set(table[i + 1].values())
            overlap = assigned_this & assigned_next
            assert not overlap, (
                f"Cool-down violated between week {i+1} and {i+2}: {overlap}"
            )

    def test_three_apps_fairness_over_supercycle(self):
        """Over N weeks, each member does each of the 3 apps equally."""
        members = make_members(6)
        apps = make_apps(3)
        n = len(members)
        result = run_schedule(members, apps, weeks=n)

        counts: dict[str, dict[str, int]] = {m.name: {a.name: 0 for a in apps} for m in members}
        for week_assignments in result:
            for a in week_assignments:
                counts[a.member.name][a.app.name] += 1

        for member_name, app_counts in counts.items():
            total = sum(app_counts.values())
            assert total == 3, f"{member_name} assigned {total} times in {n} weeks, expected 3"
            for app_name, count in app_counts.items():
                assert count == 1, (
                    f"{member_name} did {app_name} {count} times, expected 1"
                )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_single_app(self):
        """With 1 app, every member gets it in round-robin order."""
        members = make_members(4)
        apps = make_apps(1)
        result = run_schedule(members, apps, weeks=8)
        for week_assignments in result:
            assert len(week_assignments) == 1

    def test_everyone_on_vacation_raises(self):
        members = make_members(4)
        apps = make_apps(2)
        for m in members:
            m.is_available = False
        state = build_initial_state(members, apps)
        with pytest.raises(SchedulingError):
            compute_week(state)
