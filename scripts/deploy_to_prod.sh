#!/bin/bash
set -euo pipefail

FQDN="mmm.ar-ciel.org"
DEPLOY_ENV="production"

source scripts/_sourced/deploy_to_env.sh

deploy_to_env
