from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc)


user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    roles = db.relationship("Role", secondary=user_roles, back_populates="users")
    team_links = db.relationship("TeamMember", back_populates="user",
                                 cascade="all, delete-orphan")

    def has_role(self, role_name):
        return any(role.role_name == role_name for role in self.roles)

    @property
    def role_names(self):
        return [role.role_name for role in self.roles]


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", secondary=user_roles, back_populates="roles")


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    members = db.relationship("TeamMember", back_populates="team",
                              cascade="all, delete-orphan")


class TeamMember(db.Model):
    __tablename__ = "team_members"

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    assigned_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    team = db.relationship("Team", back_populates="members")
    user = db.relationship("User", back_populates="team_links")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    status = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=utc_now)
    details = db.Column(db.Text)
