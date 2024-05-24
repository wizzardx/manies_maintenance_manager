#!/bin/bash
set -e

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

# Activate python virtual environment
source .venv/bin/activate

# Make the db migrations.
python manage.py makemigrations
