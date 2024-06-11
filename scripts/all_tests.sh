#!/bin/bash

# Strict error handling
set -euo pipefail
IFS=$'\n\t'

# The .ipython directory gets populated by the root process under Docker, and can cause
# permissions-related issues for none-root scripts/etc running outside of docker.
if [ -d .ipython ]; then
    echo "Tidying up annoying .ipython directory..."
    if ! rm -rf .ipython; then
        echo "Errors removing .ipython directory. I'm going to do it as root user instead!"
        sudo rm -rf .ipython
    fi
fi

# Flag indicating whether we had errors so far in the script:
ERRORS=no

# Run unit tests first, to get useful things setup under .venv.
echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests_outside_docker.sh || ERRORS=yes

# Do the helper script checks over here, because it wants to check the .venv file
# logic (but the .venv might not exist if the previous line has not yet run)
echo "Check helper scripts..."
shellcheck -x scripts/*.sh

# Activate the .venv just setup, to get the correct versions of various testing utils
# available.
VENV_DIR=$(scripts/print_venv_dir.sh)

# shellcheck disable=SC1091
. "$VENV_DIR"/bin/activate

# Run 'black' against the code, it makes some things a bit faster in the pre-commit,
# instead of it taking a long time to run reformats, and then terminate with an
# error message because it reformatted something.
echo "Running Black to reformat code..."
black --line-length 88 . || ERRORS=yes

echo "Type checks..."

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

mypy --strict . || ERRORS=yes

# Reset variable that we no longer need
unset DATABASE_URL
unset USE_DOCKER

echo "Pylint..."

# Find all Python files in the current directory and subdirectories, excluding hidden directories and migration files
mapfile -t files < <(find . -type f -name "*.py" ! -path "*/.*/*" ! -path "*/migrations/*")

# Run pylint with the dynamically found files
pylint --django-settings-module=config.settings --output-format=colorized --enable-all-extensions "${files[@]}" || ERRORS=yes

echo "Running pre-commit checks..."
pre-commit run --all-files || ERRORS=yes

echo "darglint..."
darglint "${files[@]}" || ERRORS=yes

# Check for security issues:
echo "Check for security issues..."
# The ignored numbers here are known, and don't apply, and also I'm (currently) already
# using the latest available versions of the affected PyPI packages.
safety check --ignore 51457,70612 || ERRORS=yes

# Check for out of date packages:
echo "Check for outdated packages..."
scripts/check_outdated_packages.py --ignore Django,regex || ERRORS=yes

# Done with tools from under the python venv, so deactivate that now.
echo "Deactivate python virtualenv."
deactivate

echo "Running Django's system checks..."
docker compose -f docker-compose.local.yml exec django python manage.py check || ERRORS=yes

echo "Unit and functional tests (under docker), with coverage..."
docker compose -f docker-compose.local.yml exec django coverage run --rcfile=.coveragerc -m pytest --showlocals || ERRORS=yes

echo "Coverage report (console)..."
# Run both coverage reports, even if one of them fails, before returning with an exit.
# This is so that we can have both type of output report (terminal, and HTML).
COVERAGE_ERROR=0
docker compose -f docker-compose.local.yml exec django coverage report --rcfile=.coveragerc || COVERAGE_ERROR=1

echo "Coverage report (html)..."
docker compose -f docker-compose.local.yml exec django coverage html --rcfile=.coveragerc || COVERAGE_ERROR=1

# Stop now if there was an error (eg, not enough coverage %) returned by one of the
# coverage report runs
if [ "$COVERAGE_ERROR" != "0" ]; then
    echo "Error running coverage"
    ERRORS=yes
fi

# Were there errors in the above checks?
if [ "$ERRORS" == "no" ]; then
    echo "Done with all_tests.sh - SUCCESS"
else
    echo "Done with all_tests.sh - FAILURE. Check the logs above for details."
    exit 1
fi
