import pytest
from datetime import date, timedelta

from app import create_app
from app.extensions import db as _db
from app.db_models import Member, TriageApp, Team, Availability, Assignment, ScheduleState
from app.db_models.availability import AvailabilityReason
from app.services.scheduler_service import run_week

MONDAY = date(2026, 4, 6)  # A known Monday


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        yield
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def seeded_team(app):
    """6-member, 2-app team with no prior schedule state."""
    with app.app_context():
        app_a = TriageApp(name="App A", sort_order=0)
        app_b = TriageApp(name="App B", sort_order=1)
        names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
        members = [
            Member(name=n, email=f"{n.lower()}@example.com", rotation_order=i)
            for i, n in enumerate(names)
        ]
        team = Team(name="Platform Team", members=members, apps=[app_a, app_b])
        _db.session.add_all([app_a, app_b, *members, team])
        _db.session.commit()
        return team.id


class TestFirstRun:
    def test_first_run_creates_state(self, app, seeded_team):
        with app.app_context():
            assert ScheduleState.query.count() == 0
            run_week(seeded_team, MONDAY)
            assert ScheduleState.query.count() == 1

    def test_assignments_persisted(self, app, seeded_team):
        with app.app_context():
            run_week(seeded_team, MONDAY)
            assignments = Assignment.query.filter_by(team_id=seeded_team, week=MONDAY).all()
            assert len(assignments) == 2  # one per app

    def test_assignment_week_normalized_to_monday(self, app, seeded_team):
        with app.app_context():
            wednesday = MONDAY + timedelta(days=2)
            run_week(seeded_team, wednesday)
            # Should normalize to the Monday
            assert Assignment.query.filter_by(week=MONDAY).count() == 2

    def test_schedule_state_updated(self, app, seeded_team):
        with app.app_context():
            run_week(seeded_team, MONDAY)
            state = _db.session.get(ScheduleState, seeded_team)
            assert state.current_week == 1
            assert len(state.last_assignments) == 2  # 2 members assigned


class TestSubsequentRuns:
    def test_duplicate_week_raises(self, app, seeded_team):
        with app.app_context():
            run_week(seeded_team, MONDAY)
            with pytest.raises(ValueError, match="already scheduled"):
                run_week(seeded_team, MONDAY)

    def test_cooldown_respected(self, app, seeded_team):
        with app.app_context():
            week1 = run_week(seeded_team, MONDAY)
            week1_names = {a.member.name for a in week1}

            week2 = run_week(seeded_team, MONDAY + timedelta(weeks=1))
            week2_names = {a.member.name for a in week2}

            assert week1_names.isdisjoint(week2_names)


class TestVacation:
    def test_vacation_member_not_assigned(self, app, seeded_team):
        with app.app_context():
            # Put Alice on vacation for this week
            alice = Member.query.filter_by(name="Alice").first()
            avail = Availability(
                member_id=alice.id,
                week_start=MONDAY,
                week_end=MONDAY + timedelta(weeks=1),
                reason=AvailabilityReason.vacation,
            )
            _db.session.add(avail)
            _db.session.commit()

            assignments = run_week(seeded_team, MONDAY)
            assigned_names = {a.member.name for a in assignments}
            assert "Alice" not in assigned_names

    def test_substitute_flagged(self, app, seeded_team):
        with app.app_context():
            # Put Alice (rotation_order=0, first pointer target) on vacation
            alice = Member.query.filter_by(name="Alice").first()
            avail = Availability(
                member_id=alice.id,
                week_start=MONDAY,
                week_end=MONDAY + timedelta(weeks=1),
                reason=AvailabilityReason.vacation,
            )
            _db.session.add(avail)
            _db.session.commit()

            assignments = run_week(seeded_team, MONDAY)
            # At least one assignment should be a substitute
            assert any(a.is_substitute for a in assignments)


class TestDryRun:
    def test_dry_run_does_not_persist(self, app, seeded_team):
        with app.app_context():
            run_week(seeded_team, MONDAY, dry_run=True)
            assert Assignment.query.count() == 0
            assert ScheduleState.query.count() == 0

    def test_dry_run_returns_domain_assignments(self, app, seeded_team):
        with app.app_context():
            from src.models import Assignment as DomainAssignment
            results = run_week(seeded_team, MONDAY, dry_run=True)
            assert len(results) == 2
            assert all(isinstance(r, DomainAssignment) for r in results)


class TestPreviewCommand:
    def test_preview_command_exits_ok(self, app, seeded_team):
        with app.app_context():
            from app.commands import schedule_preview
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(
                schedule_preview,
                ["--weeks", "3", "--start", "2026-04-06"],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            assert "Week of 2026-04-06" in result.output
            assert "Week of 2026-04-13" in result.output
            assert "Week of 2026-04-20" in result.output

    def test_preview_does_not_persist(self, app, seeded_team):
        with app.app_context():
            from app.commands import schedule_preview
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(schedule_preview, ["--weeks", "4"], catch_exceptions=False)
            assert Assignment.query.count() == 0
