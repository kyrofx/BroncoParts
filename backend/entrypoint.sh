#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

# Run database migrations
# It's good practice to ensure the Flask app context is available for db commands
# and that FLASK_APP is correctly set (which it is, via Dockerfile ENV).
echo "Running database migrations..."
flask db upgrade
echo "Database migrations complete."

# Seed initial admin user
echo "Seeding admin user..."
flask seed-admin
echo "Admin user seeding process complete."

# Then exec the container's main process (what's set as CMD in the Dockerfile).
exec "$@"
