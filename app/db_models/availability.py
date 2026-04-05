import enum
import uuid

from app.extensions import db


class AvailabilityReason(enum.Enum):
    vacation = "vacation"
    leave = "leave"
    other = "other"


class Availability(db.Model):
    __tablename__ = "availability"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey("members.id"), nullable=False)
    week_start = db.Column(db.Date, nullable=False)
    week_end = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Enum(AvailabilityReason), nullable=False, default=AvailabilityReason.vacation)
    created_by = db.Column(db.String(36), db.ForeignKey("members.id"), nullable=True)

    member = db.relationship("Member", foreign_keys=[member_id], back_populates="availability")
    creator = db.relationship("Member", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Availability member={self.member_id} {self.week_start}–{self.week_end}>"
