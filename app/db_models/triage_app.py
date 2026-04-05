import uuid

from app.extensions import db


class TriageApp(db.Model):
    __tablename__ = "apps"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    assignments = db.relationship("Assignment", back_populates="triage_app")

    def __repr__(self):
        return f"<TriageApp {self.name}>"
