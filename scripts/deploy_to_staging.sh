#!/bin/bash
set -euo pipefail

FQDN=mmm-staging.ar-ciel.org
ssh-keygen -f "/home/david/.ssh/known_hosts" -R "$FQDN"
ssh -o StrictHostKeyChecking=no root@$FQDN echo ""

# Setup the virtual env so that we have access to the correct versions of
# ansible, mitogen, etc:
scripts/setup_venv_dir.sh
VENV_DIR=$(scripts/print_venv_dir.sh)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Set custom path to ansible config:
# shellcheck disable=SC2155
export ANSIBLE_CONFIG=$(pwd)/infra/ansible.cfg

# Initial setup of the host:
time ansible-playbook -i infra/hosts.ini infra/initial-setup.yml -vv \
    --limit new_staging_droplet \
    --vault-pass-file infra/.secrets/vault_password_file.txt \
    --extra-vars "deploy_env=staging"

# Install the rest:
time ansible-playbook -i infra/hosts.ini infra/ansible-provision.yml -vv \
    --limit local,staging \
    --extra-vars "deploy_env=staging"
