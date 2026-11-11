
import os
from datetime import timedelta

from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

from .models import db, User, Role
from .extensions import csrf, limiter

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():

    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is missing. Add it to the .env file."
        )

    app.config.update(
        SECRET_KEY=secret_key,

        SQLALCHEMY_DATABASE_URI=(
            "sqlite:///" + os.path.join(
                app.instance_path, "module1.db"
            )
        ),

        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,

        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),

        WTF_CSRF_TIME_LIMIT=3600
    )

    db.init_app(app)
    login_manager.init_app(app)

    csrf.init_app(app)
    limiter.init_app(app)

    from .auth import auth_bp
    from .routes import main_bp
    from .teams import teams_bp
    from .audit import audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(audit_bp)

    with app.app_context():

        db.create_all()

        default_roles = [
            (
                "Administrator",
                "Manage users, roles, teams and audit logs."
            ),
            (
                "Security Analyst",
                "Review assigned security activity and alerts."
            ),
            (
                "Team Lead / Supervisor",
                "Oversee assigned analysts and teams."
            )
        ]

        for role_name, description in default_roles:

            role = Role.query.filter_by(
                role_name=role_name
            ).first()

            if not role:
                db.session.add(
                    Role(
                        role_name=role_name,
                        description=description
                    )
                )

        db.session.commit()

    return app
