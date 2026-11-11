
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from .models import db, User
from .audit import record_event
from .extensions import limiter


auth_bp = Blueprint("auth", __name__)

password_hasher = PasswordHasher()


@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":

        identity = request.form.get(
            "identity", ""
        ).strip().lower()

        password = request.form.get("password", "")

        user = User.query.filter(
            db.or_(
                db.func.lower(User.email) == identity,
                db.func.lower(User.username) == identity
            )
        ).first()

        valid = False

        if user and user.status == "active":

            try:
                valid = password_hasher.verify(
                    user.password_hash,
                    password
                )

            except (VerifyMismatchError, VerificationError):
                valid = False

        if valid:

            login_user(user)

            record_event(
                "login",
                "success",
                "User",
                user.id,
                "User signed in"
            )

            flash("Login successful.", "success")

            return redirect(url_for("main.dashboard"))

        record_event(
            "login",
            "failed",
            "User",
            user.id if user else None,
            "Unsuccessful login attempt",
            actor_id=None
        )

        flash(
            "Login failed. Check your details or contact an administrator.",
            "error"
        )

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():

    user_id = current_user.id

    record_event(
        "logout",
        "success",
        "User",
        user_id,
        "User signed out"
    )

    logout_user()

    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        existing = User.query.filter(
            db.func.lower(User.email) == email,
            User.id != current_user.id
        ).first()

        if not name or not email or existing:

            flash(
                "Enter a valid name and a unique email address.",
                "error"
            )

        else:

            current_user.name = name
            current_user.email = email

            db.session.commit()

            record_event(
                "profile_updated",
                "success",
                "User",
                current_user.id,
                "Name or email updated"
            )

            flash("Profile updated.", "success")

            return redirect(url_for("auth.profile"))

    return render_template("profile.html")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        old_password = request.form.get(
            "old_password", ""
        )

        new_password = request.form.get(
            "new_password", ""
        )

        try:

            password_ok = password_hasher.verify(
                current_user.password_hash,
                old_password
            )

        except (VerifyMismatchError, VerificationError):

            password_ok = False

        if not password_ok:

            flash(
                "Current password is incorrect.",
                "error"
            )

        elif len(new_password) < 10:

            flash(
                "New password must contain at least 10 characters.",
                "error"
            )

        else:

            current_user.password_hash = password_hasher.hash(
                new_password
            )

            db.session.commit()

            record_event(
                "password_changed",
                "success",
                "User",
                current_user.id,
                "Password changed"
            )

            flash(
                "Password changed successfully.",
                "success"
            )

            return redirect(url_for("main.dashboard"))

    return render_template("change_password.html")
