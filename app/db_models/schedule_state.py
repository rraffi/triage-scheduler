from app.extensions import db


class ScheduleState(db.Model):
    __tablename__ = "schedule_state"

    team_id = db.Column(db.String(36), db.ForeignKey("teams.id"), primary_key=True)
    pointer_positions = db.Column(db.JSON, nullable=False, default=dict)
    pointer_held = db.Column(db.JSON, nullable=False, default=dict)
    label_rotation_offset = db.Column(db.Integer, nullable=False, default=0)
    last_assignments = db.Column(db.JSON, nullable=False, default=dict)
    current_week = db.Column(db.Integer, nullable=False, default=0)

    team = db.relationship("Team", back_populates="schedule_state")

    def __repr__(self):
        return f"<ScheduleState team={self.team_id} week={self.current_week}>"
