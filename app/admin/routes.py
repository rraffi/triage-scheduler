import calendar
from datetime import date, timedelta

from flask import flash, redirect, render_template, request, url_for

from app.admin import admin
from app.admin.auth import admin_required
from app.db_models import Availability, Assignment, Member, ScheduleState, Team, TriageApp
from app.db_models.availability import AvailabilityReason
from app.extensions import db
from app.services.scheduler_service import run_week


def _get_team():
    return Team.query.filter_by(name="Platform Team").first()


def _next_monday():
    today = date.today()
    days = (7 - today.weekday()) % 7
    return today + timedelta(days=days if days else 7)


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #

@admin.route("/")
@admin_required
def dashboard():
    return redirect(url_for("admin.roster"))


# --------------------------------------------------------------------------- #
# Roster
# --------------------------------------------------------------------------- #

@admin.route("/roster")
@admin_required
def roster():
    team = _get_team()
    members = (
        Member.query
        .join(Member.teams)
        .filter(Team.id == team.id)
        .order_by(Member.rotation_order)
        .all()
        if team else []
    )
    return render_template("admin/roster.html", members=members, team=team)


@admin.route("/roster/add", methods=["POST"])
@admin_required
def roster_add():
    team = _get_team()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not email:
        flash("Name and email are required.", "danger")
        return redirect(url_for("admin.roster"))

    if Member.query.filter_by(email=email).first():
        flash(f"Email {email} already exists.", "danger")
        return redirect(url_for("admin.roster"))

    max_order = max((m.rotation_order for m in team.members), default=-1)
    member = Member(name=name, email=email, rotation_order=max_order + 1)
    db.session.add(member)
    team.members.append(member)
    db.session.commit()
    flash(f"Added {name} at rotation position {max_order + 1}.", "success")
    return redirect(url_for("admin.roster"))


@admin.route("/roster/<member_id>/deactivate", methods=["POST"])
@admin_required
def roster_deactivate(member_id):
    member = db.session.get(Member, member_id)
    if member:
        member.is_active = False
        db.session.commit()
        flash(f"{member.name} deactivated.", "warning")
    return redirect(url_for("admin.roster"))


@admin.route("/roster/<member_id>/reactivate", methods=["POST"])
@admin_required
def roster_reactivate(member_id):
    member = db.session.get(Member, member_id)
    if member:
        member.is_active = True
        db.session.commit()
        flash(f"{member.name} reactivated.", "success")
    return redirect(url_for("admin.roster"))


@admin.route("/roster/<member_id>/reorder", methods=["POST"])
@admin_required
def roster_reorder(member_id):
    team = _get_team()
    member = db.session.get(Member, member_id)
    try:
        new_order = int(request.form.get("rotation_order", ""))
    except ValueError:
        flash("Invalid rotation order.", "danger")
        return redirect(url_for("admin.roster"))

    conflict = next(
        (m for m in team.members if m.rotation_order == new_order and m.id != member_id),
        None,
    )
    if conflict:
        flash(f"Rotation order {new_order} already taken by {conflict.name}.", "danger")
        return redirect(url_for("admin.roster"))

    member.rotation_order = new_order
    db.session.commit()
    flash(f"{member.name} moved to position {new_order}.", "success")
    return redirect(url_for("admin.roster"))


# --------------------------------------------------------------------------- #
# Apps
# --------------------------------------------------------------------------- #

@admin.route("/apps")
@admin_required
def apps():
    team = _get_team()
    triage_apps = (
        TriageApp.query
        .join(TriageApp.teams)
        .filter(Team.id == team.id)
        .order_by(TriageApp.sort_order)
        .all()
        if team else []
    )
    return render_template("admin/apps.html", apps=triage_apps, team=team)


@admin.route("/apps/add", methods=["POST"])
@admin_required
def apps_add():
    team = _get_team()
    name = request.form.get("name", "").strip()
    if not name:
        flash("App name is required.", "danger")
        return redirect(url_for("admin.apps"))

    if TriageApp.query.filter_by(name=name).first():
        flash(f"App '{name}' already exists.", "danger")
        return redirect(url_for("admin.apps"))

    max_order = max((a.sort_order for a in team.apps), default=-1)
    triage_app = TriageApp(name=name, sort_order=max_order + 1)
    db.session.add(triage_app)
    team.apps.append(triage_app)
    db.session.commit()
    flash(f"Added app '{name}'.", "success")
    return redirect(url_for("admin.apps"))


