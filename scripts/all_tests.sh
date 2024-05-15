#!/bin/bash
set -e

# # Reset permissions/ownerships on files, our docker logic can set it to be root-owned.
# echo "Resetting ownerships..."
# sudo chown david:david . -R

# Run unit tests first, to get useful things setup under .venv.
echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests_outside_docker.sh

# Do the helper script checks over here, because it wants to check the .venv file
# logic (but the .venv might not exist if the previous line has not yet run)
echo "Check helper scripts..."
shellcheck -x scripts/*.sh

# Activate the .venv just setup, to get the correct versions of various testing utils
# available.
. .venv/bin/activate

# Run 'black' agains the code, it makes some things a bit faster in the precommit,
# instead of it taking a long time to run reformats, and then terminate with an
# error message because it reformatted something.
echo "Running Black to reformat code..."
black --line-length 88 marnies_maintenance_manager

echo "Type checks..."

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

mypy --strict marnies_maintenance_manager

# Reset variable that we no longer need
unset DATABASE_URL
unset USE_DOCKER

echo "Pylint..."
pylint \
    --django-settings-module=config.settings \
    --output-format=colorized marnies_maintenance_manager/

echo "Running pre-commit checks..."
pre-commit run --all-files

# Check for security issues:
echo "Check for security issues..."
# The ignored numbers here are known, and don't apply, and also I'm (currently) already
# using the latest available versions of the affected PyPI packages.
safety check --ignore 51457,67599

# Check for out of date packages:
echo "Check for outdated packages..."
scripts/check_outdated_packages.py --ignore Django,django-allauth,django-stubs,mypy,regex,Werkzeug

# Done with tools from under the python venv, so deactivate that now.
echo "Deactivate python virtualenv."
deactivate

echo "Running Django's system checks..."
docker compose -f local.yml exec django python manage.py check

echo "Unit and functional tests (under docker), with coverage..."
docker compose -f local.yml exec django coverage run --rcfile=.coveragerc -m pytest --showlocals

echo "Coverage report (console)..."
# Run both coverage reports, even if one of them fails, before returning with an exit.
# This is so that we can have both type of output report (terminal, and HTML).
COVERAGE_ERROR=0
docker compose -f local.yml exec django coverage report --rcfile=.coveragerc || COVERAGE_ERROR=1

echo "Coverage report (html)..."
docker compose -f local.yml exec django coverage html --rcfile=.coveragerc || COVERAGE_ERROR=1

# Stop now if there was an error (eg, not enough coverage %) returned by one of the
# coverage report runs
if [ "$COVERAGE_ERROR" != "0" ]; then
    echo "Error running coverage"
    exit 1
fi

echo "Done with all_tests.sh"
