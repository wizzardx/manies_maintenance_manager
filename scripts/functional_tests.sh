#!/bin/bash
set -euo pipefail

# Similar to "all_tests.sh", the logic for scripts/functional_tests.sh can sometimes
# take a while to run. We have some extra notification logic here so that I can do
# something else while waiting for this to run.

# Check for --stop-on-first-error or -s argument
STOP_ON_FIRST_ERROR="no"
for arg in "$@";
do
    if [ "$arg" == "--stop-on-first-error" ] || [ "$arg" == "-s" ]; then
        STOP_ON_FIRST_ERROR="yes"
    else
        echo "Unknown argument: $arg"
        exit 1
    fi
done

# Clear out the pycached "lastfailed" marker if it refers to something besides the
# functional tests:
scripts/clear_none_functional_tests_pytest_lastfailed_marker.py

# Capture the window ID of the terminal where the script is running
TERMINAL_WIN_ID=$(xdotool getactivewindow)

# Run the functional tests
RETCODE=0

# Reminder: Google Chrome can be seen in a local VNC client like Remmina, on
# port 5900, with password 'secret'.
CMD=(
    docker compose -f docker-compose.local.yml exec django pytest \
        marnies_maintenance_manager/functional_tests --doctest-modules
)

# If STOP_ON_FIRST_ERROR is set, then fail after the firset error.
if [ "$STOP_ON_FIRST_ERROR" == "yes" ]; then
    CMD+=("--maxfail=1")
fi

# Run the command with timing, and capturing any error return code:
time "${CMD[@]}" || RETCODE=$?

# That script can take a while, so play a noise and run `yad` to bring my attention
# back to it.
paplay /usr/share/sounds/sound-icons/message

show_message() {
    local message="$1"
    echo "$message"
    yad --text="$message" --button=yad-ok --on-top --width=300 --height=100 --center
}

if [ "$RETCODE" == "0" ]; then
    show_message "Functional Tests done - SUCCESS"
    echo "Done with functional_tests.sh - SUCCESS"
else
    show_message "Functional Tests done - FAILURE"
    echo "Done with functional_tests.sh - FAILURE"
fi

# Bring the focus back to the terminal
echo "Bringing focus back to the original terminal."
xdotool windowactivate "$TERMINAL_WIN_ID"

echo "Exiting with code $RETCODE "
exit $RETCODE
