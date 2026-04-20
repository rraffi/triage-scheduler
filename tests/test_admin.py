import pytest
from datetime import date, timedelta

from app import create_app
from app.extensions import db as _db
from app.db_models import Member, TriageApp, Team, Availability, Assignment

MONDAY = date(2026, 4, 6)


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    app.config["ADMIN_PASSWORD"] = "testpass"
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
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/manage/login", data={"password": "testpass"})
    return client


@pytest.fixture
def seeded(app):
    with app.app_context():
        app_a = TriageApp(name="App A", sort_order=0)
        app_b = TriageApp(name="App B", sort_order=1)
        members = [
            Member(name=n, email=f"{n.lower()}@example.com", rotation_order=i)
            for i, n in enumerate(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"])
        ]
        team = Team(name="Platform Team", members=members, apps=[app_a, app_b])
        _db.session.add_all([app_a, app_b, *members, team])
        _db.session.commit()
        return team.id


class TestAuth:
    def test_unauthenticated_redirects_to_login(self, client, seeded):
        r = client.get("/manage/roster")
        assert r.status_code == 302
        assert "/manage/login" in r.headers["Location"]

    def test_wrong_password_rejected(self, client):
        r = client.post("/manage/login", data={"password": "wrong"})
        assert b"Invalid password" in r.data

    def test_correct_password_sets_session(self, client):
        r = client.post("/manage/login", data={"password": "testpass"},
                        follow_redirects=True)
        assert r.status_code == 200

    def test_logout_clears_session(self, auth_client, seeded):
        auth_client.get("/manage/logout")
        r = auth_client.get("/manage/roster")
        assert r.status_code == 302


class TestRoster:
    def test_roster_lists_members(self, auth_client, seeded):
        r = auth_client.get("/manage/roster")
        assert r.status_code == 200
        assert b"Alice" in r.data

    def test_add_member(self, auth_client, seeded, app):
        auth_client.post("/manage/roster/add", data={
            "name": "Grace", "email": "grace@example.com"
        })
        with app.app_context():
            assert Member.query.filter_by(email="grace@example.com").count() == 1

    def test_add_duplicate_email_rejected(self, auth_client, seeded):
        r = auth_client.post("/manage/roster/add", data={
            "name": "Dup", "email": "alice@example.com"
        }, follow_redirects=True)
        assert b"already exists" in r.data

    def test_deactivate_member(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            alice_id = alice.id
        auth_client.post(f"/manage/roster/{alice_id}/deactivate")
        with app.app_context():
            assert _db.session.get(Member, alice_id).is_active is False

    def test_reorder_blocked_when_assignments_exist(self, auth_client, seeded, app):
        with app.app_context():
            team = Team.query.filter_by(name="Platform Team").first()
            charlie = Member.query.filter_by(name="Charlie").first()
            alice = Member.query.filter_by(name="Alice").first()
            app_a = TriageApp.query.filter_by(name="App A").first()
            _db.session.add(Assignment(
                member_id=alice.id, app_id=app_a.id,
                team_id=team.id, week=MONDAY, is_substitute=False,
            ))
            _db.session.commit()
            charlie_id = charlie.id
        r = auth_client.post(f"/manage/roster/{charlie_id}/reorder",
                             data={"rotation_order": 0},
                             follow_redirects=True)
        assert b"Delete all scheduled weeks" in r.data

    def test_reorder_conflict_rejected(self, auth_client, seeded, app):
        with app.app_context():
            charlie = Member.query.filter_by(name="Charlie").first()
            charlie_id = charlie.id
        r = auth_client.post(f"/manage/roster/{charlie_id}/reorder",
                             data={"rotation_order": 0},
                             follow_redirects=True)
        assert b"already taken" in r.data


class TestApps:
    def test_apps_page_renders(self, auth_client, seeded):
        r = auth_client.get("/manage/apps")
        assert r.status_code == 200
        assert b"App A" in r.data

    def test_add_app(self, auth_client, seeded, app):
        auth_client.post("/manage/apps/add", data={"name": "App C"})
        with app.app_context():
            assert TriageApp.query.filter_by(name="App C").count() == 1

    def test_add_duplicate_app_rejected(self, auth_client, seeded):
        r = auth_client.post("/manage/apps/add", data={"name": "App A"},
                             follow_redirects=True)
        assert b"already exists" in r.data

    def test_delete_app(self, auth_client, seeded, app):
        with app.app_context():
            app_b = TriageApp.query.filter_by(name="App B").first()
            app_b_id = app_b.id
        auth_client.post(f"/manage/apps/{app_b_id}/delete")
        with app.app_context():
            assert _db.session.get(TriageApp, app_b_id) is None


class TestAvailability:
    def test_availability_page_renders(self, auth_client, seeded):
        r = auth_client.get("/manage/availability")
        assert r.status_code == 200

    def test_add_availability_block(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            alice_id = alice.id
        auth_client.post("/manage/availability/add", data={
            "member_id": alice_id,
            "week_start": "2026-04-13",
            "week_end": "2026-04-20",
            "reason": "vacation",
        })
        with app.app_context():
            assert Availability.query.filter_by(member_id=alice_id).count() == 1

    def test_invalid_dates_rejected(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            alice_id = alice.id
        r = auth_client.post("/manage/availability/add", data={
            "member_id": alice_id,
            "week_start": "2026-04-20",
            "week_end": "2026-04-13",  # end before start
            "reason": "vacation",
        }, follow_redirects=True)
        assert b"End date must be after" in r.data

    def test_non_monday_start_rejected(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            alice_id = alice.id
        r = auth_client.post("/manage/availability/add", data={
            "member_id": alice_id,
            "week_start": "2026-04-15",  # Wednesday
            "week_end": "2026-04-20",    # Monday
            "reason": "vacation",
        }, follow_redirects=True)
        assert b"must be a Monday" in r.data

    def test_non_monday_end_rejected(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            alice_id = alice.id
        r = auth_client.post("/manage/availability/add", data={
            "member_id": alice_id,
            "week_start": "2026-04-13",  # Monday
            "week_end": "2026-04-17",    # Friday
            "reason": "vacation",
        }, follow_redirects=True)
        assert b"must be a Monday" in r.data

    def test_delete_availability_block(self, auth_client, seeded, app):
        with app.app_context():
            alice = Member.query.filter_by(name="Alice").first()
            block = Availability(
                member_id=alice.id,
                week_start=date(2026, 4, 13),
                week_end=date(2026, 4, 20),
            )
            _db.session.add(block)
            _db.session.commit()
            block_id = block.id
        auth_client.post(f"/manage/availability/{block_id}/delete")
        with app.app_context():
            assert _db.session.get(Availability, block_id) is None


class TestSchedule:
    def test_schedule_page_renders(self, auth_client, seeded):
        r = auth_client.get("/manage/schedule")
        assert r.status_code == 200
        assert b"Schedule" in r.data
        assert b"App A" in r.data

    def test_run_week_persists_assignments(self, auth_client, seeded, app):
        r = auth_client.post("/manage/schedule", data={
            "action": "run",
            "week": str(MONDAY),
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            assert Assignment.query.filter_by(week=MONDAY).count() == 2

    def test_duplicate_run_shows_error(self, auth_client, seeded, app):
        auth_client.post("/manage/schedule", data={"action": "run", "week": str(MONDAY)})
        r = auth_client.post("/manage/schedule", data={"action": "run", "week": str(MONDAY)},
                             follow_redirects=True)
        assert b"already scheduled" in r.data
