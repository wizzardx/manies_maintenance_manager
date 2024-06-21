#!/bin/bash

# Strict error handling
set -euo pipefail
IFS=$'\n\t'

# Define the red color escape code
RED='\033[0;31m'

# Define the no color escape code
NC='\033[0m' # No Color

# Initialize the global variables
NUM_ERRORS=0
STOP_ON_FIRST_ERROR="no"

# Check for --stop-on-first-error or -s argument
for arg in "$@";
do
    if [ "$arg" == "--stop-on-first-error" ] || [ "$arg" == "-s" ]; then
        STOP_ON_FIRST_ERROR="yes"
    else
        echo "Unknown argument: $arg"
        exit 1
    fi
done


# Function to echo text in red to stderr and increment NUM_ERRORS
echo_error() {
    echo -e "${RED}$1${NC}" >&2
    NUM_ERRORS=$((NUM_ERRORS + 1))
}


# The .ipython directory gets populated by the root process under Docker, and can cause
# permissions-related issues for none-root scripts/etc running outside of docker.
if [ -d .ipython ]; then
    echo "Tidying up annoying .ipython directory..."
    if ! rm -rf .ipython; then
        echo "Errors removing .ipython directory. I'm going to do it as root user instead!"
        sudo rm -rf .ipython
    fi
fi

# Initialize the global variable NUM_ERRORS
NUM_ERRORS=0

# This function is called by the script when one of the important commands runs a none-zero return code.
function handle_error() {
    echo_error "There was an error!"
    NUM_ERRORS=$((NUM_ERRORS + 1))
    if [ "$STOP_ON_FIRST_ERROR" == "yes" ]; then
        exit 1
    fi
}

# Run unit tests first, to get useful things setup under .venv.
echo "Fast unit tests (using sqlite mem, outside of docker)..."
scripts/unit_tests_outside_docker.sh || handle_error

# Do the helper script checks over here, because it wants to check the .venv file
# logic (but the .venv might not exist if the previous line has not yet run)
echo "Check helper scripts..."
shellcheck -x scripts/*.sh

# Activate the .venv just setup, to get the correct versions of various testing utils
# available.
VENV_DIR=$(scripts/print_venv_dir.sh)

# shellcheck disable=SC1091
. "$VENV_DIR"/bin/activate

echo "Checking if makemigrations needs to be run..."
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no
RESULT=0
OUTPUT=$(python manage.py makemigrations --dry-run 2>&1) || RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo "'python manage.py makemigrations --dry-run' terminated with exit code $RESULT, and output:"
    echo "$OUTPUT"
    handle_error
else
    if echo "$OUTPUT" | grep -q "No changes detected"; then
        echo "No migrations pending."
    else
        echo "Migrations pending:"
        echo "$OUTPUT"
        echo "Please create the database migrations by running 'scripts/makemigrations.sh'"
        handle_error
    fi
fi

# Run 'black' against the code, it makes some things a bit faster in the pre-commit,
# instead of it taking a long time to run reformats, and then terminate with an
# error message because it reformatted something.
echo "Running Black to reformat code..."
black --line-length 88 . || handle_error

echo "Type checks..."

# Setup needed environment variables
export DATABASE_URL=sqlite://:memory:  # Faster than PostgreSQL
export USE_DOCKER=no

mypy --strict . || handle_error

# Reset variable that we no longer need
unset DATABASE_URL
unset USE_DOCKER

echo "Pylint..."

# Find all Python files in the current directory and subdirectories, excluding hidden directories and migration files
mapfile -t files < <(find . -type f -name "*.py" ! -path "*/.*/*" ! -path "*/migrations/*")

# Run pylint with the dynamically found files
pylint --django-settings-module=config.settings --output-format=colorized --enable-all-extensions "${files[@]}" || handle_error

echo "Updating pre-commit references..."
pre-commit autoupdate || handle_error

echo "Running pre-commit checks 1/2... (only staged files)"
pre-commit run || handle_error

echo "Running pre-commit checks 2/2... (all files)"
pre-commit run --all-files || handle_error

echo "darglint2..."
darglint2 "${files[@]}" || handle_error

# Check for security issues:
echo "Check for security issues..."
# The ignored numbers here are known, and don't apply, and also I'm (currently) already
# using the latest available versions of the affected PyPI packages.
safety check --ignore 51457,70612 || handle_error

# Check for out of date packages:
echo "Check for outdated packages..."
scripts/check_outdated_packages.py --ignore Django,regex,pydantic_core || handle_error

# Done with tools from under the python venv, so deactivate that now.
echo "Deactivate python virtualenv."
deactivate

echo "Running Django's system checks..."
docker compose -f docker-compose.local.yml exec django python manage.py check || handle_error

echo "Unit and functional tests (under docker), with coverage..."
docker compose -f docker-compose.local.yml exec django coverage run --rcfile=.coveragerc -m pytest || handle_error

echo "Coverage report (console)..."
# Run both coverage reports, even if one of them fails, before returning with an exit.
# This is so that we can have both type of output report (terminal, and HTML).
COVERAGE_ERROR=0
docker compose -f docker-compose.local.yml exec django coverage report --rcfile=.coveragerc || COVERAGE_ERROR=1

echo "Coverage report (html)..."
docker compose -f docker-compose.local.yml exec django coverage html --rcfile=.coveragerc || COVERAGE_ERROR=1

# Stop now if there was an error (eg, not enough coverage %) returned by one of the
# coverage report runs
if [ "$COVERAGE_ERROR" != "0" ]; then
    handle_error
fi

# Different output at the end depending on if there were errors or not in the logic above.
if [ $NUM_ERRORS -eq 0 ]; then
    # No errors
    echo "Done with all_tests.sh - SUCCESS"

    # And in the case of success, also make some further suggestions:
    echo
    echo "Now that all of my checks look good, you should also manually run these checks in PyCharm:

    1. \`Code\` > \`Analyse Code\` > \`Locate Duplicates\`
    2. \`Code\` > \`Inspect Code\`
"

    echo "After you have done that, and everything looks good, then consider making a git commit."
    echo
else
    # There were errors.
    echo "Done with all_tests.sh - FAILURE. Check the logs above for details."
    exit 1
fi
