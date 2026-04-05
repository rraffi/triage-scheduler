from app.main import main


@main.route("/")
def index():
    return "Triage Scheduler", 200
