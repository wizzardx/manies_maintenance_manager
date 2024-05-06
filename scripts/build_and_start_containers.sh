#!/bin/bash
set -e

# Remove a directory that can cause some problems with building the image:
if [ -e .ipython/profile_default ]; then
    sudo rm -rvf .ipython/profile_default
fi

docker compose -f local.yml up --build
