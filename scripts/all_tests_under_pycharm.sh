#!/bin/bash
set -e

# Extra logic for scripts/all_scripts.sh, when we run the script under PyCharm's
# terminal

# Run the script itself
RETCODE=0

time scripts/all_tests.sh || RETCODE=1

# That script can take a while, so play a noise and run kdialog to bring my attention
# back to it.
paplay /usr/share/sounds/sound-icons/message

if [ "$RETCODE" == 0 ]; then
    kdialog --msgbox "Tests done - SUCCESS"
else
    kdialog --msgbox "Tests done - FAILURE"
fi
