#!/bin/bash
set -euo pipefail

# Function to log messages
log() {
    echo "[INFO] $1"
}

# # Setup Python version to use for the unit tests
# log "Setting up Python version..."
# pyenv local 3.12.4

# Setup the virtualenv dir.
log "Setup venv dir...."
scripts/setup_venv_dir.sh

# Activate the virtualenv
log "Activating virtual environment..."
VENV_DIR=$(scripts/print_venv_dir.sh)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Setup needed environment variables
log "Setting up environment variables..."
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

TEST_USER_PASSWORD=$(scripts/print_test_user_password.sh)
export TEST_USER_PASSWORD

# Start pycharm.
log "Running PyCham...."
RETCODE=0
pycharm "$@" || RETCODE=$?

log "PyCharm terminated with return code $RETCODE"
