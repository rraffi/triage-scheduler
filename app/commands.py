from datetime import date, timedelta

import click
from flask.cli import with_appcontext

from app.db_models import Member, TriageApp, Team
from app.extensions import db
from app.services.scheduler_service import run_week


def _next_monday(ref: date | None = None) -> date:
    d = ref or date.today()
    days_ahead = (7 - d.weekday()) % 7
    return d + timedelta(days=days_ahead if days_ahead else 7)


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


@click.command("schedule-week")
@click.option(
    "--week",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Monday of the week to schedule (default: next Monday).",
)
@with_appcontext
def schedule_week(week):
    """Run one week of scheduling and persist assignments."""
    target = week.date() if week else _next_monday()

    team = Team.query.filter_by(name="Platform Team").first()
    if team is None:
        click.echo("No team found. Run 'flask seed-db' first.", err=True)
        raise SystemExit(1)

    try:
        assignments = run_week(team.id, target)
    except ValueError as e:
        click.echo(str(e), err=True)
        raise SystemExit(1)

    click.echo(f"Week of {target}:")
    for a in assignments:
        click.echo(f"  {a.member.name} → {a.triage_app.name}")


@click.command("schedule-preview")
@click.option("--weeks", default=4, show_default=True, help="Number of weeks to preview.")
@click.option(
    "--start",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Start Monday (default: next Monday).",
)
@with_appcontext
def schedule_preview(weeks, start):
    """Dry-run schedule for upcoming weeks without persisting."""
    from app.db_models.assignment import _to_monday
    from app.services.scheduler_service import (
        _load_domain_objects,
        _orm_state_to_domain,
        _domain_state_to_orm,
    )
    from src.scheduler import build_initial_state, compute_week
    from src.models import ScheduleState as DomainScheduleState
    from app.db_models import ScheduleState

    target = _to_monday(start.date() if start else _next_monday())

    team = Team.query.filter_by(name="Platform Team").first()
    if team is None:
        click.echo("No team found. Run 'flask seed-db' first.", err=True)
        raise SystemExit(1)

    # Build a throw-away copy of state for preview
    domain_members, domain_apps, _, _ = _load_domain_objects(team, target)
    orm_state = team.schedule_state
    if orm_state is None:
        domain_state = build_initial_state(domain_members, domain_apps)
    else:
        domain_state = _orm_state_to_domain(orm_state, domain_members, domain_apps)

    for i in range(weeks):
        week_date = target + timedelta(weeks=i)
        # Refresh availability for each week
        domain_members, domain_apps, _, _ = _load_domain_objects(team, week_date)
        domain_state.members = domain_members
        domain_state.apps = domain_apps

        assignments = compute_week(domain_state)
        click.echo(f"Week of {week_date}:")
        for a in assignments:
            sub = " (sub)" if a.is_substitute else ""
            click.echo(f"  {a.member.name} → {a.app.name}{sub}")
