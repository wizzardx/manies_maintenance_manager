#!/bin/bash
set -e

# Remove a directory that can cause some problems with building the image:
if [ -e .ipython/profile_default ]; then
    sudo rm -rvf .ipython/profile_default
fi

# Bring down our containers first before bringing them up. Just in case of weird quirks
# like eg, some containers unable to shut down for some reason, that I need to check
# more closely in my dev environment.
docker compose -f local.yml down
docker compose -f local.yml up --build
