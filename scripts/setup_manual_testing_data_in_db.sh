#!/bin/bash
set -e
docker compose -f docker-compose.local.yml exec django python manage.py setup_manual_dev_testing_data
