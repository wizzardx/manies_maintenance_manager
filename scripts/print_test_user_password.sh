#!/bin/bash
set -euo pipefail
grep TEST_USER_PASSWORD .envs/.local/.testing | awk -F = '{print $2}'
