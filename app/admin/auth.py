from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for

from app.admin import admin


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


@admin.route("/login", methods=["GET", "POST"])
def login():
    from flask import render_template
    error = None
    if request.method == "POST":
        if request.form.get("password") == current_app.config["ADMIN_PASSWORD"]:
            session["is_admin"] = True
            next_url = request.args.get("next") or url_for("admin.roster")
            return redirect(next_url)
        error = "Invalid password."
    return render_template("admin/login.html", error=error)


@admin.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))
