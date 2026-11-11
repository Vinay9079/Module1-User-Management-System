
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from .models import db, Team, TeamMember, User
from .audit import record_event


teams_bp = Blueprint("teams", __name__, url_prefix="/teams")


def can_manage_team(team):
    # Administrator can manage every team.
    if current_user.has_role("Administrator"):
        return True

    # Team Lead can manage only assigned teams.
    if current_user.has_role("Team Lead / Supervisor"):
        return any(
            link.team_id == team.id
            for link in current_user.team_links
        )

    return False


@teams_bp.route("/", methods=["GET", "POST"])
@login_required
def list_teams():

    is_admin = current_user.has_role("Administrator")
    is_lead = current_user.has_role("Team Lead / Supervisor")

    # Administrator can view all teams.
    if is_admin:
        teams = Team.query.order_by(Team.team_name).all()

    # Team Lead can view assigned teams only.
    elif is_lead:
        team_ids = [
            link.team_id for link in current_user.team_links
        ]

        teams = Team.query.filter(
            Team.id.in_(team_ids)
        ).all() if team_ids else []

    # Other users can view their assigned teams.
    else:
        team_ids = [
            link.team_id for link in current_user.team_links
        ]

        teams = Team.query.filter(
            Team.id.in_(team_ids)
        ).all() if team_ids else []

    # Only Administrator can create a team.
    if request.method == "POST":

        if not is_admin:
            abort(403)

        name = request.form.get("team_name", "").strip()
        description = request.form.get("description", "").strip()

        existing_team = Team.query.filter(
            db.func.lower(Team.team_name) == name.lower()
        ).first()

        if not name:
            flash("Team name is required.", "error")

        elif existing_team:
            flash("A team with this name already exists.", "error")

        else:
            team = Team(
                team_name=name,
                description=description or None
            )

            db.session.add(team)
            db.session.commit()

            record_event(
                "team_created",
                "success",
                "Team",
                team.id,
                "Team created"
            )

            flash("Team created successfully.", "success")

            return redirect(url_for("teams.list_teams"))

    return render_template(
        "teams.html",
        teams=teams,
        is_admin=is_admin
    )


@teams_bp.route("/<int:team_id>/update", methods=["POST"])
@login_required
def update_team(team_id):

    team = Team.query.get_or_404(team_id)

    if not can_manage_team(team):
        abort(403)

    name = request.form.get("team_name", "").strip()
    description = request.form.get("description", "").strip()

    duplicate = Team.query.filter(
        db.func.lower(Team.team_name) == name.lower(),
        Team.id != team.id
    ).first()

    if not name or duplicate:
        flash(
            "Enter a valid team name that is not already in use.",
            "error"
        )

    else:
        team.team_name = name
        team.description = description or None

        db.session.commit()

        record_event(
            "team_updated",
            "success",
            "Team",
            team.id,
            "Team details updated"
        )

        flash("Team updated successfully.", "success")

    return redirect(url_for("teams.list_teams"))


@teams_bp.route("/<int:team_id>/delete", methods=["POST"])
@login_required
def delete_team(team_id):

    if not current_user.has_role("Administrator"):
        abort(403)

    team = Team.query.get_or_404(team_id)
    deleted_team_id = team.id

    db.session.delete(team)
    db.session.commit()

    record_event(
        "team_deleted",
        "success",
        "Team",
        deleted_team_id,
        "Team deleted"
    )

    flash("Team deleted successfully.", "success")

    return redirect(url_for("teams.list_teams"))


@teams_bp.route("/<int:team_id>/members", methods=["POST"])
@login_required
def add_member(team_id):

    team = Team.query.get_or_404(team_id)

    if not can_manage_team(team):
        abort(403)

    user_id = request.form.get("user_id", type=int)

    user = db.session.get(User, user_id) if user_id else None

    if not user:
        flash("User not found.", "error")

    elif user.status != "active":
        flash("Inactive users cannot be assigned.", "error")

    elif not (
        user.has_role("Security Analyst")
        or user.has_role("Team Lead / Supervisor")
    ):
        flash(
            "Only Security Analysts and Team Leads can be assigned.",
            "error"
        )

    elif TeamMember.query.filter_by(
        team_id=team.id,
        user_id=user.id
    ).first():

        flash("This user is already a member of this team.", "error")

    else:
        member = TeamMember(
            team_id=team.id,
            user_id=user.id
        )

        db.session.add(member)
        db.session.commit()

        record_event(
            "team_member_added",
            "success",
            "Team",
            team.id,
            f"User ID {user.id} added to team"
        )

        flash("Team member added successfully.", "success")

    return redirect(url_for("teams.list_teams"))


@teams_bp.route(
    "/<int:team_id>/members/<int:user_id>/remove",
    methods=["POST"]
)
@login_required
def remove_member(team_id, user_id):

    team = Team.query.get_or_404(team_id)

    if not can_manage_team(team):
        abort(403)

    member = TeamMember.query.filter_by(
        team_id=team.id,
        user_id=user_id
    ).first()

    if not member:
        flash("This user is not a member of the team.", "error")

    else:
        db.session.delete(member)
        db.session.commit()

        record_event(
            "team_member_removed",
            "success",
            "Team",
            team.id,
            f"User ID {user_id} removed from team"
        )

        flash("Team member removed successfully.", "success")

    return redirect(url_for("teams.list_teams"))
