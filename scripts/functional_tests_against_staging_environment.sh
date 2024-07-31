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

# A hacked version of functional_tests.sh, where we're running Selenium and
# Chrome outside of Docker, by using the "TEST_SERVER" argument, similar to
# in Obey The Testing Goat. Then we'll attempt to follow the Obey The Testing
# Goat worklow for also running our FTs in prod-like setups; use Ansible, etc.


# Activate the virtualenv
echo "Activating virtual environment..."
VENV_DIR=$(scripts/print_venv_dir.sh)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Preparing pytest command..."
export TEST_SERVER=mmm-staging2.ar-ciel.org:80

TEST_USER_PASSWORD=$(grep ^TEST_USER_PASSWORD ./.envs/.test/.testing | awk -F '=' '{print $2}')
export TEST_USER_PASSWORD

CMD=(
    pytest
        marnies_maintenance_manager/functional_tests
        --doctest-modules
        --reuse-db
        --no-migrations
        --save_screenshots
)

# If STOP_ON_FIRST_ERROR is set, then fail after the firset error.
if [ "$STOP_ON_FIRST_ERROR" == "yes" ]; then
    CMD+=("--maxfail=1")
fi

DATABASE_URL=$(grep ^REMOTE_DATABASE_URL ./.envs/.staging/.postgres | awk -F '=' '{print $2}')
export DATABASE_URL

export DATABASE_IS_EXISTING_EXTERNAL=True
export DEPRECATION_WARNINGS_EXPECTED=False
export TEST_USERS_SHOULD_ALREADY_EXIST=True
export USE_BROWSER_IN_DOCKER=False

time "${CMD[@]}" || RETCODE=$?

# That script can take a while, so play a noise and run `yad` to bring my attention
# back to it.
pw-play /usr/share/sounds/sound-icons/message

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
