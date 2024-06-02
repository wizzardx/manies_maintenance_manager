#!/bin/bash
set -e

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

# Activate python virtual environment
VENV_DIR=$(scripts/print_venv_dir.sh)
echo "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR"/bin/activate

# Make the db migrations.
python manage.py makemigrations
