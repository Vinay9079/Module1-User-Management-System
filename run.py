import click
from flask.cli import with_appcontext
from argon2 import PasswordHasher
from app import create_app
from app.models import db, User, Role

app = create_app()


@app.cli.command("create-admin")
@click.option("--name", prompt=True)
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.password_option()
@with_appcontext
def create_admin(name, username, email, password):
    """Create the first Administrator account."""
    if len(password) < 10:
        raise click.ClickException("Password must contain at least 10 characters.")

    existing = User.query.filter(
        db.or_(db.func.lower(User.email) == email.lower(),
               db.func.lower(User.username) == username.lower())
    ).first()
    if existing:
        raise click.ClickException("That username or email is already registered.")

    admin_role = Role.query.filter_by(role_name="Administrator").first()
    user = User(
        name=name.strip(),
        username=username.strip().lower(),
        email=email.strip().lower(),
        password_hash=PasswordHasher().hash(password),
    )
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    click.echo("Administrator account created successfully.")


if __name__ == "__main__":
    app.run(debug=True)
