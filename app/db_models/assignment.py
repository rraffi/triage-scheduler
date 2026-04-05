import uuid
from datetime import datetime, timezone, date, timedelta

from app.extensions import db


def _to_monday(d: date) -> date:
    """Normalize a date to the Monday of its week."""
    return d - timedelta(days=d.weekday())


class Assignment(db.Model):
    __tablename__ = "assignments"
    __table_args__ = (
        db.UniqueConstraint("member_id", "week", "team_id", name="uq_assignment_member_week_team"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey("members.id"), nullable=False)
    app_id = db.Column(db.String(36), db.ForeignKey("apps.id"), nullable=False)
    team_id = db.Column(db.String(36), db.ForeignKey("teams.id"), nullable=False)
    week = db.Column(db.Date, nullable=False)
    is_substitute = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    member = db.relationship("Member", back_populates="assignments")
    triage_app = db.relationship("TriageApp", back_populates="assignments")
    team = db.relationship("Team", back_populates="assignments")

    def __init__(self, **kwargs):
        if "week" in kwargs and isinstance(kwargs["week"], date):
            kwargs["week"] = _to_monday(kwargs["week"])
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Assignment member={self.member_id} app={self.app_id} week={self.week}>"
