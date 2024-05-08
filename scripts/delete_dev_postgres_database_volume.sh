#!/bin/bash
set -e
./scripts/stop_containers.sh
docker volume rm marnies_maintenance_manager_project_marnies_maintenance_manager_local_postgres_data || true
docker volume rm marnies_maintenance_manager_project_marnies_maintenance_manager_local_postgres_data_backups || true

echo "Dev postgres volumes deleted."
