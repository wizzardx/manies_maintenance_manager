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
# shellcheck disable=SC1091
source .venv/bin/activate

# Clear out the pycached "lastfailed" marker if it refers to something besides the
# unit test tests:
scripts/clear_functional_tests_pytest_lastfailed_marker.py

# Get md5sum of requirements/local.txt, and use that to determine if we need to
# run pip install.
LOCAL_TXT_MD5=$(md5sum requirements/local.txt | awk '{print $1}')
LOCAL_ALREADY_INSTALLED_MARKER_FILE=".venv/.local_already_installed_${LOCAL_TXT_MD5}"

# Do the same for the requirements/base.txt file:
BASE_TXT_MD5=$(md5sum requirements/base.txt | awk '{print $1}')
BASE_ALREADY_INSTALLED_MARKER_FILE=".venv/.base_already_installed_${BASE_TXT_MD5}"

# Only run Pip to install software if this is a new venv (the marker file does not
# exist), or the user made changes to the "local.txt" or "base.txt" file (the marker
# file md5sum markers are now out of date).
if [[ ! -f $LOCAL_ALREADY_INSTALLED_MARKER_FILE || ! -f $BASE_ALREADY_INSTALLED_MARKER_FILE ]]; then
    python -m pip install -r requirements/local.txt
    touch "$LOCAL_ALREADY_INSTALLED_MARKER_FILE"
    touch "$BASE_ALREADY_INSTALLED_MARKER_FILE"
fi

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

# Run the unit tests:
pytest \
    marnies_maintenance_manager/jobs \
    marnies_maintenance_manager/users \
    --ff --maxfail=1 --showlocals \
    -n auto \
    --reuse-db --nomigrations

# If we got this far, then there were no test erors. Now we can clear some data from
# the pytest cache so that we don't -repeatedly get warnings like this:
# "run-last-failure: 16 known failures not in selected tests"
if [ -f .pytest_cache/v/cache/lastfailed ]; then
    echo "Removing a pytest cache file to stop getting now-obsolete messages"
    rm -vf .pytest_cache/v/cache/lastfailed
fi
