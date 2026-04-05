import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db as _db
from app.db_models import Member, TriageApp, Team, Availability, Assignment, AvailabilityReason


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Roll back after each test to keep tests isolated."""
    with app.app_context():
        yield
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def team_with_members(app):
    with app.app_context():
        app_a = TriageApp(name="App A", sort_order=0)
        app_b = TriageApp(name="App B", sort_order=1)
        m1 = Member(name="Alice", email="alice@example.com", rotation_order=0)
        m2 = Member(name="Bob", email="bob@example.com", rotation_order=1)
        team = Team(name="Platform Team", members=[m1, m2], apps=[app_a, app_b])
        _db.session.add_all([app_a, app_b, m1, m2, team])
        _db.session.commit()
        return team.id, m1.id, m2.id, app_a.id, app_b.id


class TestMemberModel:
    def test_create_member(self, app):
        with app.app_context():
            m = Member(name="Alice", email="alice@example.com", rotation_order=0)
            _db.session.add(m)
            _db.session.commit()
            assert Member.query.filter_by(email="alice@example.com").first() is not None

    def test_email_unique_constraint(self, app):
        with app.app_context():
            m1 = Member(name="Alice", email="dup@example.com", rotation_order=0)
            m2 = Member(name="Alice2", email="dup@example.com", rotation_order=1)
            _db.session.add_all([m1, m2])
            with pytest.raises(IntegrityError):
                _db.session.commit()

    def test_is_active_default_true(self, app):
        with app.app_context():
            m = Member(name="Bob", email="bob@example.com", rotation_order=1)
            _db.session.add(m)
            _db.session.commit()
            assert m.is_active is True

    def test_timestamps_set_on_create(self, app):
        with app.app_context():
            m = Member(name="Carol", email="carol@example.com", rotation_order=2)
            _db.session.add(m)
            _db.session.commit()
            assert m.created_at is not None
            assert m.updated_at is not None


class TestTeamModel:
    def test_team_member_association(self, app, team_with_members):
        with app.app_context():
            team_id, m1_id, *_ = team_with_members
            team = _db.session.get(Team, team_id)
            assert len(team.members) == 2

    def test_team_app_association(self, app, team_with_members):
        with app.app_context():
            team_id, *_ = team_with_members
            team = _db.session.get(Team, team_id)
            assert len(team.apps) == 2


class TestAvailabilityModel:
    def test_create_availability(self, app, team_with_members):
        with app.app_context():
            _, m1_id, *_ = team_with_members
            avail = Availability(
                member_id=m1_id,
                week_start=date(2026, 4, 7),
                week_end=date(2026, 4, 14),
                reason=AvailabilityReason.vacation,
            )
            _db.session.add(avail)
            _db.session.commit()
            assert Availability.query.filter_by(member_id=m1_id).count() == 1

    def test_availability_reason_enum(self, app, team_with_members):
        with app.app_context():
            _, m1_id, *_ = team_with_members
            avail = Availability(
                member_id=m1_id,
                week_start=date(2026, 4, 7),
                week_end=date(2026, 4, 14),
                reason=AvailabilityReason.leave,
            )
            _db.session.add(avail)
            _db.session.commit()
            fetched = Availability.query.filter_by(member_id=m1_id).first()
            assert fetched.reason == AvailabilityReason.leave


class TestAssignmentModel:
    def test_week_normalized_to_monday(self, app, team_with_members):
        with app.app_context():
            team_id, m1_id, _, app_a_id, _ = team_with_members
            # Wednesday April 8 should normalize to Monday April 6
            a = Assignment(
                member_id=m1_id,
                app_id=app_a_id,
                team_id=team_id,
                week=date(2026, 4, 8),  # Wednesday
            )
            _db.session.add(a)
            _db.session.commit()
            fetched = Assignment.query.filter_by(member_id=m1_id).first()
            assert fetched.week == date(2026, 4, 6)  # Monday

    def test_unique_member_week_team_constraint(self, app, team_with_members):
        with app.app_context():
            team_id, m1_id, _, app_a_id, app_b_id = team_with_members
            week = date(2026, 4, 6)
            a1 = Assignment(member_id=m1_id, app_id=app_a_id, team_id=team_id, week=week)
            a2 = Assignment(member_id=m1_id, app_id=app_b_id, team_id=team_id, week=week)
            _db.session.add_all([a1, a2])
            with pytest.raises(IntegrityError):
                _db.session.commit()

    def test_different_members_same_week_allowed(self, app, team_with_members):
        with app.app_context():
            team_id, m1_id, m2_id, app_a_id, app_b_id = team_with_members
            week = date(2026, 4, 6)
            a1 = Assignment(member_id=m1_id, app_id=app_a_id, team_id=team_id, week=week)
            a2 = Assignment(member_id=m2_id, app_id=app_b_id, team_id=team_id, week=week)
            _db.session.add_all([a1, a2])
            _db.session.commit()
            assert Assignment.query.filter_by(team_id=team_id, week=week).count() == 2


class TestSeedCommand:
    def test_seed_creates_expected_records(self, app):
        with app.app_context():
            from app.commands import seed_db
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(seed_db, catch_exceptions=False)
            assert result.exit_code == 0
            assert "Seeded" in result.output
            assert Team.query.filter_by(name="Platform Team").count() == 1
            assert TriageApp.query.count() == 2
            assert Member.query.count() == 6

    def test_seed_idempotent(self, app):
        with app.app_context():
            from app.commands import seed_db
            from click.testing import CliRunner
            runner = CliRunner()
            runner.invoke(seed_db, catch_exceptions=False)
            result = runner.invoke(seed_db, catch_exceptions=False)
            assert "skipping" in result.output
            assert Team.query.filter_by(name="Platform Team").count() == 1
