from app import create_app, db # Import db
from app.models import User # Import User model
import os
import click

app = create_app()

@app.cli.command("seed-admin")
def seed_admin():
    """Creates an initial admin user if one doesn't exist."""
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme') # IMPORTANT: Change this in production!

    if not admin_password or admin_password == 'changeme':
        print("WARNING: Default admin password is being used. Please set ADMIN_PASSWORD environment variable.")

    # Check if admin user already exists by username or email
    existing_admin = User.query.filter(
        (User.username == admin_username) | (User.email == admin_email)
    ).first()

    if existing_admin:
        print(f"Admin user '{admin_username}' or email '{admin_email}' already exists.")
        # Optionally, update existing admin's permissions/status if needed
        # For example, ensure they have admin permission and are enabled/approved:
        if existing_admin.permission != 'admin' or not existing_admin.enabled or not existing_admin.is_approved:
            print(f"Ensuring user '{existing_admin.username}' has admin privileges and is active.")
            existing_admin.permission = 'admin'
            existing_admin.enabled = True
            existing_admin.is_approved = True
            db.session.commit()
            print("Existing admin user updated.")
        return

    print(f"Creating admin user: {admin_username} ({admin_email})")
    admin_user = User(
        username=admin_username,
        email=admin_email,
        permission='admin',
        enabled=True,
        is_approved=True # Automatically approve the seeded admin
    )
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created successfully.")

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0') # Running on a different port than React dev server
