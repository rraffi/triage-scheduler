import click
from flask.cli import with_appcontext

from app.extensions import db
from app.db_models import Member, TriageApp, Team


@click.command("seed-db")
@with_appcontext
def seed_db():
    """Seed the database with a default team, apps, and members."""
    if Team.query.filter_by(name="Platform Team").first():
        click.echo("Already seeded, skipping.")
        return

    app_a = TriageApp(name="App A", sort_order=0)
    app_b = TriageApp(name="App B", sort_order=1)
    db.session.add_all([app_a, app_b])

    member_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    members = [
        Member(
            name=name,
            email=f"{name.lower()}@example.com",
            rotation_order=i,
        )
        for i, name in enumerate(member_names)
    ]
    db.session.add_all(members)

    team = Team(name="Platform Team", members=members, apps=[app_a, app_b])
    db.session.add(team)

    db.session.commit()
    click.echo(f"Seeded: 1 team, 2 apps, {len(members)} members.")
