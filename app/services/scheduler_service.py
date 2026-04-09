import calendar as _calendar
from datetime import date, timedelta

from app.db_models import Member, TriageApp, Availability, Assignment, ScheduleState, Team
from app.db_models.assignment import _to_monday
from app.extensions import db
from src.models import (
    Member as DomainMember,
    App as DomainApp,
    PointerState,
    ScheduleState as DomainScheduleState,
)
from src.scheduler import build_initial_state, compute_week


def _is_available(member_id: str, target_week: date) -> bool:
    """Return False if member has any availability block covering target_week."""
    return not Availability.query.filter(
        Availability.member_id == member_id,
        Availability.week_start <= target_week,
        Availability.week_end > target_week,
    ).first()


def _load_domain_objects(team: Team, target_week: date):
    """Return (domain_members, domain_apps, orm_app_map) for the given team and week."""
    orm_members = sorted(
        [m for m in team.members if m.is_active],
        key=lambda m: m.rotation_order,
    )
    orm_apps = sorted(team.apps, key=lambda a: a.sort_order)

    domain_members = [
        DomainMember(
            name=m.name,
            rotation_order=m.rotation_order,
            is_available=_is_available(m.id, target_week),
        )
        for m in orm_members
    ]
    domain_apps = [
        DomainApp(name=a.name, id=i)
        for i, a in enumerate(orm_apps)
    ]

    # Maps for reverse lookup when persisting
    member_id_by_name = {m.name: m.id for m in orm_members}
    app_id_by_name = {a.name: a.id for a in orm_apps}

    return domain_members, domain_apps, member_id_by_name, app_id_by_name


def _orm_state_to_domain(
    orm_state: ScheduleState,
    domain_members: list[DomainMember],
    domain_apps: list[DomainApp],
) -> DomainScheduleState:
    pointers = [
        PointerState(
            pointer_id=int(ptr_id),
            position=pos,
            held=orm_state.pointer_held.get(ptr_id, False),
        )
        for ptr_id, pos in orm_state.pointer_positions.items()
    ]
    return DomainScheduleState(
        members=domain_members,
        apps=domain_apps,
        pointers=pointers,
        week=orm_state.current_week,
        last_assignments=orm_state.last_assignments,
        label_rotation_offset=orm_state.label_rotation_offset,
    )


def _domain_state_to_orm(domain_state: DomainScheduleState, orm_state: ScheduleState) -> None:
    orm_state.pointer_positions = {
        str(p.pointer_id): p.position for p in domain_state.pointers
    }
    orm_state.pointer_held = {
        str(p.pointer_id): p.held for p in domain_state.pointers
    }
    orm_state.label_rotation_offset = domain_state.label_rotation_offset
    orm_state.last_assignments = domain_state.last_assignments
    orm_state.current_week = domain_state.week


def run_week(team_id: str, target_week: date, dry_run: bool = False) -> list:
    """
    Run one week of scheduling for the given team.

    Returns list of domain Assignment objects (dry_run) or ORM Assignment objects (persisted).
    Raises ValueError if this week has already been scheduled.
    """
    target_week = _to_monday(target_week)

    team = db.session.get(Team, team_id)
    if team is None:
        raise ValueError(f"Team {team_id!r} not found")

    if not dry_run:
        existing = Assignment.query.filter_by(team_id=team_id, week=target_week).first()
        if existing:
            raise ValueError(f"Week {target_week} already scheduled for this team")

    domain_members, domain_apps, member_id_by_name, app_id_by_name = _load_domain_objects(
        team, target_week
    )

    orm_state = team.schedule_state
    if orm_state is None:
        domain_state = build_initial_state(domain_members, domain_apps)
    else:
        domain_state = _orm_state_to_domain(orm_state, domain_members, domain_apps)

    domain_assignments = compute_week(domain_state)

    if dry_run:
        return domain_assignments

    # Persist assignments
    orm_assignments = []
    for da in domain_assignments:
        orm_a = Assignment(
            member_id=member_id_by_name[da.member.name],
            app_id=app_id_by_name[da.app.name],
            team_id=team_id,
            week=target_week,
            is_substitute=da.is_substitute,
        )
        db.session.add(orm_a)
        orm_assignments.append(orm_a)

    # Persist state
    if orm_state is None:
        orm_state = ScheduleState(team_id=team_id)
        db.session.add(orm_state)
    _domain_state_to_orm(domain_state, orm_state)

    db.session.commit()
    return orm_assignments


def build_calendar(team, year: int, month: int) -> list[dict]:
    """
    Return a list of week dicts covering the given month.

    Each dict:
        monday        : date  — Monday of the week
        in_month      : bool  — week overlaps the requested month
        persisted     : bool  — assignments are finalized in DB
        assignments   : list of {member, member_email, app, app_index, sub}

    app_index is the app's sort_order; color mapping is left to the UI layer.
    """
    first_day = date(year, month, 1)
    last_day = date(year, month, _calendar.monthrange(year, month)[1])
    start_monday = first_day - timedelta(days=first_day.weekday())
    end_monday = last_day - timedelta(days=last_day.weekday())

    mondays: list[date] = []
    d = start_monday
    while d <= end_monday:
        mondays.append(d)
        d += timedelta(weeks=1)

    # Persisted assignments from DB
    persisted: dict[date, list] = {}
    if team:
        rows = (
            Assignment.query
            .filter(
                Assignment.team_id == team.id,
                Assignment.week >= start_monday,
                Assignment.week <= end_monday,
            )
            .all()
        )
        for a in rows:
            persisted.setdefault(a.week, []).append({
                "member": a.member.name,
                "member_email": a.member.email,
                "app": a.triage_app.name,
                "app_index": a.triage_app.sort_order,
                "sub": a.is_substitute,
            })

    # Preview: dry-run for future unscheduled weeks
    today = date.today()
    future_mondays = [m for m in mondays if m not in persisted and m >= today]
    preview: dict[date, list] = {}

    if team and future_mondays:
        member_email = {m.name: m.email for m in team.members}
        app_index_map = {
            a.name: a.sort_order
            for a in team.apps
        }
        try:
            first_future = future_mondays[0]
            dm, da, _, _ = _load_domain_objects(team, first_future)
            orm_state = team.schedule_state
            domain_state = (
                _orm_state_to_domain(orm_state, dm, da)
                if orm_state else build_initial_state(dm, da)
            )
            for monday in future_mondays:
                dm, da, _, _ = _load_domain_objects(team, monday)
                domain_state.members = dm
                domain_state.apps = da
                week_assignments = compute_week(domain_state)
                preview[monday] = [
                    {
                        "member": a.member.name,
                        "member_email": member_email.get(a.member.name, ""),
                        "app": a.app.name,
                        "app_index": app_index_map.get(a.app.name, 0),
                        "sub": a.is_substitute,
                    }
                    for a in week_assignments
                ]
        except Exception:
            pass

    weeks = []
    for monday in mondays:
        in_month = monday.month == month or (monday + timedelta(days=6)).month == month
        weeks.append({
            "monday": monday,
            "in_month": in_month,
            "persisted": monday in persisted,
            "assignments": persisted.get(monday) or preview.get(monday) or [],
        })
    return weeks
