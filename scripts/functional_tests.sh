#!/bin/bash
set -e
# Reminder: Google Chrome can be seen in a local VNC client like Remmina, on
# port 5900, with password 'secret'.
docker compose -f local.yml exec django python manage.py test functional_tests
