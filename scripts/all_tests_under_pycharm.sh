#!/bin/bash
set -e

# Extra logic for scripts/all_scripts.sh, when we run the script under PyCharm's
# terminal

# Run the script itself
time scripts/all_tests.sh || true

# That script can take a while, so play a noise and run kdialog to bring my attention
# back to it.
paplay /usr/share/sounds/sound-icons/message
kdialog --msgbox "Tests done" || true