@admin.route("/apps/<app_id>/delete", methods=["POST"])
@admin_required
def apps_delete(app_id):
    triage_app = db.session.get(TriageApp, app_id)
    if triage_app:
        db.session.delete(triage_app)
        db.session.commit()
        flash(f"Deleted app '{triage_app.name}'.", "warning")
    return redirect(url_for("admin.apps"))


@admin.route("/apps/<app_id>/reorder", methods=["POST"])
@admin_required
def apps_reorder(app_id):
    team = _get_team()
    triage_app = db.session.get(TriageApp, app_id)
    try:
        new_order = int(request.form.get("sort_order", ""))
    except ValueError:
        flash("Invalid sort order.", "danger")
        return redirect(url_for("admin.apps"))

    conflict = next(
        (a for a in team.apps if a.sort_order == new_order and a.id != app_id),
        None,
    )
    if conflict:
        flash(f"Sort order {new_order} already taken by '{conflict.name}'.", "danger")
        return redirect(url_for("admin.apps"))

    triage_app.sort_order = new_order
    db.session.commit()
    flash(f"'{triage_app.name}' moved to sort order {new_order}.", "success")
    return redirect(url_for("admin.apps"))


# --------------------------------------------------------------------------- #
# Availability
# --------------------------------------------------------------------------- #

@admin.route("/availability")
@admin_required
def availability():
    team = _get_team()
    members = (
        Member.query
        .join(Member.teams)
        .filter(Team.id == team.id)
        .order_by(Member.rotation_order)
        .all()
        if team else []
    )
    blocks = (
        Availability.query
        .filter(Availability.member_id.in_([m.id for m in members]))
        .order_by(Availability.week_start)
        .all()
        if members else []
    )
    return render_template(
        "admin/availability.html",
        members=members,
        blocks=blocks,
        reasons=AvailabilityReason,
    )


@admin.route("/availability/add", methods=["POST"])
@admin_required
def availability_add():
    member_id = request.form.get("member_id")
    week_start_str = request.form.get("week_start")
    week_end_str = request.form.get("week_end")
    reason_str = request.form.get("reason", "vacation")

    try:
        week_start = date.fromisoformat(week_start_str)
        week_end = date.fromisoformat(week_end_str)
    except (ValueError, TypeError):
        flash("Invalid dates.", "danger")
        return redirect(url_for("admin.availability"))

    if week_start.weekday() != 0:
        flash("Start date must be a Monday.", "danger")
        return redirect(url_for("admin.availability"))

    if week_end.weekday() != 0:
        flash("End date must be a Monday.", "danger")
        return redirect(url_for("admin.availability"))

    if week_end <= week_start:
        flash("End date must be after start date.", "danger")
        return redirect(url_for("admin.availability"))

    try:
        reason = AvailabilityReason[reason_str]
    except KeyError:
        reason = AvailabilityReason.vacation

    block = Availability(
        member_id=member_id,
        week_start=week_start,
        week_end=week_end,
        reason=reason,
    )
    db.session.add(block)
    db.session.commit()
    flash("Availability block added.", "success")
    return redirect(url_for("admin.availability"))


@admin.route("/availability/<block_id>/delete", methods=["POST"])
@admin_required
def availability_delete(block_id):
    block = db.session.get(Availability, block_id)
    if block:
        db.session.delete(block)
        db.session.commit()
        flash("Availability block removed.", "success")
    return redirect(url_for("admin.availability"))


# Bootstrap color cycle for apps (by sort_order index)
APP_COLORS = ["primary", "success", "warning", "danger", "info", "secondary"]


