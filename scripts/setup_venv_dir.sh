#!/bin/bash
set -euo pipefail

# Function to log messages
log() {
    echo "[INFO] $1"
}

# Determine the path to the Python executable
log "Determining Python executable path..."
PYTHON_EXEC=$(pyenv which python)

# Make a Python virtual environment if it does not already exist
log "Creating virtual environment if it doesn't exist..."
VENV_DIR=$(scripts/print_venv_dir.sh)
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_EXEC -m venv "$VENV_DIR"
fi

# Activate the virtualenv
log "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Get md5sum of requirements/local.txt, and use that to determine if we need to
# run pip install.
log "Checking for changes in requirements files..."
LOCAL_TXT_MD5=$(md5sum requirements/local.txt | awk '{print $1}')
LOCAL_ALREADY_INSTALLED_MARKER_FILE="$VENV_DIR/.local_already_installed_${LOCAL_TXT_MD5}"

# Do the same for the requirements/base.txt file:
BASE_TXT_MD5=$(md5sum requirements/base.txt | awk '{print $1}')
BASE_ALREADY_INSTALLED_MARKER_FILE="$VENV_DIR/.base_already_installed_${BASE_TXT_MD5}"

# Only run Pip to install software if this is a new venv (the marker file does not
# exist), or the user made changes to the "local.txt" or "base.txt" file (the marker
# file md5sum markers are now out of date).
if [[ ! -f "$LOCAL_ALREADY_INSTALLED_MARKER_FILE" || ! -f "$BASE_ALREADY_INSTALLED_MARKER_FILE" ]]; then
    log "Installing dependencies..."
    python -m pip install -r requirements/local.txt
    touch "$LOCAL_ALREADY_INSTALLED_MARKER_FILE"
    touch "$BASE_ALREADY_INSTALLED_MARKER_FILE"
fi
