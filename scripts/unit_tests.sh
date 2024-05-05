#!/bin/bash
set -e
docker compose -f local.yml run --rm \
    django pytest manies_maintenance_manager/jobs --ff --maxfail=1 --showlocals
