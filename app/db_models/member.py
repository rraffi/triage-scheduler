import uuid
from datetime import datetime, timezone

from app.extensions import db


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    rotation_order = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    availability = db.relationship("Availability", foreign_keys="Availability.member_id", back_populates="member")
    assignments = db.relationship("Assignment", back_populates="member")

    def __repr__(self):
        return f"<Member {self.name} order={self.rotation_order}>"
