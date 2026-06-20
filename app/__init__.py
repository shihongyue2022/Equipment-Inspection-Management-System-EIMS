from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.config import Config
from app.extensions import csrf, db, migrate


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if str(app.config["SQLALCHEMY_DATABASE_URI"]).startswith("sqlite"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.accounts import bp as accounts_bp
    from app.auth import bp as auth_bp
    from app.dashboard import bp as dashboard_bp
    from app.equipment import bp as equipment_bp
    from app.inspections import bp as inspections_bp
    from app.maintenance import bp as maintenance_bp
    from app import models  # noqa: F401 - registers migration metadata

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(inspections_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(accounts_bp)

    @app.get("/")
    def index():
        return redirect(url_for("auth.login_get"))

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error", exc_info=error)
        return render_template("errors/500.html"), 500

    return app
