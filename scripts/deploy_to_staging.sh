#!/bin/bash
set -euo pipefail

FQDN="mmm-staging2.ar-ciel.org"
DEPLOY_ENV="staging"

source "scripts/_sourced/deploy_to_env.sh"

deploy_to_env
