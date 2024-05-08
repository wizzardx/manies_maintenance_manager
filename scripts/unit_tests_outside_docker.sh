#!/bin/bash
set -euo pipefail

# Setup Python version to use for the unit tests
if [ ! -f .python-version ]; then
    pyenv local 3.12.3
fi

# Determine the path to the Python executable
PYTHON_EXEC=$(pyenv which python)

# Make a Python virtual environment if it does not already exist
if [ ! -d .venv ]; then
    $PYTHON_EXEC -m venv .venv
fi

# Activate the virtualenv
source .venv/bin/activate

# Get md5sum of requirements/local.txt, and use that to determine if we need to
# run pip install.
TXT_MD5=$(md5sum requirements/local.txt | awk '{print $1}')
ALREADY_INSTALLED_MARKER_FILE=".venv/.already_installed_${TXT_MD5}"

# Only run Pip to install software if this is a new venv (the marker file does not
# exist), or the user made changes to the "local.txt" file (the marker file md5sum
# marker is now out of date).
if [ !  -f $ALREADY_INSTALLED_MARKER_FILE ]; then
    python -m pip install -r requirements/local.txt
    touch $ALREADY_INSTALLED_MARKER_FILE
fi

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

# Run the unit tests:
pytest marnies_maintenance_manager/jobs --ff --maxfail=1 --showlocals
