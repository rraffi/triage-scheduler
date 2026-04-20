import calendar
from datetime import date, timedelta

from flask import render_template, request

from app.db_models import Team
from app.main import main
from app.services.scheduler_service import build_calendar

APP_COLORS = ["primary", "success", "warning", "danger", "info", "secondary"]


def _get_team():
    return Team.query.filter_by(name="Platform Team").first()


def _app_color_map(team):
    if not team:
        return {}
    return {
        a.name: APP_COLORS[i % len(APP_COLORS)]
        for i, a in enumerate(sorted(team.apps, key=lambda x: x.sort_order))
    }


@main.route("/")
def index():
    team = _get_team()
    today = date.today()

    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        month = max(1, min(12, month))
    except ValueError:
        year, month = today.year, today.month

    weeks = build_calendar(team, year, month)

    # Current-week hero: find today's Monday in weeks list
    this_monday = today - timedelta(days=today.weekday())
    hero = next((w for w in weeks if w["monday"] == this_monday), None)
    # If this month doesn't contain today, run a separate lookup
    if hero is None:
        hero_weeks = build_calendar(team, today.year, today.month)
        hero = next((w for w in hero_weeks if w["monday"] == this_monday), None)

    # Attach color to each assignment and precompute day cells
    app_colors = _app_color_map(team)
    for w in weeks:
        for a in w["assignments"]:
            a["color"] = app_colors.get(a["app"], "secondary")
        # 7 day objects for this week (Mon-Sun)
        w["days"] = [w["monday"] + timedelta(days=i) for i in range(7)]
        w["is_today_week"] = w["monday"] <= today < w["monday"] + timedelta(days=7)
    if hero:
        for a in hero["assignments"]:
            a["color"] = app_colors.get(a["app"], "secondary")

    prev_month = date(year, month, 1) - timedelta(days=1)
    next_month = date(year, month, calendar.monthrange(year, month)[1]) + timedelta(days=1)

    return render_template(
        "schedule.html",
        weeks=weeks,
        hero=hero,
        year=year,
        month=month,
        month_name=date(year, month, 1).strftime("%B %Y"),
        prev_month=prev_month,
        next_month=next_month,
        today=today,
        app_colors=app_colors,
    )
