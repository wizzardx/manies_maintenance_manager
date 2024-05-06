#!/bin/bash
set -e

echo "Type checks..."
docker compose -f local.yml exec django mypy manies_maintenance_manager

echo "Unit and functional tests, with coverage..."
docker compose -f local.yml exec django coverage run -m pytest --showlocals

echo "Coverage report..."
docker compose -f local.yml exec django coverage report

echo "Done with all_tests.sh"
