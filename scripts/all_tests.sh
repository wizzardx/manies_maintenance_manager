#!/bin/bash
set -e

echo "Type checks..."
docker compose -f local.yml exec django mypy --strict marnies_maintenance_manager

echo "Unit and functional tests, with coverage..."
docker compose -f local.yml exec django coverage run --rcfile=.coveragerc --branch -m pytest --showlocals

echo "Coverage report (console)..."
docker compose -f local.yml exec django coverage report --rcfile=.coveragerc

echo "Coverage report (html)..."
docker compose -f local.yml exec django coverage html --rcfile=.coveragerc

echo "Done with all_tests.sh"
