#!/bin/bash
set -e
./scripts/stop_containers.sh
docker system prune -a && docker volume prune -a
