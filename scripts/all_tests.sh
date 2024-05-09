#!/bin/bash
set -e

echo "Check helper scripts..."
shellcheck scripts/*.sh

echo "Type checks..."
docker compose -f local.yml exec django mypy --strict marnies_maintenance_manager

echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests_outside_docker.sh

echo "Unit and functional tests (under docker), with coverage..."
docker compose -f local.yml exec django coverage run --rcfile=.coveragerc -m pytest --showlocals

echo "Running pre-commit checks..."
pre-commit run --all-files

echo "Coverage report (console)..."
docker compose -f local.yml exec django coverage report --rcfile=.coveragerc

echo "Coverage report (html)..."
docker compose -f local.yml exec django coverage html --rcfile=.coveragerc

echo "Done with all_tests.sh"
