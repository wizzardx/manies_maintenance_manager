#!/bin/bash
set -euo pipefail

FQDN="mmm.ar-ciel.org"
DEPLOY_ENV="production"

WORKING_DIR="$(dirname ${0})"
source "${WORKING_DIR}/_sourced/deploy_to_env.sh"

deploy_to_env
