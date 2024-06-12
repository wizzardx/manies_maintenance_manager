#!/bin/bash
set -e

# Clear out the pycached "lastfailed" marker if it refers to something besides the
# unit test tests:
scripts/clear_functional_tests_pytest_lastfailed_marker.py

docker compose -f docker-compose.local.yml run --rm \
    django pytest \
    marnies_maintenance_manager/jobs \
    marnies_maintenance_manager/users \
    --maxfail=1 \
    --doctest-modules
