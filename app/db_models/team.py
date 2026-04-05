import uuid

from app.extensions import db

team_members = db.Table(
    "team_members",
    db.Column("team_id", db.String(36), db.ForeignKey("teams.id"), primary_key=True),
    db.Column("member_id", db.String(36), db.ForeignKey("members.id"), primary_key=True),
)

team_apps = db.Table(
    "team_apps",
    db.Column("team_id", db.String(36), db.ForeignKey("teams.id"), primary_key=True),
    db.Column("app_id", db.String(36), db.ForeignKey("apps.id"), primary_key=True),
)


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)

    members = db.relationship("Member", secondary=team_members, backref="teams")
    apps = db.relationship("TriageApp", secondary=team_apps, backref="teams")
    assignments = db.relationship("Assignment", back_populates="team")
    schedule_state = db.relationship("ScheduleState", back_populates="team", uselist=False)

    def __repr__(self):
        return f"<Team {self.name}>"
