#!/bin/bash
set -e

# Bring down our containers first before bringing them up. Just in case of weird quirks
# like eg, some containers unable to shut down for some reason, that I need to check
# more closely in my dev environment.
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up --build
