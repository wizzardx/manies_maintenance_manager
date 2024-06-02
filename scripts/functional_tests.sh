#!/bin/bash
set -euo pipefail

# Clear out the pycached "lastfailed" marker if it refers to something besides the
# functional tests:
scripts/clear_none_functional_tests_pytest_lastfailed_marker.py

# Reminder: Google Chrome can be seen in a local VNC client like Remmina, on
# port 5900, with password 'secret'.
docker compose -f docker-compose.local.yml exec django pytest \
    marnies_maintenance_manager/functional_tests --ff --maxfail=1 --showlocals
