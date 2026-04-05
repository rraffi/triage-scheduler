from flask import Flask

from app.extensions import db, migrate
from config import config


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Alembic can detect them
    from app import db_models  # noqa: F401

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.commands import seed_db, schedule_week, schedule_preview
    app.cli.add_command(seed_db)
    app.cli.add_command(schedule_week)
    app.cli.add_command(schedule_preview)

    return app
