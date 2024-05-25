#!/bin/bash
set -e

# Random general tidy-up - clean up docker-related resources that were created over
# a week ago, hopefully this corresponds roughly to ones that haven't been used
# for a week. Otherwise, they can usually be rebuilt fairly quickly as needed.

echo "Pruning docker-related resources (other than volumes) that were created over a week ago"

# Prune stopped containers created over a week ago
echo "- Containers..."
docker container prune --force --filter "until=168h"

# Prune dangling images (not associated with any container)
echo "- Dangling Images..."
docker image prune --force

# Prune unused networks created over a week ago
echo "- Networks..."
docker network prune --force --filter "until=168h"

# Bring down our containers first before bringing them up. Just in case of weird quirks
# like eg, some containers unable to shut down for some reason, that I need to check
# more closely in my dev environment.
echo "Docker compose going down..."
docker compose -f docker-compose.local.yml down

echo "Docker compose going up, and rebuilding as needed..."
docker compose -f docker-compose.local.yml up --build
