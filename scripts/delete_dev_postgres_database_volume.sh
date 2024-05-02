#!/bin/bash
set -e
./scripts/stop_containers.sh
docker volume rm manies_maintenance_manager_project_manies_maintenance_manager_local_postgres_data || true
docker volume rm manies_maintenance_manager_project_manies_maintenance_manager_local_postgres_data_backups || true

echo "Dev postgres volumes deleted."