def _build_calendar(team, year, month):
    """Return list of week dicts for the calendar view covering the given month."""
    from app.services.scheduler_service import (
        _load_domain_objects,
        _orm_state_to_domain,
    )
    from src.scheduler import build_initial_state, compute_week as _compute_week

    # Find all Mondays that overlap the month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    # Start from the Monday of the first week
    start_monday = first_day - timedelta(days=first_day.weekday())
    # End on the Monday of the last week
    end_monday = last_day - timedelta(days=last_day.weekday())

    mondays = []
    d = start_monday
    while d <= end_monday:
        mondays.append(d)
        d += timedelta(weeks=1)

    # Load persisted assignments for this date range
    persisted = {}
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
                "app": a.triage_app.name,
                "app_index": a.triage_app.sort_order,
                "sub": a.is_substitute,
            })

    # Build preview state starting from first unscheduled Monday
    today = date.today()
    future_mondays = [m for m in mondays if m not in persisted and m >= today]

    preview = {}
    if team and future_mondays:
        try:
            first_future = future_mondays[0]
            domain_members, domain_apps, _, _ = _load_domain_objects(team, first_future)
            orm_state = team.schedule_state
            domain_state = (
                _orm_state_to_domain(orm_state, domain_members, domain_apps)
                if orm_state else build_initial_state(domain_members, domain_apps)
            )
            # Build app_index lookup
            app_index = {a.name: i for i, a in enumerate(sorted(team.apps, key=lambda x: x.sort_order))}
            for monday in future_mondays:
                dm, da, _, _ = _load_domain_objects(team, monday)
                domain_state.members = dm
                domain_state.apps = da
                week_assignments = _compute_week(domain_state)
                preview[monday] = [
                    {
                        "member": a.member.name,
                        "app": a.app.name,
                        "app_index": app_index.get(a.app.name, 0),
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


def _delete_week(team, target_week):
    """Delete all assignments for target_week and rewind schedule state."""
    from app.db_models.assignment import _to_monday
    from app.services.scheduler_service import _domain_state_to_orm
    from src.scheduler import build_initial_state, compute_week as _compute_week
    from app.services.scheduler_service import _load_domain_objects, _orm_state_to_domain

    target_week = _to_monday(target_week)

    deleted = (
        Assignment.query
        .filter_by(team_id=team.id, week=target_week)
        .all()
    )
    if not deleted:
        flash(f"No assignments found for week of {target_week}.", "warning")
        return

    for a in deleted:
        db.session.delete(a)

    # Rewind state: replay all remaining persisted weeks from scratch
    remaining = (
        Assignment.query
        .filter(Assignment.team_id == team.id, Assignment.week != target_week)
        .with_entities(Assignment.week)
        .distinct()
        .order_by(Assignment.week)
        .all()
    )
    remaining_weeks = [r.week for r in remaining]

    orm_state = team.schedule_state
    if not remaining_weeks:
        # Nothing left — reset state entirely
        if orm_state:
            orm_state.current_week = 0
            orm_state.pointer_positions = {}
            orm_state.pointer_held = {}
            orm_state.label_rotation_offset = 0
            orm_state.last_assignments = {}
    else:
        # Replay through all remaining weeks to reconstruct pointer state
        first = remaining_weeks[0]
        dm, da, _, _ = _load_domain_objects(team, first)
        domain_state = build_initial_state(dm, da)
        for w in remaining_weeks:
            dm, da, _, _ = _load_domain_objects(team, w)
            domain_state.members = dm
            domain_state.apps = da
            _compute_week(domain_state)
        _domain_state_to_orm(domain_state, orm_state)

    db.session.commit()
    flash(f"Deleted assignments for week of {target_week}. State rewound.", "warning")


# --------------------------------------------------------------------------- #
# Schedule
# --------------------------------------------------------------------------- #

@admin.route("/schedule", methods=["GET", "POST"])
@admin_required
def schedule():
    team = _get_team()
    today = date.today()

    # Month navigation
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        # clamp to valid range
        month = max(1, min(12, month))
    except ValueError:
        year, month = today.year, today.month

    if request.method == "POST":
        action = request.form.get("action")
        week_str = request.form.get("week")
        try:
            target = date.fromisoformat(week_str)
        except (ValueError, TypeError):
            target = _next_monday()

        if action == "run":
            try:
                assignments = run_week(team.id, target)
                flash(
                    f"Scheduled week of {target}: "
                    + ", ".join(f"{a.member.name} → {a.triage_app.name}" for a in assignments),
                    "success",
                )
            except ValueError as e:
                flash(str(e), "danger")

        elif action == "delete":
            _delete_week(team, target)

        return redirect(url_for("admin.schedule", year=year, month=month))

    weeks = _build_calendar(team, year, month)

    # Prev / next month
    prev_month = date(year, month, 1) - timedelta(days=1)
    next_month = date(year, month, calendar.monthrange(year, month)[1]) + timedelta(days=1)

    # App color map for legend
    app_colors = {}
    if team:
        for i, a in enumerate(sorted(team.apps, key=lambda x: x.sort_order)):
            app_colors[a.name] = APP_COLORS[i % len(APP_COLORS)]

    state = team.schedule_state if team else None
    return render_template(
        "admin/schedule.html",
        weeks=weeks,
        year=year,
        month=month,
        month_name=date(year, month, 1).strftime("%B %Y"),
        prev_month=prev_month,
        next_month=next_month,
        app_colors=app_colors,
        app_color_list=APP_COLORS,
        next_week=_next_monday(),
        state=state,
        today=today,
    )
