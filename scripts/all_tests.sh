#!/bin/bash
set -e

echo "Check helper scripts..."
shellcheck scripts/*.sh

echo "Type checks..."
docker compose -f local.yml exec django mypy --strict marnies_maintenance_manager

echo "Running pre-commit checks..."
pre-commit run --all-files

echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests_outside_docker.sh

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
