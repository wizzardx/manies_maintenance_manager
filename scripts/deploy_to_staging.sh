#!/bin/bash
set -euo pipefail

while true; do
    RETCODE=0
    ssh -o StrictHostKeyChecking=no root@mmm-staging.ar-ciel.org whoami || RETCODE=$?
    if [ $RETCODE -eq 0 ]; then
        # Looks like the login test succeeded; so we can proceed further.
        break;
    elif [ $RETCODE -eq 255 ]; then
        # This can occur when our known_hosts file does not match the server.
        # This in turn can happen when we've re-created the droplet. Nuke our
        # known_hosts entry as needed.
        ssh-keygen -f "/home/david/.ssh/known_hosts" -R "mmm-staging.ar-ciel.org"
    else
        # Unknown return code
        echo "Unknown return code $RETCODE from SSH!"
        exit 1
    fi
done;

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
