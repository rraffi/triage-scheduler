from flask import Blueprint

admin = Blueprint("admin", __name__, url_prefix="/manage")

from app.admin import auth, routes  # noqa: E402, F401
