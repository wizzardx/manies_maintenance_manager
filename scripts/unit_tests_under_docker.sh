#!/bin/bash
set -e
docker compose -f docker-compose.local.yml run --rm \
    django pytest marnies_maintenance_manager/jobs --ff --maxfail=1 --showlocals
