"""Tests for the public-facing schedule dashboard."""
from __future__ import annotations

from datetime import date

import pytest

from app import create_app
from app.extensions import db as _db
from app.db_models import Assignment, Member, Team, TriageApp

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


class TestPublicDashboard:
    def test_index_returns_200(self, client, seeded):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_shows_app_names(self, client, seeded):
        r = client.get("/")
        assert b"App A" in r.data
        assert b"App B" in r.data

    def test_month_navigation_links_present(self, client, seeded):
        r = client.get("/?year=2026&month=4")
        assert r.status_code == 200
        # Prev (Mar) and Next (May) links exist
        assert b"Mar" in r.data
        assert b"May" in r.data

    def test_no_forms_or_action_buttons(self, client, seeded):
        r = client.get("/")
        assert b'<form' not in r.data
        assert b'<button' not in r.data

    def test_hero_shows_persisted_assignments(self, client, seeded, app):
        with app.app_context():
            team = Team.query.filter_by(name="Platform Team").first()
            app_a = TriageApp.query.filter_by(name="App A").first()
            app_b = TriageApp.query.filter_by(name="App B").first()
            alice = Member.query.filter_by(name="Alice").first()
            bob = Member.query.filter_by(name="Bob").first()
            _db.session.add_all([
                Assignment(member_id=alice.id, app_id=app_a.id,
                           team_id=team.id, week=MONDAY, is_substitute=False),
                Assignment(member_id=bob.id, app_id=app_b.id,
                           team_id=team.id, week=MONDAY, is_substitute=False),
            ])
            _db.session.commit()
        r = client.get(f"/?year={MONDAY.year}&month={MONDAY.month}")
        assert b"Alice" in r.data
        assert b"Bob" in r.data

    def test_no_admin_nav_links_for_unauthenticated(self, client, seeded):
        r = client.get("/")
        assert b"Roster" not in r.data
        assert b"Availability" not in r.data
