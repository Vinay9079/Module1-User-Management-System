from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from argon2 import PasswordHasher
from .models import db, User, Role
from .audit import record_event

main_bp = Blueprint("main", __name__)
password_hasher = PasswordHasher()


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if not current_user.has_role("Administrator"):
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role_id = request.form.get("role_id", type=int)
        role = db.session.get(Role, role_id) if role_id else None

        duplicate = User.query.filter(
            db.or_(db.func.lower(User.email) == email,
                   db.func.lower(User.username) == username)
        ).first()

        if not all([name, username, email, password, role]) or len(password) < 10:
            flash("Complete all fields. Password must be at least 10 characters.", "error")
        elif duplicate:
            flash("Username or email is already in use.", "error")
        else:
            user = User(name=name, username=username, email=email,
                        password_hash=password_hasher.hash(password))
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            record_event("user_created", "success", "User", user.id,
                         f"Account created with role {role.role_name}")
            flash("User account created.", "success")
            return redirect(url_for("main.users"))

    all_users = User.query.order_by(User.id.desc()).all()
    roles = Role.query.order_by(Role.role_name).all()
    return render_template("users.html", users=all_users, roles=roles)


@main_bp.route("/users/<int:user_id>/status", methods=["POST"])
@login_required
def change_user_status(user_id):
    if not current_user.has_role("Administrator"):
        abort(403)

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "error")
    else:
        user.status = "inactive" if user.status == "active" else "active"
        db.session.commit()
        record_event("account_status_changed", "success", "User", user.id,
                     f"Account status changed to {user.status}")
        flash("Account status updated.", "success")
    return redirect(url_for("main.users"))


@main_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
def change_user_role(user_id):
    if not current_user.has_role("Administrator"):
        abort(403)

    user = User.query.get_or_404(user_id)
    role = db.session.get(Role, request.form.get("role_id", type=int))
    if not role:
        flash("Select a valid role.", "error")
    elif user.id == current_user.id:
        flash("You cannot change your own role here.", "error")
    else:
        user.roles = [role]
        db.session.commit()
        record_event("role_changed", "success", "User", user.id,
                     f"Role changed to {role.role_name}")
        flash("User role updated.", "success")
    return redirect(url_for("main.users"))
