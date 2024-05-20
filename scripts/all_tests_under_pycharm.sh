#!/bin/bash
set -e

# Extra logic for scripts/all_scripts.sh, when we run the script under PyCharm's
# terminal

# Capture the window ID of the terminal where the script is running
TERMINAL_WIN_ID=$(xdotool getactivewindow)

# Run the script itself
RETCODE=0

time scripts/all_tests.sh || RETCODE=$?

# That script can take a while, so play a noise and run kdialog to bring my attention
# back to it.
paplay /usr/share/sounds/sound-icons/message

if [ "$RETCODE" == "0" ]; then
    echo "Tests done - SUCCESS"
    kdialog --msgbox "Tests done - SUCCESS"
    echo "Done with all_tests_under_pycharm.sh - SUCCESS"
else
    echo "Tests done - FAILURE"
    kdialog --msgbox "Tests done - FAILURE"
    echo "Done with all_tests_under_pycharm.sh - FAILURE"
fi

# Bring the focus back to the terminal
echo "Bringing focus back to the original terminal.".
xdotool windowactivate "$TERMINAL_WIN_ID"

echo "Exiting with code $RETCODE "
exit $RETCODE
