#!/bin/bash
set -e
# Reminder: Google Chrome can be seen in a local VNC client like Remmina, on
# port 5900, with password 'secret'.
docker compose -f docker-compose.local.yml exec django pytest \
    marnies_maintenance_manager/functional_tests --ff --maxfail=1 --showlocals
