#!/bin/bash
set -e

PWD_MD5=$(pwd | md5sum | awk '{print $1}')
VENV_DIR="/tmp/.manies_maintenance_manager_project.$PWD_MD5.venv"

echo "$VENV_DIR"
