from flask import redirect, url_for

from app.main import main


@main.route("/")
def index():
    return redirect(url_for("admin.roster"))
